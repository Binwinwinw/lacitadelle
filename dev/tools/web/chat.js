// Chat client pour La Citadelle V2

let currentSessionId = null;
let isSending = false;
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

function csrfHeaders(headers = {}) {
	return { ...headers, "X-CSRF-Token": csrfToken };
}

const sessionsList = document.getElementById("sessions-list");
const messagesDiv = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const newSessionBtn = document.getElementById("new-session");
const statusDiv = document.getElementById("status");
const adminLink = document.getElementById("admin-link");

function showStatus(message, isError = false) {
	statusDiv.textContent = message;
	statusDiv.className = isError ? "status error" : "status";
}

function createMessage(role, content) {
	const message = document.createElement("div");
	message.className = `message ${role}`;
	message.textContent = content;
	return message;
}

function showMessagesPlaceholder(text) {
	const placeholder = document.createElement("p");
	placeholder.className = "placeholder";
	placeholder.textContent = text;
	messagesDiv.replaceChildren(placeholder);
}

function applyPreferences(preferences) {
	document.documentElement.dataset.theme = preferences.theme;
	document.documentElement.dataset.fontSize = preferences.font_size;
}

async function loadPreferences() {
	try {
		const response = await fetch("/api/preferences", {
			credentials: "same-origin",
		});
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		if (!response.ok) {
			showStatus("Erreur de chargement des préférences.", true);
			return;
		}
		applyPreferences(await response.json());
	} catch (error) {
		showStatus(`Erreur réseau : ${error.message}`, true);
	}
}

async function loadAdminLink() {
	try {
		const response = await fetch("/api/me", {
			credentials: "same-origin",
		});
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		if (!response.ok) {
			showStatus("Erreur de vérification du rôle.", true);
			return;
		}
		const user = await response.json();
		adminLink.hidden = user.role !== "admin";
	} catch (error) {
		showStatus(`Erreur réseau : ${error.message}`, true);
	}
}

function renderSessions(sessions) {
	sessionsList.replaceChildren();
	if (!sessions.length) {
		const empty = document.createElement("li");
		empty.textContent = "Aucune session. Créez-en une.";
		empty.classList.add("empty");
		sessionsList.appendChild(empty);
		return;
	}

	for (const session of sessions) {
		const item = document.createElement("li");
		item.textContent = session.title || `Session #${session.id}`;
		item.dataset.sessionId = session.id;
		item.classList.toggle("active", session.id === currentSessionId);
		item.addEventListener("click", () => selectSession(session.id));
		sessionsList.appendChild(item);
	}
}

async function loadSessions() {
	try {
		const response = await fetch("/api/sessions", {
			credentials: "same-origin",
		});
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		if (!response.ok) {
			showStatus("Erreur de chargement des sessions.", true);
			return;
		}

		const data = await response.json();
		renderSessions(Array.isArray(data.sessions) ? data.sessions : []);
		showStatus("");
	} catch (error) {
		showStatus(`Erreur réseau : ${error.message}`, true);
	}
}

async function selectSession(sessionId) {
	currentSessionId = sessionId;
	for (const item of sessionsList.querySelectorAll("li[data-session-id]")) {
		item.classList.toggle("active", Number(item.dataset.sessionId) === sessionId);
	}
	userInput.disabled = true;
	sendBtn.disabled = true;
	showMessagesPlaceholder("Chargement de la conversation...");
	showStatus("Chargement...");

	try {
		const response = await fetch(`/api/sessions/${sessionId}/messages`, {
			credentials: "same-origin",
		});
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		if (!response.ok) {
			showStatus("Erreur de chargement des messages.", true);
			showMessagesPlaceholder("Impossible de charger cette conversation.");
			return;
		}

		const data = await response.json();
		messagesDiv.replaceChildren();
		for (const message of data.messages || []) {
			messagesDiv.appendChild(createMessage(message.role, message.content));
		}
		if (!data.messages || data.messages.length === 0) {
			showMessagesPlaceholder("Commencez la conversation.");
		}
		userInput.disabled = false;
		sendBtn.disabled = false;
		showStatus("");
		userInput.focus();
	} catch (error) {
		showStatus(`Erreur réseau : ${error.message}`, true);
		showMessagesPlaceholder("Impossible de charger cette conversation.");
	}
}

async function sendMessage(content) {
	if (currentSessionId === null || isSending) return;

	isSending = true;
	userInput.disabled = true;
	sendBtn.disabled = true;
	const loading = createMessage("assistant loading", "Réponse en cours...");
	messagesDiv.appendChild(loading);
	messagesDiv.scrollTop = messagesDiv.scrollHeight;
	showStatus("Le modèle prépare une réponse...");

	try {
		const response = await fetch(
			`/api/sessions/${currentSessionId}/messages`,
			{
				method: "POST",
				headers: csrfHeaders({ "Content-Type": "application/json" }),
				body: JSON.stringify({ content }),
				credentials: "same-origin",
			}
		);
		loading.remove();
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			const message = response.status === 502
				? "Le modèle est indisponible. Réessayez."
				: errorData.error || "Erreur lors de l'envoi du message.";
			showStatus(message, true);
			return;
		}

		const data = await response.json();
		messagesDiv.appendChild(createMessage("user", content));
		messagesDiv.appendChild(
			createMessage("assistant", data.assistant_message.content)
		);
		messagesDiv.scrollTop = messagesDiv.scrollHeight;
		userInput.value = "";
		showStatus("");
	} catch (error) {
		loading.remove();
		showStatus(`Erreur réseau : ${error.message}`, true);
	} finally {
		isSending = false;
		if (currentSessionId !== null) {
			userInput.disabled = false;
			sendBtn.disabled = false;
		}
	}
}

async function createNewSession() {
	newSessionBtn.disabled = true;
	showStatus("Création de la session...");
	try {
		const response = await fetch("/api/sessions", {
			method: "POST",
			headers: csrfHeaders({ "Content-Type": "application/json" }),
			body: JSON.stringify({}),
			credentials: "same-origin",
		});
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		if (!response.ok) {
			showStatus("Erreur de création de la session.", true);
			return;
		}

		const data = await response.json();
		await loadSessions();
		await selectSession(data.session_id);
	} catch (error) {
		showStatus(`Erreur réseau : ${error.message}`, true);
	} finally {
		newSessionBtn.disabled = false;
	}
}

chatForm.addEventListener("submit", (event) => {
	event.preventDefault();
	const content = userInput.value.trim();
	if (content) sendMessage(content);
});

userInput.addEventListener("keydown", (event) => {
	if (event.key === "Enter" && !event.shiftKey) {
		event.preventDefault();
		chatForm.requestSubmit();
	}
});

newSessionBtn.addEventListener("click", createNewSession);

loadPreferences();
loadAdminLink();
loadSessions();
