document.addEventListener("DOMContentLoaded", () => {
  // Element References
  const pdfInput = document.getElementById("pdf-input");
  const uploadStatus = document.getElementById("upload-status");
  const questionEl = document.getElementById("question");
  const askBtn = document.getElementById("ask-btn");
  const statusEl = document.getElementById("status");
  const answerEl = document.getElementById("answer");
  const answerTextEl = document.getElementById("answer-text");
  const qtypePill = document.getElementById("qtype-pill");
  const toolPill = document.getElementById("tool-pill");
  const sourcesEl = document.getElementById("sources");
  const sourcesListEl = document.getElementById("sources-list");

  const QTYPE_BASE = "px-3 py-1 rounded-full text-xs font-medium ";
  const QTYPE_COLORS = {
    definition: "bg-blue-100 text-blue-700",
    example: "bg-green-100 text-green-700",
    comparison: "bg-purple-100 text-purple-700",
  };

  function resetAnswerUI() {
    answerEl.hidden = true;
    qtypePill.hidden = true;
    toolPill.hidden = true;
    sourcesEl.hidden = true;
    
    answerTextEl.textContent = "";
    qtypePill.textContent = "";
    toolPill.textContent = "";
    
    // Reset pill classes to base
    qtypePill.className = QTYPE_BASE;
    
    sourcesListEl.textContent = "";
  }

  // File Upload Handler
  pdfInput.addEventListener("change", async () => {
    const file = pdfInput.files[0];
    if (!file) {
      uploadStatus.textContent = "";
      return;
    }

    uploadStatus.textContent = `Uploading "${file.name}"...`;
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const data = await response.json();
      uploadStatus.textContent = `Loaded "${data.filename}" — ${data.pages} pages, ${data.chars} characters, ${data.chunks_indexed} chunks indexed.`;
    } catch (error) {
      uploadStatus.textContent = `Upload failed: ${error.message}`;
    }
  });

  // Submit Button Handler
  askBtn.addEventListener("click", async () => {
    const question = questionEl.value.trim();
    
    if (!question) {
      statusEl.textContent = "Please enter a question.";
      statusEl.classList.add("text-red-500");
      resetAnswerUI();
      return;
    }

    statusEl.classList.remove("text-red-500");
    statusEl.textContent = "Thinking...";
    resetAnswerUI();

    try {
      const response = await fetch("/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error("Server error occurred");
      }

      const data = await response.json();
      statusEl.textContent = "";

      // Render Answer
      if (data.tool_used === 'draw_diagram') {
        answerTextEl.textContent = ''; // Clear text
        
        // Remove any previous diagrams
        const prevDiagram = answerEl.querySelector('.mermaid');
        if (prevDiagram) prevDiagram.remove();
        
        // Create Mermaid container
        const mermaidDiv = document.createElement('div');
        mermaidDiv.className = 'mermaid bg-white p-4 rounded border border-gray-200 mt-2 overflow-auto';
        
        // Use a unique ID for mermaid rendering
        const diagramId = 'mermaid-' + Date.now();
        mermaidDiv.id = diagramId;
        mermaidDiv.textContent = data.answer;
        
        answerTextEl.after(mermaidDiv);
        
        // Render diagram
        try {
          // In newer versions of Mermaid, mermaid.run() is used.
          // If that's not working, we try mermaid.render as a fallback.
          await mermaid.run({
            nodes: [mermaidDiv],
          });
        } catch (e) {
          console.error('Mermaid render error:', e);
          answerTextEl.textContent = 'Error rendering diagram: ' + e.message;
        }
      } else {
        // Regular text answer
        const prevDiagram = answerEl.querySelector('.mermaid');
        if (prevDiagram) prevDiagram.remove();
        
        answerTextEl.textContent = data.answer;
      }
      
      // Render Question Type Pill
      qtypePill.textContent = data.question_type;
      qtypePill.className = QTYPE_BASE + (QTYPE_COLORS[data.question_type] || QTYPE_COLORS.definition);
      qtypePill.hidden = false;

      // Render Tool Pill
      toolPill.textContent = data.tool_used;
      toolPill.hidden = false;

      // Render Sources
      if (data.used_chunks && data.used_chunks.length > 0) {
        sourcesListEl.textContent = "";
        data.used_chunks.forEach((chunk) => {
          const li = document.createElement("li");
          li.textContent = typeof chunk === 'string' ? chunk : chunk.text;
          sourcesListEl.appendChild(li);
        });
        sourcesEl.hidden = false;
      } else {
        sourcesEl.hidden = true;
      }

      answerEl.hidden = false;
    } catch (error) {
      statusEl.textContent = `Error: ${error.message}`;
      statusEl.classList.add("text-red-500");
    }
  });
});
