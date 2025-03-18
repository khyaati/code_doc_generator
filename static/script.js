document.addEventListener("DOMContentLoaded", function () {
    // File Upload Handling
    document.getElementById("fileInput").addEventListener("change", handleFileUpload);

    // Drag and Drop Handling
    let dropZone = document.querySelector(".dropzone");
    dropZone.addEventListener("drop", dropHandler);
    dropZone.addEventListener("dragover", dragOverHandler);
});

// Handle File Upload
function handleFileUpload(event) {
    let file = event.target.files[0];
    if (!file) return;

    let reader = new FileReader();
    reader.onload = function (e) {
        document.getElementById("codeInput").value = e.target.result;
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
        document.getElementById("codeInput").value = e.target.result;
    };
    reader.readAsText(file);
}

// Process Code
function processCode() {
    let code = document.getElementById("codeInput").value.trim();
    if (!code) {
        alert("Please enter some code!");
        return;
    }

    let progressBar = document.getElementById("progressBar");
    progressBar.style.width = "50%";
    progressBar.innerText = "Processing...";

    fetch("/upload", {
        method: "POST",
        body: JSON.stringify({ code: code, comment_style: "brief" }),
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
