document.addEventListener('DOMContentLoaded', () => {
  // Element References
  const pdfInput = document.getElementById('pdf-input');
  const uploadStatus = document.getElementById('upload-status');
  const questionInput = document.getElementById('question');
  const askBtn = document.getElementById('ask-btn');
  const statusEl = document.getElementById('status');
  const answerPanel = document.getElementById('answer');
  const answerText = document.getElementById('answer-text');
  const qtypePill = document.getElementById('qtype-pill');
  const toolPill = document.getElementById('tool-pill');
  const sourcesSection = document.getElementById('sources');
  const sourcesList = document.getElementById('sources-list');

  // Constants
  const QTYPE_BASE = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium';
  const QTYPE_COLORS = {
    definition: 'bg-indigo-100 text-indigo-700',
    example: 'bg-emerald-100 text-emerald-700',
    comparison: 'bg-amber-100 text-amber-700',
  };

  // Helper Function: resetAnswerUI
  function resetAnswerUI() {
    answerPanel.hidden = true;
    qtypePill.hidden = true;
    qtypePill.textContent = '';
    qtypePill.className = QTYPE_BASE;
    toolPill.hidden = true;
    toolPill.textContent = '';
    sourcesSection.hidden = true;
    sourcesList.innerHTML = '';
    answerText.textContent = '';
  }

  // 1. File Input Behavior
  pdfInput.addEventListener('change', () => {
    const file = pdfInput.files[0];
    if (!file) {
      uploadStatus.textContent = '';
      uploadStatus.className = 'text-sm text-gray-500 mt-2 min-h-[1.25rem]';
      return;
    }
    uploadStatus.textContent = `Selected "${file.name}" (ready to upload)`;
    uploadStatus.className = 'text-sm text-green-600 mt-2 min-h-[1.25rem]';
  });

  // 3. Submit Button Behavior
  askBtn.addEventListener('click', () => {
    const question = questionInput.value.trim();

    // Step 1: Validate Input
    if (!question) {
      statusEl.textContent = 'Please type a question first.';
      statusEl.className = 'text-sm text-red-500 mt-2 min-h-[1.25rem]';
      resetAnswerUI();
      return;
    }

    // Step 2: Loading State
    resetAnswerUI();
    statusEl.textContent = 'Thinking...';
    statusEl.className = 'text-sm text-gray-500 mt-2 min-h-[1.25rem]';

    // Step 3: Simulated Delay
    setTimeout(() => {
      const lowerQuestion = question.toLowerCase();

      // Step 4: Determine Placeholder Question Type
      let placeholderType = 'definition';
      if (lowerQuestion.startsWith('what is')) {
        placeholderType = 'definition';
      } else if (lowerQuestion.startsWith('give') || lowerQuestion.includes('example')) {
        placeholderType = 'example';
      } else if (lowerQuestion.includes('vs') || lowerQuestion.includes('versus') || lowerQuestion.includes('compare') || lowerQuestion.includes('difference')) {
        placeholderType = 'comparison';
      }

      // Step 5: Determine Placeholder Tool
      let placeholderTool = 'search_notes';
      // Regex for digits, spaces, and arithmetic symbols: 0-9, space, +, -, *, /, (, ), .
      const calculatorRegex = /^[0-9\s\+\-\*\/\(\)\.]*$/;
      if (calculatorRegex.test(question)) {
        placeholderTool = 'calculator';
      }

      // Step 6: Build Placeholder Answer
      const answerMsg = `Placeholder answer for: "${question}". Real answers will appear here once the backend is connected.`;

      // Step 7: Populate UI
      answerText.textContent = answerMsg;

      qtypePill.hidden = false;
      qtypePill.textContent = `type: ${placeholderType}`;
      qtypePill.className = `${QTYPE_BASE} ${QTYPE_COLORS[placeholderType]}`;

      toolPill.hidden = false;
      toolPill.textContent = `tool: ${placeholderTool}`;

      // Sources List
      const sampleSources = [
        'Sample source chunk 1 — example excerpt from the uploaded notes.',
        'Sample source chunk 2 — another excerpt.',
        'Sample source chunk 3 — final excerpt.',
      ];

      sampleSources.forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        sourcesList.appendChild(li);
      });

      // Calculator Path Rule
      if (placeholderTool === 'calculator') {
        sourcesSection.hidden = true;
      } else {
        sourcesSection.hidden = false;
      }

      // Final Reveal
      answerPanel.hidden = false;
      statusEl.textContent = '';
      statusEl.className = 'text-sm text-gray-500 mt-2 min-h-[1.25rem]';
    }, 600);
  });
});
