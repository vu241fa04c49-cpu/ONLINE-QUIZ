document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("loaded");

  const savedTheme = localStorage.getItem("quizforge-theme");
  if (savedTheme) document.documentElement.dataset.theme = savedTheme;

  const themeButton = document.querySelector("[data-theme-toggle]");
  const syncThemeIcon = () => {
    if (!themeButton) return;
    themeButton.innerHTML =
      document.documentElement.dataset.theme === "dark"
        ? '<i class="fa-solid fa-sun"></i>'
        : '<i class="fa-solid fa-moon"></i>';
  };
  syncThemeIcon();
  themeButton?.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("quizforge-theme", next);
    syncThemeIcon();
  });

  const backToTop = document.querySelector("[data-back-to-top]");
  const toggleBackToTop = () => backToTop?.classList.toggle("visible", window.scrollY > 500);
  toggleBackToTop();
  window.addEventListener("scroll", toggleBackToTop, { passive: true });
  backToTop?.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = button.parentElement?.querySelector("input");
      if (!input) return;
      input.type = input.type === "password" ? "text" : "password";
      button.innerHTML =
        input.type === "password"
          ? '<i class="fa-regular fa-eye"></i>'
          : '<i class="fa-regular fa-eye-slash"></i>';
    });
  });

  document.querySelectorAll("[data-strength-input]").forEach((input) => {
    input.addEventListener("input", () => {
      let score = 0;
      const value = input.value;
      if (value.length >= 8) score += 1;
      if (/[A-Z]/.test(value)) score += 1;
      if (/[0-9]/.test(value)) score += 1;
      if (/[^A-Za-z0-9]/.test(value)) score += 1;
      const bar = input.closest("form")?.querySelector(".strength span");
      if (!bar) return;
      bar.style.width = [20, 40, 65, 85, 100][score] + "%";
      bar.style.background = ["#ef4444", "#f97316", "#f59e0b", "#22c55e", "#14b8a6"][score];
    });
  });

  document.querySelectorAll("[data-validate-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });

  const otpInput = document.querySelector("[data-otp-group] input");
  otpInput?.addEventListener("input", () => {
    otpInput.value = otpInput.value.replace(/\D/g, "").slice(0, 5);
  });

  const revealVisible = () => {
    document.querySelectorAll(".reveal").forEach((element) => {
      if (element.getBoundingClientRect().top < window.innerHeight - 60) {
        element.classList.add("visible");
      }
    });
  };
  revealVisible();
  window.addEventListener("scroll", revealVisible, { passive: true });

  const search = document.querySelector("[data-quiz-search]");
  const filter = document.querySelector("[data-quiz-filter]");
  const applyQuizFilters = () => {
    const query = (search?.value || "").toLowerCase();
    const category = filter?.value || "all";
    document.querySelectorAll(".quiz-item").forEach((item) => {
      const matchesText = item.textContent.toLowerCase().includes(query);
      const matchesCategory = category === "all" || item.dataset.category === category;
      item.style.display = matchesText && matchesCategory ? "" : "none";
    });
  };
  search?.addEventListener("input", applyQuizFilters);
  filter?.addEventListener("change", applyQuizFilters);

  const attempt = document.querySelector("[data-quiz-attempt]");
  if (attempt) {
    const questions = [
      { text: "Which Python data type is immutable?", options: ["Tuple", "List", "Dictionary", "Set"] },
      { text: "Which Django file maps URL patterns to views?", options: ["urls.py", "models.py", "admin.py", "asgi.py"] },
      { text: "Which Bootstrap class creates a responsive row?", options: [".row", ".stack", ".columns", ".layout"] },
      { text: "What does CSRF protection defend against?", options: ["Forged requests", "Slow queries", "Broken images", "CSS errors"] },
      { text: "Which HTML element is best for page navigation?", options: ["nav", "section", "aside", "article"] },
    ];
    let index = 0;
    let remaining = Number(attempt.dataset.duration || 900);
    const current = document.querySelector("[data-current-question]");
    const progress = document.querySelector("[data-quiz-progress]");
    const text = document.querySelector("[data-question-text]");
    const panel = document.querySelector("[data-question-panel]");
    const timer = document.querySelector("[data-timer]");
    const palette = Array.from(document.querySelectorAll("[data-question-palette] button"));

    const renderQuestion = () => {
      const question = questions[index];
      if (current) current.textContent = String(index + 1);
      if (progress) progress.style.width = `${((index + 1) / questions.length) * 100}%`;
      if (text) text.textContent = question.text;
      panel?.querySelectorAll(".quiz-option").forEach((label, optionIndex) => {
        const input = label.querySelector("input");
        if (input) input.checked = false;
        label.lastChild.textContent = ` ${question.options[optionIndex]}`;
      });
      palette.forEach((button, buttonIndex) => button.classList.toggle("active", buttonIndex === index));
    };

    const renderTimer = () => {
      const minutes = String(Math.floor(remaining / 60)).padStart(2, "0");
      const seconds = String(remaining % 60).padStart(2, "0");
      if (timer) timer.innerHTML = `<i class="fa-regular fa-clock"></i> ${minutes}:${seconds}`;
      if (remaining > 0) remaining -= 1;
    };

    document.querySelector("[data-next-question]")?.addEventListener("click", () => {
      index = Math.min(questions.length - 1, index + 1);
      renderQuestion();
    });
    document.querySelector("[data-prev-question]")?.addEventListener("click", () => {
      index = Math.max(0, index - 1);
      renderQuestion();
    });
    document.querySelector("[data-flag-question]")?.addEventListener("click", () => {
      palette[index]?.classList.toggle("flagged");
    });
    palette.forEach((button, buttonIndex) => {
      button.addEventListener("click", () => {
        index = buttonIndex;
        renderQuestion();
      });
    });
    document.querySelector("[data-start-quiz]")?.addEventListener("click", () => {
      attempt.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    renderQuestion();
    renderTimer();
    setInterval(renderTimer, 1000);
  }

  const chartElement = document.getElementById("resultChart");
  if (chartElement && window.Chart) {
    const score = Number(chartElement.dataset.score || 0);
    new Chart(chartElement, {
      type: "doughnut",
      data: {
        labels: ["Score", "Remaining"],
        datasets: [{ data: [score, Math.max(0, 100 - score)], backgroundColor: ["#3157e7", "#e7eaf0"], borderWidth: 0 }],
      },
      options: { cutout: "72%", plugins: { legend: { display: false }, tooltip: { enabled: true } } },
    });
  }
});
