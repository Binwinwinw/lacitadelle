const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const chatScriptPath = path.join(
	__dirname,
	"..",
	"tools",
	"web",
	"chat.js"
);
const source = readFileSync(chatScriptPath, "utf8");
const workflowMap = source.match(
	/^const workflowsByExtension = \{[\s\S]*?^\};/m
);
const detector = source.match(
	/^function detectWorkflow\(path\) \{[\s\S]*?^\}/m
);

if (!workflowMap || !detector) {
	throw new Error("Workflow mapping or detector not found in chat.js");
}

const sandbox = {};
vm.runInNewContext(
	`${workflowMap[0]}\n${detector[0]}\nglobalThis.detectWorkflow = detectWorkflow;`,
	sandbox,
	{ filename: chatScriptPath }
);

assert.equal(sandbox.detectWorkflow("dev/docs/guide.md"), "analyse_md");
assert.equal(sandbox.detectWorkflow("dev/docs/guide.pdf"), "analyse_pdf");
assert.equal(sandbox.detectWorkflow("dev\\tests\\query.SQL"), "analyse_sql");
assert.equal(sandbox.detectWorkflow("dev/docs/notes.txt"), null);

console.log("workflow chat detection: OK");
