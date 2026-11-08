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

function handleLangChange() {
  const lang = document.getElementById("lang-select").value;
  const optinGroup = document.getElementById("optin-translation-group");
  if (lang !== "en") {
    optinGroup.style.display = "block";
  } else {
    optinGroup.style.display = "none";
  }
}

async function handleAsk(e) {
  e.preventDefault();
  const query = document.getElementById("query-input").value.trim();
  const lang = document.getElementById("lang-select").value;
  const allowTranslation = document.getElementById("translate-optin") ? document.getElementById("translate-optin").checked : false;
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
      body: JSON.stringify({ query, language: lang, allow_translation: allowTranslation })
    });
    const data = await res.json();
    renderAnswer(data);
  } catch (err) {
    alert("Connection error: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "Get Verified Answer";
  }
}

function renderAnswer(data) {
  const resultBox = document.getElementById("ask-result");
  const answerBody = document.getElementById("answer-body");
  const answerPlainBody = document.getElementById("answer-plain-body");
  const citationsList = document.getElementById("citations-list");
  const flagsContainer = document.getElementById("confidence-flags-container");

  currentAnswerText = data.answer_text;
  currentLang = data.language;

  if (data.status === "NEEDS_LANGUAGE_CONFIRMATION") {
    answerBody.innerHTML = `
      <div style="background:#fff3cd; color:#856404; padding:14px; border-radius:6px; border:1px solid #ffeeba;">
        <strong>⚠️ Language Confirmation Required</strong>
        <p style="margin:8px 0 12px 0;">The system detected potential candidate language <em>${data.detected_candidate || 'unknown'}</em> (Confidence: ${data.confidence_score ? (data.confidence_score * 100).toFixed(1) + '%' : 'Uncertain'}). Under our nonpartisan civic safety policy, we do not guess silently.</p>
        <p style="font-weight:600; margin-bottom:8px;">Please click your language to receive a verified statutory answer:</p>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <button type="button" class="btn btn-secondary" onclick="confirmLangAndSubmit('en')">1. English</button>
          <button type="button" class="btn btn-secondary" onclick="confirmLangAndSubmit('ha')">2. Hausa (Harshen Hausa)</button>
          <button type="button" class="btn btn-secondary" onclick="confirmLangAndSubmit('yo')">3. Yoruba (Èdè Yorùbá)</button>
          <button type="button" class="btn btn-secondary" onclick="confirmLangAndSubmit('ig')">4. Igbo (Asụsụ Igbo)</button>
          <button type="button" class="btn btn-secondary" onclick="confirmLangAndSubmit('pcm')">5. Pidgin (Naijá)</button>
        </div>
      </div>
    `;
    answerPlainBody.style.display = "none";
    citationsList.innerHTML = "<small>Statutory citations will appear once your language is confirmed.</small>";
    if (flagsContainer) flagsContainer.innerHTML = "";
    resultBox.style.display = "block";
    return;
  }

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

  if (flagsContainer && data.confidence_flags) {
    flagsContainer.innerHTML = data.confidence_flags.map(f => `<span class="flag-badge" style="display:inline-block; margin:2px 4px; padding:2px 6px; font-size:0.75rem; background:#e2e3e5; color:#383d41; border-radius:4px;">${f}</span>`).join(" ");
  }

  resultBox.style.display = "block";
}

function confirmLangAndSubmit(chosenLang) {
  document.getElementById("lang-select").value = chosenLang;
  handleLangChange();
  const query = document.getElementById("query-input").value.trim();
  const allowTranslation = document.getElementById("translate-optin") ? document.getElementById("translate-optin").checked : false;

  fetch("/api/v1/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, language: chosenLang, allow_translation: allowTranslation, confirmed_language: true })
  })
  .then(res => res.json())
  .then(data => renderAnswer(data))
  .catch(err => alert("Error: " + err.message));
}
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

