"""Tests ciblés du moteur d'orchestration AIWorkflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from workflow_engine import (
    Node,
    NodeCondition,
    NodeModel,
    NodeOut,
    SharedContext,
    Workflow,
    WorkflowError,
)


def test_shared_context_get_set():
    context = SharedContext({"input": "hello"})

    assert context.get("input") == "hello"
    assert context.get("missing", "default") == "default"
    context.set("output", "world")
    assert context.data["output"] == "world"
    assert context.state == {}
    assert context.errors == []


def test_node_out_executes_and_stores_result():
    context = SharedContext({"value": 4})
    node = NodeOut("doubled", lambda current: current.get("value") * 2)

    assert node.execute(context) == 8
    assert context.get("doubled") == 8


def test_node_model_passes_configured_timeout_to_http():
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(
        {"choices": [{"message": {"content": "answer"}}]}
    ).encode("utf-8")
    context = SharedContext({"model_prompt": "Explain FTS5"})
    node = NodeModel(
        "model",
        "model_prompt",
        "answer",
        timeout=180,
        model_path="model.gguf",
    )

    with patch(
        "client.urllib.request.urlopen",
        return_value=response,
    ) as urlopen:
        assert node.execute(context) == "answer"

    assert urlopen.call_args.kwargs["timeout"] == 180
    assert json.loads(urlopen.call_args.args[0].data)["model"] == "model.gguf"
    assert context.get("answer") == "answer"


def test_node_condition_returns_and_records_branch():
    context = SharedContext()
    node = NodeCondition("decision", lambda _: "approved")

    assert node.execute(context) == "approved"
    assert context.state["decision"] == "approved"


def test_workflow_runs_nodes_in_order():
    calls = []
    workflow = Workflow(
        [
            NodeOut("first", lambda context: calls.append("first") or 1),
            NodeOut("second", lambda context: calls.append("second") or 2),
        ]
    )

    result = workflow.run({})

    assert calls == ["first", "second"]
    assert result.data == {"first": 1, "second": 2}
    assert result.state["status"] == "completed"


def test_workflow_retries_node_and_records_transient_error():
    class FlakyNode(Node):
        def __init__(self):
            super().__init__("flaky", retry=1)
            self.calls = 0

        def execute(self, context):
            self.calls += 1
            if self.calls == 1:
                raise ValueError("temporary")
            return "ok"

    node = FlakyNode()
    result = Workflow([node]).run({})

    assert node.calls == 2
    assert result.state["status"] == "completed"
    assert result.errors[0]["error"] == "temporary"


def test_workflow_stops_after_retries_are_exhausted():
    calls = []

    class FailingNode(Node):
        def execute(self, context):
            calls.append(self.name)
            raise ValueError("failed")

    context = SharedContext()
    workflow = Workflow(
        [
            FailingNode("failure", retry=1),
            NodeOut("unreached", lambda _: calls.append("unreached")),
        ]
    )

    with pytest.raises(WorkflowError, match="échoué après 2 tentative"):
        workflow.run(context)

    assert calls == ["failure", "failure"]
    assert context.state["status"] == "failed"
    assert len(context.errors) == 2


def test_workflow_condition_jumps_to_named_forward_branch():
    workflow = Workflow(
        [
            NodeCondition("route", lambda _: "chosen"),
            NodeOut("skipped", lambda _: "wrong"),
            NodeOut("chosen", lambda _: "right"),
        ]
    )

    result = workflow.run({})

    assert result.get("chosen") == "right"
    assert "skipped" not in result.data
