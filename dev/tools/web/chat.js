// Chat client pour La Citadelle V2

let currentSessionId = null;
let currentChatDocument = null;
let isSending = false;
let isAdminUser = false;
let isAnalyzingDocument = false;
let isManagingChatDocument = false;
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
const chatDocumentFile = document.getElementById("chat-document-file");
const attachChatDocumentButton = document.getElementById("attach-chat-document");
const chatDocumentFormats = document.getElementById("chat-document-formats");
const chatDocumentName = document.getElementById("chat-document-name");
const removeChatDocumentButton = document.getElementById("remove-chat-document");
const analyzeDocumentButton = document.getElementById("analyze-document-button");
const workflowDialog = document.getElementById("workflow-dialog");
const workflowForm = document.getElementById("workflow-form");
const workflowType = document.getElementById("workflow-type");
const workflowPath = document.getElementById("workflow-path");
const workflowPrompt = document.getElementById("workflow-prompt");
const workflowDialogStatus = document.getElementById("workflow-dialog-status");
const workflowSubmitButton = document.getElementById("workflow-submit-button");
const workflowCancelButton = document.getElementById("workflow-cancel-button");

const workflowsByExtension = {
	".md": "analyse_md",
	".pdf": "analyse_pdf",
	".sql": "analyse_sql",
};
const allowedChatUploadExtensions = new Set([".md", ".txt", ".sql"]);

function renderMarkdown(content) {
	if (!window.marked || !window.DOMPurify) {
		return null;
	}

	const html = window.marked.parse(content, { breaks: true });
	return window.DOMPurify.sanitize(html, {
		ALLOWED_TAGS: [
			"a", "blockquote", "br", "code", "del", "em", "h1", "h2",
			"h3", "h4", "h5", "h6", "hr", "li", "ol", "p", "pre",
			"strong", "table", "tbody", "td", "th", "thead", "tr", "ul",
		],
		ALLOWED_ATTR: ["href", "title"],
		ALLOW_DATA_ATTR: false,
		RETURN_DOM_FRAGMENT: true,
	});
}

function showStatus(message, isError = false) {
	statusDiv.textContent = message;
	statusDiv.className = isError ? "status error" : "status";
}

async function loadChatDocumentCapabilities() {
	try {
		const response = await fetch("/api/chat/upload/capabilities", {
			credentials: "same-origin",
		});
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		const data = await response.json().catch(() => ({}));
		if (!response.ok) {
			chatDocumentFormats.textContent =
				typeof data.error === "string"
					? `Formats indisponibles : ${data.error}`
					: "Impossible de charger les formats disponibles.";
			return;
		}
		const extensions = data.extensions;
		if (
			!Array.isArray(extensions)
			|| !extensions.includes(".md")
			|| extensions.some(
				(extension) => !allowedChatUploadExtensions.has(extension),
			)
			|| new Set(extensions).size !== extensions.length
		) {
			chatDocumentFormats.textContent = "Réponse de capacités invalide.";
			return;
		}
		chatDocumentFile.accept = extensions.join(",");
		chatDocumentFormats.textContent =
			`Formats disponibles : ${extensions.join(", ")}`;
	} catch (error) {
		chatDocumentFormats.textContent =
			`Erreur de chargement des formats : ${error.message}`;
	}
}

function updateAnalyzeDocumentButton() {
	analyzeDocumentButton.disabled =
		!isAdminUser
		|| currentSessionId === null
		|| userInput.disabled
		|| isSending
		|| isAnalyzingDocument
		|| isManagingChatDocument;
}

function updateChatDocumentControls() {
	const hasDocument = currentChatDocument !== null;
	const busy =
		currentSessionId === null
		|| userInput.disabled
		|| isSending
		|| isAnalyzingDocument
		|| isManagingChatDocument;
	attachChatDocumentButton.hidden = hasDocument;
	attachChatDocumentButton.disabled = busy;
	chatDocumentFile.disabled = busy || hasDocument;
	chatDocumentName.hidden = !hasDocument;
	if (hasDocument) {
		const fileName = currentChatDocument.metadata.file_name;
		const partial = currentChatDocument.metadata.characters > 6000;
		chatDocumentName.textContent = partial
			? `Document : ${fileName} (réponses basées sur des extraits)`
			: `Document : ${fileName}`;
	} else {
		chatDocumentName.textContent = "";
	}
	removeChatDocumentButton.hidden = !hasDocument;
	removeChatDocumentButton.disabled = busy;
}

function createMessage(role, content) {
	const message = document.createElement("div");
	message.className = `message ${role}`;
	if (role === "assistant") {
		const rendered = renderMarkdown(content);
		if (rendered) {
			message.appendChild(rendered);
		} else {
			message.textContent = content;
		}
	} else {
		message.textContent = content;
	}
	return message;
}

function renderAssistantMarkdown(message, content) {
	const rendered = renderMarkdown(content);
	if (rendered) {
		message.replaceChildren(rendered);
	} else {
		message.textContent = content;
	}
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
		isAdminUser = user.role === "admin";
		adminLink.hidden = !isAdminUser;
		analyzeDocumentButton.hidden = !isAdminUser;
		updateAnalyzeDocumentButton();
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
	if (isAnalyzingDocument || isManagingChatDocument) return;
	currentSessionId = sessionId;
	currentChatDocument = null;
	for (const item of sessionsList.querySelectorAll("li[data-session-id]")) {
		item.classList.toggle("active", Number(item.dataset.sessionId) === sessionId);
	}
	userInput.disabled = true;
	sendBtn.disabled = true;
	updateAnalyzeDocumentButton();
	updateChatDocumentControls();
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
		currentChatDocument =
			data.document
			&& Number.isSafeInteger(data.document.id)
			&& data.document.metadata
			&& typeof data.document.metadata.file_name === "string"
				? data.document
				: null;
		messagesDiv.replaceChildren();
		for (const message of data.messages || []) {
			messagesDiv.appendChild(createMessage(message.role, message.content));
		}
		if (!data.messages || data.messages.length === 0) {
			showMessagesPlaceholder("Commencez la conversation.");
		}
		userInput.disabled = false;
		sendBtn.disabled = false;
		updateAnalyzeDocumentButton();
		updateChatDocumentControls();
		showStatus("");
		userInput.focus();
	} catch (error) {
		showStatus(`Erreur réseau : ${error.message}`, true);
		showMessagesPlaceholder("Impossible de charger cette conversation.");
		updateChatDocumentControls();
	}
}

async function uploadChatDocument(file) {
	if (
		!file
		|| currentSessionId === null
		|| currentChatDocument !== null
		|| isSending
		|| isAnalyzingDocument
		|| isManagingChatDocument
	) return;

	isManagingChatDocument = true;
	updateAnalyzeDocumentButton();
	updateChatDocumentControls();
	showStatus("Téléversement du document...");
	const form = new FormData();
	form.append("session_id", String(currentSessionId));
	form.append("file", file, file.name);

	try {
		const response = await fetch("/api/chat/upload", {
			method: "POST",
			headers: csrfHeaders(),
			body: form,
			credentials: "same-origin",
		});
		const data = await response.json().catch(() => ({}));
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		if (!response.ok) {
			showStatus(data.error || "Erreur de téléversement du document.", true);
			return;
		}
		if (
			!Number.isSafeInteger(data.document_id)
			|| !data.metadata
			|| typeof data.metadata.file_name !== "string"
		) {
			showStatus("Réponse de téléversement du document invalide.", true);
			return;
		}
		currentChatDocument = {
			id: data.document_id,
			metadata: data.metadata,
		};
		showStatus(`Document joint : ${data.metadata.file_name}`);
	} catch (error) {
		showStatus(`Erreur réseau : ${error.message}`, true);
	} finally {
		isManagingChatDocument = false;
		chatDocumentFile.value = "";
		updateAnalyzeDocumentButton();
		updateChatDocumentControls();
	}
}

async function removeChatDocument() {
	if (
		currentChatDocument === null
		|| isSending
		|| isAnalyzingDocument
		|| isManagingChatDocument
	) return;

	isManagingChatDocument = true;
	updateAnalyzeDocumentButton();
	updateChatDocumentControls();
	try {
		const response = await fetch(
			`/api/chat/document/${currentChatDocument.id}`,
			{
				method: "DELETE",
				headers: csrfHeaders(),
				credentials: "same-origin",
			}
		);
		const data = await response.json().catch(() => ({}));
		if (response.status === 401) {
			window.location.href = "/login";
			return;
		}
		if (!response.ok) {
			showStatus(data.error || "Erreur de retrait du document.", true);
			return;
		}
		currentChatDocument = null;
		showStatus(
			"Document retiré; les messages restent dans l’historique."
		);
	} catch (error) {
		showStatus(`Erreur réseau : ${error.message}`, true);
	} finally {
		isManagingChatDocument = false;
		updateAnalyzeDocumentButton();
		updateChatDocumentControls();
	}
}

async function sendMessage(content) {
	if (
		currentSessionId === null
		|| isSending
		|| isAnalyzingDocument
		|| isManagingChatDocument
	) return;

	isSending = true;
	userInput.disabled = true;
	sendBtn.disabled = true;
	updateAnalyzeDocumentButton();
	updateChatDocumentControls();
	const loading = createMessage("assistant loading", "Réponse en cours...");
	let assistantMessage = null;
	let streamedContent = "";
	messagesDiv.appendChild(loading);
	messagesDiv.scrollTop = messagesDiv.scrollHeight;
	showStatus("Le modèle prépare une réponse...");

	try {
		const streamRequested = typeof ReadableStream !== "undefined";
		const response = await fetch(
			`/api/sessions/${currentSessionId}/messages`,
			{
				method: "POST",
				headers: csrfHeaders({ "Content-Type": "application/json" }),
				body: JSON.stringify({ content, stream: streamRequested }),
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

		if (!response.body || typeof response.body.getReader !== "function") {
			const data = await response.json();
			loading.remove();
			messagesDiv.appendChild(createMessage("user", content));
			messagesDiv.appendChild(
				createMessage("assistant", data.assistant_message.content)
			);
			messagesDiv.scrollTop = messagesDiv.scrollHeight;
			userInput.value = "";
			showStatus("");
			return;
		}

		loading.remove();
		messagesDiv.appendChild(createMessage("user", content));
		assistantMessage = document.createElement("div");
		assistantMessage.className = "message assistant thinking";
		const thinkingLabel = document.createElement("p");
		thinkingLabel.className = "thinking-label";
		thinkingLabel.textContent = "Nexxus réfléchit…";
		assistantMessage.appendChild(thinkingLabel);
		messagesDiv.appendChild(assistantMessage);
		userInput.value = "";
		messagesDiv.scrollTop = messagesDiv.scrollHeight;

		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let pending = "";
		let streamFinished = false;
		const processEvent = (eventText) => {
			for (const line of eventText.split(/\r?\n/)) {
				if (!line.startsWith("data:")) continue;
				const data = line.slice(5).trim();
				if (!data) continue;

				const event = JSON.parse(data);
				if (event.status === "thinking") {
					assistantMessage.classList.add("thinking");
					continue;
				}
				if (typeof event.delta === "string" && event.delta) {
					thinkingLabel.remove();
					assistantMessage.classList.remove("thinking");
					assistantMessage.classList.add("streaming");
					streamedContent += event.delta;
					renderAssistantMarkdown(assistantMessage, streamedContent);
					messagesDiv.scrollTop = messagesDiv.scrollHeight;
					continue;
				}
				if (event.done === true) {
					if (typeof event.content === "string") {
						streamedContent = event.content;
						renderAssistantMarkdown(
							assistantMessage,
							streamedContent
						);
					}
					thinkingLabel.remove();
					assistantMessage.classList.remove("thinking", "streaming");
					if (
						Number.isFinite(event.duration_ms)
						&& event.duration_ms >= 0
					) {
						const durationSpan = document.createElement("span");
						durationSpan.className = "message-duration";
						durationSpan.textContent =
							`⏱️ ${(event.duration_ms / 1000).toFixed(1)}s`;
						assistantMessage.appendChild(durationSpan);
					}
					showStatus("");
					streamFinished = true;
					return;
				}
				if (typeof event.error === "string") {
					thinkingLabel.remove();
					assistantMessage.classList.remove("thinking", "streaming");
					if (!streamedContent) assistantMessage.remove();
					showStatus(event.error, true);
					streamFinished = true;
					return;
				}
			}
		};

		try {
			while (!streamFinished) {
				const { value, done } = await reader.read();
				pending += decoder.decode(
					value || new Uint8Array(),
					{ stream: !done }
				);
				const events = pending.split(/\r?\n\r?\n/);
				pending = events.pop() || "";
				for (const eventText of events) {
					processEvent(eventText);
					if (streamFinished) break;
				}
				if (done && !streamFinished) {
					if (pending.trim()) processEvent(pending);
					if (!streamFinished) {
						throw new Error("Le flux s'est terminé sans événement final.");
					}
				}
			}
			if (streamFinished) await reader.cancel();
		} finally {
			reader.releaseLock();
		}
	} catch (error) {
		loading.remove();
		if (assistantMessage) {
			assistantMessage.classList.remove("thinking", "streaming");
			const label = assistantMessage.querySelector(".thinking-label");
			if (label) label.remove();
			if (!streamedContent) assistantMessage.remove();
		}
		showStatus(`Erreur réseau : ${error.message}`, true);
	} finally {
		isSending = false;
		if (currentSessionId !== null) {
			userInput.disabled = false;
			sendBtn.disabled = false;
		}
		updateAnalyzeDocumentButton();
		updateChatDocumentControls();
	}
}

function detectWorkflow(path) {
	const fileName = path.split(/[\\/]/).pop() || "";
	const extensionIndex = fileName.lastIndexOf(".");
	if (extensionIndex < 0) return null;
	return workflowsByExtension[fileName.slice(extensionIndex).toLowerCase()] || null;
}

function showWorkflowError(message) {
	workflowDialogStatus.textContent = message;
	workflowDialogStatus.hidden = false;
}

analyzeDocumentButton.addEventListener("click", () => {
	workflowDialogStatus.hidden = true;
	workflowDialog.showModal();
	workflowPath.focus();
});

workflowCancelButton.addEventListener("click", () => workflowDialog.close());

workflowPath.addEventListener("input", () => {
	const workflow = detectWorkflow(workflowPath.value.trim());
	if (workflow) workflowType.value = workflow;
});

workflowForm.addEventListener("submit", async (event) => {
	event.preventDefault();
	if (
		!isAdminUser
		|| currentSessionId === null
		|| isAnalyzingDocument
		|| isManagingChatDocument
		|| isSending
	) return;

	const path = workflowPath.value.trim();
	const prompt = workflowPrompt.value.trim();
	const workflow = detectWorkflow(path);
	if (!workflow) {
		showWorkflowError("Seuls les fichiers .md, .pdf et .sql sont pris en charge.");
		return;
	}
	if (!prompt) {
		showWorkflowError("Saisissez une question sur le document.");
		return;
	}
	workflowType.value = workflow;
	workflowDialogStatus.hidden = true;
	isAnalyzingDocument = true;
	workflowSubmitButton.disabled = true;
	workflowCancelButton.disabled = true;
	workflowSubmitButton.textContent = "Analyse en cours...";
	userInput.disabled = true;
	sendBtn.disabled = true;
	newSessionBtn.disabled = true;
	updateAnalyzeDocumentButton();
	updateChatDocumentControls();

	const loading = createMessage(
		"assistant loading",
		"Analyse du document en cours..."
	);
	messagesDiv.appendChild(loading);
	messagesDiv.scrollTop = messagesDiv.scrollHeight;

	try {
		const response = await fetch("/api/workflow/run", {
			method: "POST",
			headers: csrfHeaders({ "Content-Type": "application/json" }),
			body: JSON.stringify({ workflow, path, prompt }),
			credentials: "same-origin",
		});
		const data = await response.json().catch(() => ({}));
		if (!response.ok) {
			if (response.status === 401) {
				window.location.href = "/login";
				return;
			}
			const errorMessage = data && typeof data.error === "string"
				? data.error
				: "Erreur inconnue.";
			showWorkflowError(
				`Erreur HTTP ${response.status} : ${errorMessage}`
			);
			return;
		}
		if (!data || typeof data.response !== "string") {
			showWorkflowError("Réponse du workflow invalide.");
			return;
		}

		loading.remove();
		messagesDiv.appendChild(
			createMessage("user", `Analyser ${path}\n${prompt}`)
		);
		messagesDiv.appendChild(createMessage("assistant", data.response));
		messagesDiv.scrollTop = messagesDiv.scrollHeight;
		workflowDialog.close();
		workflowForm.reset();
		showStatus("");
	} catch (error) {
		showWorkflowError(`Erreur réseau : ${error.message}`);
	} finally {
		loading.remove();
		isAnalyzingDocument = false;
		workflowSubmitButton.disabled = false;
		workflowCancelButton.disabled = false;
		workflowSubmitButton.textContent = "Analyser";
		if (currentSessionId !== null) {
			userInput.disabled = false;
			sendBtn.disabled = false;
		}
		newSessionBtn.disabled = false;
		updateAnalyzeDocumentButton();
		updateChatDocumentControls();
	}
});

async function createNewSession() {
	if (isAnalyzingDocument || isManagingChatDocument) return;
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
attachChatDocumentButton.addEventListener("click", () => {
	if (!attachChatDocumentButton.disabled) chatDocumentFile.click();
});
chatDocumentFile.addEventListener("change", () => {
	uploadChatDocument(chatDocumentFile.files[0]);
});
removeChatDocumentButton.addEventListener("click", removeChatDocument);

updateChatDocumentControls();
loadChatDocumentCapabilities();
loadPreferences();
loadAdminLink();
loadSessions();
