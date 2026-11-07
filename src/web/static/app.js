let currentAnswerText = "";
let currentLang = "en";

function switchTab(tab) {
  const askSection = document.getElementById("ask-section");
  const checkSection = document.getElementById("check-section");
  const askBtn = document.getElementById("tab-ask-btn");
  const checkBtn = document.getElementById("tab-check-btn");

  if (tab === "ask") {
    askSection.style.display = "block";
    checkSection.style.display = "none";
    askBtn.classList.add("active");
    checkBtn.classList.remove("active");
  } else {
    askSection.style.display = "none";
    checkSection.style.display = "block";
    askBtn.classList.remove("active");
    checkBtn.classList.add("active");
  }
}

async function handleAsk(e) {
  e.preventDefault();
  const query = document.getElementById("query-input").value.trim();
  const lang = document.getElementById("lang-select").value;
  const resultBox = document.getElementById("ask-result");
  const answerBody = document.getElementById("answer-body");
  const answerPlainBody = document.getElementById("answer-plain-body");
  const citationsList = document.getElementById("citations-list");
  const submitBtn = document.getElementById("ask-submit-btn");

  if (!query) return;

  submitBtn.disabled = true;
  submitBtn.innerText = "Retrieving official texts...";

  try {
    const res = await fetch("/api/v1/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, language: lang })
    });
    const data = await res.json();

    currentAnswerText = data.answer_text;
    currentLang = data.language;

    answerBody.innerText = data.answer_text;
    answerPlainBody.innerText = data.answer_plain ? `Plain Summary: ${data.answer_plain}` : "";

    citationsList.innerHTML = "";
    if (data.citations && data.citations.length > 0) {
      data.citations.forEach(c => {
        const div = document.createElement("div");
        div.className = "citation-card";
        div.innerHTML = `
          <strong>${c.document_title}</strong> (Section ${c.section}${c.subsection ? ', Subsection ' + c.subsection : ''})<br>
          <small>Source: <a href="${c.source_url}" target="_blank" rel="noopener">${c.source_url}</a> | Version: ${c.version} | Status: <strong>${c.legal_status}</strong></small>
        `;
        citationsList.appendChild(div);
      });
    } else {
      citationsList.innerHTML = "<small>No legal citation attached (Refusal or Abstention).</small>";
    }

    resultBox.style.display = "block";
  } catch (err) {
    alert("Connection error: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "Get Verified Answer";
  }
}

function togglePlainView() {
  const isChecked = document.getElementById("plain-toggle").checked;
  const plainBody = document.getElementById("answer-plain-body");
  plainBody.style.display = isChecked ? "block" : "none";
}

function playAudio() {
  if (!currentAnswerText) return;
  const url = `/api/v1/tts?lang=${encodeURIComponent(currentLang)}&text=${encodeURIComponent(currentAnswerText.slice(0, 200))}`;
  const audio = new Audio(url);
  audio.play().catch(e => console.error("Audio playback error:", e));
}

async function handleCheck(e) {
  e.preventDefault();
  const input = document.getElementById("check-input").value.trim();
  const submitBtn = document.getElementById("check-submit-btn");
  const resultBox = document.getElementById("check-result");
  const badge = document.getElementById("check-status-badge");
  const notes = document.getElementById("check-notes");
  const source = document.getElementById("check-matched-source");
  const disclaimer = document.getElementById("check-disclaimer");

  if (!input) return;

  submitBtn.disabled = true;
  submitBtn.innerText = "Checking authentic records...";

  try {
    const res = await fetch("/api/v1/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item: input })
    });
    const data = await res.json();

    badge.innerText = data.status;
    badge.className = "status-badge";
    if (data.status === "Matches an official source") {
      badge.classList.add("matches");
    } else if (data.status === "Does not match any official source I can check") {
      badge.classList.add("nomatch");
    } else {
      badge.classList.add("canttell");
    }

    notes.innerText = data.confidence_notes || "";
    source.innerHTML = data.matched_source ? `<strong>Source:</strong> ${data.matched_source}` : "";
    disclaimer.innerText = data.disclaimer;

    resultBox.style.display = "block";
  } catch (err) {
    alert("Check error: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "Verify Authenticity";
  }
}
