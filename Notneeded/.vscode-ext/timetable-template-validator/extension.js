const vscode = require('vscode');
const { spawn } = require('child_process');
const path = require('path');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Timetable Template Validator is now active');

    // Create diagnostics collection
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('timetable-template-validator');
    context.subscriptions.push(diagnosticCollection);

    // Register command to validate current file
    const validateCommand = vscode.commands.registerCommand('timetable-template-validator.validateCurrentFile', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            validateDocument(editor.document, diagnosticCollection);
        }
    });
    context.subscriptions.push(validateCommand);

    // Register validation on save if enabled
    const onSaveValidation = vscode.workspace.onDidSaveTextDocument(document => {
        const config = vscode.workspace.getConfiguration('timetableTemplateValidator');
        if (config.get('enable') && config.get('validateOnSave') && isHtmlFile(document)) {
            validateDocument(document, diagnosticCollection);
        }
    });
    context.subscriptions.push(onSaveValidation);

    // Register validation on type if enabled (throttled)
    let typeTimeout = null;
    const onTypeValidation = vscode.workspace.onDidChangeTextDocument(event => {
        const config = vscode.workspace.getConfiguration('timetableTemplateValidator');
        if (config.get('enable') && config.get('validateOnType') && isHtmlFile(event.document)) {
            if (typeTimeout) {
                clearTimeout(typeTimeout);
            }
            typeTimeout = setTimeout(() => {
                validateDocument(event.document, diagnosticCollection);
                typeTimeout = null;
            }, 1000); // Throttle to once per second
        }
    });
    context.subscriptions.push(onTypeValidation);

    // Clear diagnostics when document is closed
    context.subscriptions.push(
        vscode.workspace.onDidCloseTextDocument(document => {
            if (isHtmlFile(document)) {
                diagnosticCollection.delete(document.uri);
            }
        })
    );

    // Validate all open HTML documents
    vscode.workspace.textDocuments.forEach(document => {
        if (isHtmlFile(document)) {
            validateDocument(document, diagnosticCollection);
        }
    });
}

/**
 * Check if a document is an HTML file
 * @param {vscode.TextDocument} document 
 * @returns {boolean}
 */
function isHtmlFile(document) {
    return document.languageId === 'html' || document.fileName.endsWith('.html');
}

/**
 * Validate an HTML document using the template validator
 * @param {vscode.TextDocument} document 
 * @param {vscode.DiagnosticCollection} diagnosticCollection 
 */
function validateDocument(document, diagnosticCollection) {
    // Clear existing diagnostics
    diagnosticCollection.delete(document.uri);

    // Save document to a temporary file if it's unsaved
    const filePath = document.fileName;
    const workspacePath = vscode.workspace.getWorkspaceFolder(document.uri)?.uri.fsPath;
    
    if (!workspacePath) {
        vscode.window.showErrorMessage('Unable to determine workspace folder for template validation');
        return;
    }

    // Create relative path for diagnostics
    const relativePath = path.relative(workspacePath, filePath);

    // Call the Python validator script
    const pythonPath = vscode.workspace.getConfiguration('python').get('defaultInterpreterPath') || 'python';
    const validatorPath = path.join(workspacePath, 'app', 'utils', 'template_validator.py');
    
    // Create a temporary file for the validator to process the current document
    const tempFilePath = path.join(workspacePath, '.temp_validator_file.html');
    vscode.workspace.fs.writeFile(vscode.Uri.file(tempFilePath), Buffer.from(document.getText()));

    // Run the validator on the temp file
    const validatorProcess = spawn(pythonPath, [validatorPath, tempFilePath]);
    
    let outputData = '';
    let errorData = '';
    
    validatorProcess.stdout.on('data', (data) => {
        outputData += data.toString();
    });
    
    validatorProcess.stderr.on('data', (data) => {
        errorData += data.toString();
    });
    
    validatorProcess.on('close', (code) => {
        // Clean up temp file
        vscode.workspace.fs.delete(vscode.Uri.file(tempFilePath)).then(() => {
            if (code !== 0 && errorData) {
                vscode.window.showErrorMessage(`Template validator error: ${errorData}`);
                return;
            }
            
            // Parse validator output and create diagnostics
            const diagnostics = parseValidatorOutput(outputData, document);
            diagnosticCollection.set(document.uri, diagnostics);
        });
    });
}

/**
 * Parse validator output into VSCode diagnostics
 * @param {string} output 
 * @param {vscode.TextDocument} document 
 * @returns {vscode.Diagnostic[]}
 */
function parseValidatorOutput(output, document) {
    const diagnostics = [];
    const lines = output.split('\n');
    
    // Sample output format:
    // Issues in app/templates/main/index.html:
    //   - Unquoted variable in onclick: completeTask({{ task.id }})
    //     Fix: Add quotes around the template variable
    
    let currentIssue = null;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (line.startsWith('- ')) {
            const issueMatch = line.match(/^- (.+?)(?:: (.+))?$/);
            if (issueMatch) {
                currentIssue = {
                    type: issueMatch[1],
                    content: issueMatch[2] || ''
                };
            }
        } else if (line.startsWith('Fix: ') && currentIssue) {
            const fix = line.replace('Fix: ', '').trim();
            
            // Find the issue in the document content
            const documentText = document.getText();
            let position;
            
            if (currentIssue.content) {
                // Try to find the issue content in the document
                const contentIndex = documentText.indexOf(currentIssue.content);
                if (contentIndex >= 0) {
                    position = document.positionAt(contentIndex);
                }
            }
            
            // If we couldn't find the position, use the first line
            if (!position) {
                position = new vscode.Position(0, 0);
            }
            
            // Create a range spanning the content or just the current line
            let range;
            if (currentIssue.content && documentText.indexOf(currentIssue.content) >= 0) {
                const startPos = document.positionAt(documentText.indexOf(currentIssue.content));
                const endPos = document.positionAt(documentText.indexOf(currentIssue.content) + currentIssue.content.length);
                range = new vscode.Range(startPos, endPos);
            } else {
                const line = document.lineAt(position.line);
                range = line.range;
            }
            
            // Create diagnostic
            const diagnostic = new vscode.Diagnostic(
                range,
                `${currentIssue.type}${currentIssue.content ? ': ' + currentIssue.content : ''}`,
                vscode.DiagnosticSeverity.Warning
            );
            
            diagnostic.source = 'Timetable Template Validator';
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(document.uri, range),
                    `Fix: ${fix}`
                )
            ];
            
            diagnostics.push(diagnostic);
            currentIssue = null;
        }
    }
    
    return diagnostics;
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
