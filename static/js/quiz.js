document.addEventListener("DOMContentLoaded", () => {
  const attempt = document.querySelector("[data-quiz-attempt]");
  if (attempt) {
    const questions = [
      { text: "Which Python data type is immutable?", options: ["Tuple", "List", "Dictionary", "Set"] },
      { text: "Which file maps Django URL patterns to views?", options: ["urls.py", "models.py", "admin.py", "settings.py"] },
      { text: "Which Bootstrap class creates a row?", options: [".row", ".grid-row", ".columns", ".stack"] },
      { text: "What does CSRF protection help prevent?", options: ["Forged requests", "Broken CSS", "Slow queries", "Missing images"] },
      { text: "Which HTML element represents navigation?", options: ["nav", "article", "figure", "aside"] },
    ];
    let index = 0;
    let remaining = Number(attempt.dataset.duration || 900);
    const current = document.querySelector("[data-current-question]");
    const progress = document.querySelector("[data-quiz-progress]");
    const text = document.querySelector("[data-question-text]");
    const options = Array.from(document.querySelectorAll("[data-question-panel] .quiz-option"));
    const timer = document.querySelector("[data-timer]");
    const palette = Array.from(document.querySelectorAll("[data-question-palette] button"));
    const antiCheat = document.querySelector("[data-anti-cheat]");
    const suspiciousCount = document.querySelector("[data-suspicious-count]");
    const suspiciousList = document.querySelector("[data-suspicious-events]");
    const submitQuiz = document.querySelector("[data-submit-quiz]");
    const maxWarnings = 3;
    const suspiciousState = { count: 0, events: [], lastEventAt: 0, locked: false };
    const storageKey = `quizforge-anti-cheat-${antiCheat?.dataset.quizId || "attempt"}`;

    localStorage.removeItem(storageKey);

    const renderSuspiciousActivity = () => {
      if (suspiciousCount) suspiciousCount.textContent = String(suspiciousState.count);
      if (!suspiciousList) return;
      if (!suspiciousState.events.length) {
        suspiciousList.innerHTML = "<li>No suspicious activity detected.</li>";
        return;
      }
      suspiciousList.innerHTML = suspiciousState.events
        .slice(-6)
        .map((event) => `<li>${event}</li>`)
        .join("");
    };

    const resultUrlWithReport = () => {
      const baseUrl = submitQuiz?.href || "/result/";
      const events = suspiciousState.events.slice(-8).map(encodeURIComponent).join("|");
      const separator = baseUrl.includes("?") ? "&" : "?";
      const locked = suspiciousState.locked ? "&exam_locked=1" : "";
      return `${baseUrl}${separator}suspicious_count=${suspiciousState.count}&suspicious_events=${events}${locked}`;
    };

    const showExamWarning = (message, finalWarning = false) => {
      let modal = document.getElementById("antiCheatWarningModal");
      if (!modal) {
        document.body.insertAdjacentHTML("beforeend", `
          <div class="modal fade" id="antiCheatWarningModal" tabindex="-1" aria-labelledby="antiCheatWarningTitle" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
              <div class="modal-content anti-cheat-modal">
                <div class="modal-header">
                  <h2 class="modal-title fs-5" id="antiCheatWarningTitle"><i class="fa-solid fa-triangle-exclamation me-2" aria-hidden="true"></i>Exam warning</h2>
                  <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                  <p data-anti-cheat-warning-text></p>
                  <p class="mb-0"><strong data-anti-cheat-warning-count></strong></p>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Continue exam</button>
                </div>
              </div>
            </div>
          </div>
        `);
        modal = document.getElementById("antiCheatWarningModal");
      }
      modal.querySelector("[data-anti-cheat-warning-text]").textContent = message;
      modal.querySelector("[data-anti-cheat-warning-count]").textContent = finalWarning
        ? "Limit reached. The exam will now close."
        : `Warning ${suspiciousState.count} of ${maxWarnings}. After 3 warnings, the exam closes automatically.`;
      if (window.bootstrap) new bootstrap.Modal(modal).show();
      else window.alert(`${message}\nWarning ${suspiciousState.count} of ${maxWarnings}.`);
    };

    const lockExam = () => {
      if (suspiciousState.locked) return;
      suspiciousState.locked = true;
      localStorage.setItem(storageKey, JSON.stringify(suspiciousState));
      document.querySelectorAll("[data-quiz-attempt] button, [data-quiz-attempt] input").forEach((element) => {
        element.disabled = true;
      });
      showExamWarning("You switched away from the exam too many times.", true);
      window.setTimeout(() => {
        window.location.href = resultUrlWithReport();
      }, 1800);
    };

    const recordSuspiciousActivity = (reason) => {
      if (suspiciousState.locked) return;
      const now = Date.now();
      if (now - suspiciousState.lastEventAt < 900) return;
      suspiciousState.lastEventAt = now;
      suspiciousState.count += 1;
      const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      suspiciousState.events.push(`${reason} at ${time}`);
      localStorage.setItem(storageKey, JSON.stringify(suspiciousState));
      renderSuspiciousActivity();
      antiCheat?.classList.add("anti-cheat-warning");
      window.setTimeout(() => antiCheat?.classList.remove("anti-cheat-warning"), 900);
      if (suspiciousState.count >= maxWarnings) {
        lockExam();
        return;
      }
      showExamWarning(`${reason}. Please stay on the exam screen.`);
    };

    const renderQuestion = () => {
      const question = questions[index];
      if (current) current.textContent = String(index + 1);
      if (progress) progress.style.width = `${((index + 1) / questions.length) * 100}%`;
      if (text) text.textContent = question.text;
      options.forEach((label, optionIndex) => {
        const input = label.querySelector("input");
        if (input) input.checked = false;
        const optionText = question.options[optionIndex] || "";
        label.childNodes[label.childNodes.length - 1].textContent = ` ${optionText}`;
      });
      palette.forEach((button, buttonIndex) => button.classList.toggle("active", buttonIndex === index));
    };

    const renderTimer = () => {
      const minutes = String(Math.floor(remaining / 60)).padStart(2, "0");
      const seconds = String(remaining % 60).padStart(2, "0");
      if (timer) timer.innerHTML = `<i class="fa-regular fa-clock" aria-hidden="true"></i> ${minutes}:${seconds}`;
      if (remaining > 0) remaining -= 1;
    };

    document.querySelector("[data-next-question]")?.addEventListener("click", () => { index = Math.min(questions.length - 1, index + 1); renderQuestion(); });
    document.querySelector("[data-prev-question]")?.addEventListener("click", () => { index = Math.max(0, index - 1); renderQuestion(); });
    document.querySelector("[data-flag-question]")?.addEventListener("click", () => palette[index]?.classList.toggle("flagged"));
    palette.forEach((button, buttonIndex) => button.addEventListener("click", () => { index = buttonIndex; renderQuestion(); }));
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) recordSuspiciousActivity("Tab switched or browser hidden");
    });
    window.addEventListener("blur", () => recordSuspiciousActivity("Exam window lost focus"));
    submitQuiz?.addEventListener("click", () => {
      submitQuiz.href = resultUrlWithReport();
    });
    renderQuestion();
    renderSuspiciousActivity();
    renderTimer();
    setInterval(renderTimer, 1000);
  }

  const chart = document.getElementById("resultChart");
  if (chart && window.Chart) {
    const score = Number(chart.dataset.score || 0);
    new Chart(chart, {
      type: "doughnut",
      data: { labels: ["Score", "Remaining"], datasets: [{ data: [score, Math.max(0, 100 - score)], backgroundColor: ["#4F46E5", "#EEF2FF"], borderWidth: 0 }] },
      options: { cutout: "72%", plugins: { legend: { display: false } } },
    });
  }
});
