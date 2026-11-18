"""Moteur minimal d'orchestration séquentielle des workflows locaux."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from typing import Any

from nodes.call_model import call_model


class SharedContext:
    """Données, état d'exécution et erreurs partagés entre les nœuds."""

    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
        *,
        state: Mapping[str, Any] | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.data = dict(data or {})
        self.state = dict(state or {})
        self.errors = list(errors or [])

    def get(self, key: str, default: Any = None) -> Any:
        """Retourne une donnée du contexte, ou `default` si elle manque."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Enregistre une donnée accessible aux nœuds suivants."""
        self.data[key] = value


class Node(ABC):
    """Classe de base d'un nœud exécutable avec retry configurable."""

    def __init__(self, name: str, retry: int = 0) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Le nom du nœud doit être une chaîne non vide.")
        if isinstance(retry, bool) or not isinstance(retry, int) or retry < 0:
            raise ValueError("retry doit être un entier positif ou nul.")
        self.name = name
        self.retry = retry

    @abstractmethod
    def execute(self, context: SharedContext) -> Any:
        """Exécute le nœud et retourne son résultat."""
        raise NotImplementedError


class NodeOut(Node):
    """Appelle une fonction Python qui reçoit le contexte partagé."""

    def __init__(
        self,
        name: str,
        function: Callable[[SharedContext], Any],
        retry: int = 0,
    ) -> None:
        super().__init__(name, retry)
        if not callable(function):
            raise TypeError("function doit être appelable.")
        self.function = function

    def execute(self, context: SharedContext) -> Any:
        """Appelle l'outil puis range son résultat sous le nom du nœud."""
        result = self.function(context)
        context.set(self.name, result)
        return result


class NodeModel(Node):
    """Appelle le modèle local avec un prompt fixe ou construit du contexte."""

    def __init__(
        self,
        name: str,
        prompt: str | Callable[[SharedContext], str],
        model_path: str | None = None,
        retry: int = 0,
    ) -> None:
        super().__init__(name, retry)
        self.prompt = prompt
        self.model_path = model_path

    def execute(self, context: SharedContext) -> str:
        """Envoie uniquement du texte au modèle et stocke la réponse."""
        prompt = (
            self.prompt(context) if callable(self.prompt) else self.prompt
        )
        if not isinstance(prompt, str):
            raise TypeError("Le prompt du modèle doit être une chaîne.")
        result = call_model(prompt, self.model_path)
        context.set(self.name, result)
        return result


class NodeCondition(Node):
    """Retourne le nom du nœud cible choisi par une condition."""

    def __init__(
        self,
        name: str,
        condition: Callable[[SharedContext], str],
        retry: int = 0,
    ) -> None:
        super().__init__(name, retry)
        self.condition = condition

    def execute(self, context: SharedContext) -> str:
        """Évalue la condition et enregistre son nom de branche."""
        branch = self.condition(context)
        if not isinstance(branch, str) or not branch:
            raise ValueError("La condition doit retourner un nom de branche.")
        context.state[self.name] = branch
        return branch


class WorkflowError(RuntimeError):
    """Erreur terminale d'un workflow ou d'une transition invalide."""


class Workflow:
    """Exécute une séquence de nœuds et applique leurs politiques de retry."""

    def __init__(self, nodes: list[Node]) -> None:
        self.nodes = list(nodes)
        indexes = [node.name for node in self.nodes]
        if len(set(indexes)) != len(indexes):
            raise ValueError("Chaque nœud du workflow doit avoir un nom unique.")
        self._indexes = {name: index for index, name in enumerate(indexes)}

    def run(
        self,
        initial_context: SharedContext | Mapping[str, Any],
    ) -> SharedContext:
        """Exécute le workflow et retourne le contexte final."""
        if isinstance(initial_context, SharedContext):
            context = initial_context
        elif isinstance(initial_context, Mapping):
            context = SharedContext(initial_context)
        else:
            raise TypeError("initial_context doit être un mapping.")

        context.state["status"] = "running"
        index = 0
        while index < len(self.nodes):
            node = self.nodes[index]
            context.state["current_node"] = node.name
            result = None
            for attempt in range(node.retry + 1):
                try:
                    result = node.execute(context)
                    break
                except Exception as exc:
                    context.errors.append(
                        {
                            "node": node.name,
                            "attempt": attempt + 1,
                            "error": str(exc),
                        }
                    )
                    if attempt == node.retry:
                        context.state["status"] = "failed"
                        raise WorkflowError(
                            f"Le nœud {node.name!r} a échoué après "
                            f"{attempt + 1} tentative(s): {exc}"
                        ) from exc

            if isinstance(node, NodeCondition):
                target = self._indexes.get(result)
                if target is None or target <= index:
                    context.state["status"] = "failed"
                    error = (
                        f"Branche invalide {result!r} pour le nœud "
                        f"{node.name!r}; la cible doit être un nœud suivant."
                    )
                    context.errors.append(
                        {"node": node.name, "attempt": 1, "error": error}
                    )
                    raise WorkflowError(error)
                index = target
            else:
                index += 1

        context.state["current_node"] = None
        context.state["status"] = "completed"
        return context
