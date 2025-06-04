const vscode = require('vscode');
const path = require('path');

/**
 * Cherry AI Tools Extension for Cursor IDE
 * Provides integrated AI coding assistance with persona switching
 */

let aiToolsPanel = undefined;
let currentPersona = 'cherry';

function activate(context) {
    console.log('Cherry AI Tools extension is now active!');

    // Register commands
    const openPanelCommand = vscode.commands.registerCommand('cherry-ai.openPanel', () => {
        createOrShowAIToolsPanel(context.extensionPath);
    });

    const optimizeCodeCommand = vscode.commands.registerCommand('cherry-ai.optimizeCode', () => {
        handleCodeOptimization();
    });

    const explainCodeCommand = vscode.commands.registerCommand('cherry-ai.explainCode', () => {
        handleCodeExplanation();
    });

    const generateTestsCommand = vscode.commands.registerCommand('cherry-ai.generateTests', () => {
        handleTestGeneration();
    });

    const refactorCodeCommand = vscode.commands.registerCommand('cherry-ai.refactorCode', () => {
        handleCodeRefactoring();
    });

    const switchPersonaCommand = vscode.commands.registerCommand('cherry-ai.switchPersona', () => {
        handlePersonaSwitch();
    });

    // Register tree data provider for sidebar
    const aiToolsProvider = new AIToolsProvider();
    vscode.window.registerTreeDataProvider('cherry-ai-tools', aiToolsProvider);

    // Add status bar item
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = `🍒 ${currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)}`;
    statusBarItem.tooltip = 'Cherry AI Tools - Click to switch persona';
    statusBarItem.command = 'cherry-ai.switchPersona';
    statusBarItem.show();

    // Auto-open panel on startup
    createOrShowAIToolsPanel(context.extensionPath);

    context.subscriptions.push(
        openPanelCommand,
        optimizeCodeCommand,
        explainCodeCommand,
        generateTestsCommand,
        refactorCodeCommand,
        switchPersonaCommand,
        statusBarItem
    );
}

function createOrShowAIToolsPanel(extensionPath) {
    const columnToShowIn = vscode.window.activeTextEditor
        ? vscode.window.activeTextEditor.viewColumn
        : undefined;

    if (aiToolsPanel) {
        aiToolsPanel.reveal(columnToShowIn);
        return;
    }

    aiToolsPanel = vscode.window.createWebviewPanel(
        'cherryAITools',
        'Cherry AI Tools',
        vscode.ViewColumn.Beside,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.file(path.join(extensionPath, 'webview'))
            ]
        }
    );

    aiToolsPanel.webview.html = getWebviewContent(aiToolsPanel.webview, extensionPath);

    // Handle messages from webview
    aiToolsPanel.webview.onDidReceiveMessage(
        message => {
            switch (message.command) {
                case 'switchPersona':
                    currentPersona = message.persona;
                    vscode.window.showInformationMessage(`Switched to ${message.persona} persona`);
                    break;
                case 'optimizeCode':
                    handleCodeOptimization(message.code);
                    break;
                case 'explainCode':
                    handleCodeExplanation(message.code);
                    break;
                case 'generateTests':
                    handleTestGeneration(message.code);
                    break;
            }
        },
        undefined,
        []
    );

    aiToolsPanel.onDidDispose(
        () => {
            aiToolsPanel = undefined;
        },
        null,
        []
    );
}

function getWebviewContent(webview, extensionPath) {
    const webviewPath = path.join(extensionPath, 'webview');
    const htmlPath = vscode.Uri.file(path.join(webviewPath, 'index.html'));
    const cssPath = vscode.Uri.file(path.join(webviewPath, 'style.css'));
    const jsPath = vscode.Uri.file(path.join(webviewPath, 'script.js'));

    const htmlUri = webview.asWebviewUri(htmlPath);
    const cssUri = webview.asWebviewUri(cssPath);
    const jsUri = webview.asWebviewUri(jsPath);

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cherry AI Tools</title>
    <link href="${cssUri}" rel="stylesheet">
</head>
<body>
    <div id="app">
        <div class="header">
            <h2>🍒 Cherry AI Tools</h2>
            <div class="persona-selector">
                <button class="persona-btn active" data-persona="cherry">🍒 Cherry</button>
                <button class="persona-btn" data-persona="sophia">💼 Sophia</button>
                <button class="persona-btn" data-persona="karen">🏥 Karen</button>
            </div>
        </div>
        
        <div class="tools-section">
            <h3>Quick Actions</h3>
            <div class="tool-buttons">
                <button class="tool-btn" onclick="optimizeSelectedCode()">🚀 Optimize Code</button>
                <button class="tool-btn" onclick="explainSelectedCode()">💡 Explain Code</button>
                <button class="tool-btn" onclick="generateTests()">🧪 Generate Tests</button>
                <button class="tool-btn" onclick="refactorCode()">🔧 Refactor</button>
            </div>
        </div>
        
        <div class="chat-section">
            <h3>AI Chat</h3>
            <div id="chat-messages"></div>
            <div class="chat-input">
                <input type="text" id="chat-input" placeholder="Ask your AI assistant...">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <div class="status-section">
            <h3>Tool Status</h3>
            <div class="status-grid">
                <div class="status-item">
                    <span class="status-label">Roo Coder:</span>
                    <span class="status-value active">Active</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Cursor AI:</span>
                    <span class="status-value active">Connected</span>
                </div>
                <div class="status-item">
                    <span class="status-label">OpenAI Codex:</span>
                    <span class="status-value pending">Setup Required</span>
                </div>
            </div>
        </div>
    </div>
    <script src="${jsUri}"></script>
</body>
</html>`;
}

async function handleCodeOptimization(code) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor found');
        return;
    }

    const selectedText = code || editor.document.getText(editor.selection);
    if (!selectedText) {
        vscode.window.showErrorMessage('No code selected');
        return;
    }

    vscode.window.showInformationMessage(`Optimizing code with ${currentPersona} persona...`);
    
    // Here you would integrate with your AI API
    // For now, show a placeholder response
    const optimizedCode = `// Optimized by ${currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)}\n${selectedText}`;
    
    // Replace selected text with optimized version
    editor.edit(editBuilder => {
        editBuilder.replace(editor.selection, optimizedCode);
    });
}

async function handleCodeExplanation() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor found');
        return;
    }

    const selectedText = editor.document.getText(editor.selection);
    if (!selectedText) {
        vscode.window.showErrorMessage('No code selected');
        return;
    }

    vscode.window.showInformationMessage(`${currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)} is explaining your code...`);
    
    // Show explanation in a new document
    const explanation = `Code Explanation by ${currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)}:\n\n${selectedText}\n\n// This code does...`;
    
    const doc = await vscode.workspace.openTextDocument({
        content: explanation,
        language: 'markdown'
    });
    vscode.window.showTextDocument(doc);
}

async function handleTestGeneration() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor found');
        return;
    }

    vscode.window.showInformationMessage(`${currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)} is generating tests...`);
    
    // Generate test file
    const testContent = `// Tests generated by ${currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)}\n// Add your test cases here`;
    
    const doc = await vscode.workspace.openTextDocument({
        content: testContent,
        language: 'javascript'
    });
    vscode.window.showTextDocument(doc);
}

async function handleCodeRefactoring() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor found');
        return;
    }

    vscode.window.showInformationMessage(`${currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)} is refactoring your code...`);
}

async function handlePersonaSwitch() {
    const personas = ['cherry', 'sophia', 'karen'];
    const selected = await vscode.window.showQuickPick(personas, {
        placeHolder: 'Select AI persona'
    });
    
    if (selected) {
        currentPersona = selected;
        vscode.window.showInformationMessage(`Switched to ${selected} persona`);
    }
}

class AIToolsProvider {
    getTreeItem(element) {
        return element;
    }

    getChildren(element) {
        if (!element) {
            return [
                new AIToolItem('🍒 Cherry Personal', 'cherry-persona'),
                new AIToolItem('💼 Sophia Business', 'sophia-persona'),
                new AIToolItem('🏥 Karen Healthcare', 'karen-persona'),
                new AIToolItem('🚀 Optimize Code', 'optimize-code'),
                new AIToolItem('💡 Explain Code', 'explain-code'),
                new AIToolItem('🧪 Generate Tests', 'generate-tests')
            ];
        }
        return [];
    }
}

class AIToolItem extends vscode.TreeItem {
    constructor(label, command) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.command = {
            command: `cherry-ai.${command}`,
            title: label
        };
    }
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};

