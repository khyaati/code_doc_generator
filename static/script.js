const editorElement = document.getElementById("code-editor");
const outputElement = document.getElementById("output-code");
const submitBtn = document.getElementById("submit-btn");
const progressBar = document.getElementById("progress-bar");
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const languageSelect = document.getElementById("language-select");

let cmEditor;

document.addEventListener("DOMContentLoaded", () => {
  cmEditor = CodeMirror.fromTextArea(editorElement, {
    lineNumbers: true,
    mode: "python",
    theme: "dracula",
    autorefresh: true
  });

  const theme = localStorage.getItem("theme") || "light";
  document.body.className = theme;
});


document.getElementById("theme-toggle").onclick = () => {
  const newTheme = document.body.classList.contains("dark") ? "light" : "dark";
  document.body.className = newTheme;
  localStorage.setItem("theme", newTheme);
};


dropZone.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.style.background = "#f0f0f0";
});
dropZone.addEventListener("dragleave", () => {
  dropZone.style.background = "transparent";
});
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.style.background = "transparent";
  const file = e.dataTransfer.files[0];
  readFile(file);
});

fileInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  readFile(file);
});

function readFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    cmEditor.setValue(reader.result);
  };
  reader.readAsText(file);
}


submitBtn.onclick = async () => {
  const code = cmEditor.getValue();
  const selectedLang = languageSelect.value;

  if (!code || !selectedLang) {
    alert("Please enter code and select a language.");
    return;
  }

  submitBtn.disabled = true;
  progressBar.style.display = "block";
  outputElement.textContent = "Generating comments...";

  try {
    const res = await fetch("/comment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, language: selectedLang })
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    console.log("Raw response JSON:", data);

  
    const rawCode = data["commented code"] || "No comment generated.";
    const cleanCode = rawCode.replace(/^```[a-z]*\n|```$/g, '').trim();


    outputElement.textContent = cleanCode;

  } catch (err) {
    console.error("Fetch error:", err);
    outputElement.textContent = "Failed to fetch response. Check console for details.";
  }

  submitBtn.disabled = false;
  progressBar.style.display = "none";
};


function copyCode() {
  navigator.clipboard.writeText(outputElement.textContent)
    .then(() => alert("Copied to clipboard!"))
    .catch(err => alert("Copy failed: " + err));
}


function downloadCode() {
  const lang = languageSelect.value || "txt";
  const codeContent = outputElement.textContent;

  const extensionMap = {
    'python': 'py',
    'javascript': 'js',
    'java': 'java',
    'c': 'c',
    'cpp': 'cpp',
  };

  const extension = extensionMap[language] || 'txt';
  const blob = new Blob([codeContent], { type: "text/plain" });
  const a = document.createElement("a");
  
  a.href = URL.createObjectURL(blob);
  a.download = `commented_code.${extension}`;
  a.click();
}
