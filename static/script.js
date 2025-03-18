document.addEventListener("DOMContentLoaded", function () {
    // File Upload Handling
    document.getElementById("fileInput").addEventListener("change", handleFileUpload);

    // Drag and Drop Handling
    let dropZone = document.querySelector(".dropzone");
    dropZone.addEventListener("drop", dropHandler);
    dropZone.addEventListener("dragover", dragOverHandler);

    // Language Change Handling
    document.getElementById("languageSelect").addEventListener("change", function(){
        let language = this.value;
        if (language !== "auto"){
            monaco.editor.setModelLanguage(window.editor.getModel(), language);
        }
    });

    // Monaco Editor Change Listener
    window.editor.onDidChangeModelContent(function() {
        setTimeout(adjustEditorHeight, 50); // Delay the height adjustment
    });

});

// Handle File Upload
function handleFileUpload(event) {
    let file = event.target.files[0];
    if (!file) return;

    let reader = new FileReader();
    reader.onload = function (e) {
        window.editor.setValue(e.target.result); // Set code in Monaco Editor
        setTimeout(adjustEditorHeight, 50); // Delay height adjustment after file upload
    };
    reader.readAsText(file);
}

// Drag and Drop Functions
function dragOverHandler(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
}

function dropHandler(event) {
    event.preventDefault();
    let file = event.dataTransfer.files[0];
    if (!file) return;

    let reader = new FileReader();
    reader.onload = function (e) {
        window.editor.setValue(e.target.result); // Set code in Monaco Editor
        setTimeout(adjustEditorHeight, 50); // Delay height adjustment after file drop
    };
    reader.readAsText(file);
}

// Adjust Editor Height Dynamically
function adjustEditorHeight() {
    let contentHeight = window.editor.getContentHeight();
    document.getElementById("codeInput").style.height = contentHeight + "px";
    window.editor.layout(); // Force Monaco to re-layout
}

// Process Code
function processCode() {
    let code = window.editor.getValue().trim(); // Get code from Monaco Editor
    if (!code) {
        alert("Please enter some code!");
        return;
    }
    let language = document.getElementById("languageSelect").value;
    let progressBar = document.getElementById("progressBar");
    progressBar.style.width = "50%";
    progressBar.innerText = "Processing...";

    fetch("/upload", {
        method: "POST",
        body: JSON.stringify({ code: code, comment_style: "brief", language: language }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        progressBar.style.width = "100%";
        progressBar.innerText = "Done!";
        document.getElementById("outputContainer").style.display = "block";
        document.getElementById("commentedCode").innerText = data.commented_code;

        // Apply Syntax Highlighting with highlight.js
        hljs.highlightAll();
    })
    .catch(err => alert("Error processing code: " + err));
}

// Copy to Clipboard
function copyToClipboard() {
    let text = document.getElementById("commentedCode").innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert("Copied to clipboard!");
    });
}
