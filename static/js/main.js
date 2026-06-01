document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("loaded");

  const savedTheme = localStorage.getItem("quizforge-theme");
  if (savedTheme) document.documentElement.dataset.theme = savedTheme;
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const syncThemeIcon = () => {
    if (!themeToggle) return;
    themeToggle.innerHTML = document.documentElement.dataset.theme === "dark"
      ? '<i class="fa-solid fa-sun" aria-hidden="true"></i>'
      : '<i class="fa-solid fa-moon" aria-hidden="true"></i>';
  };
  syncThemeIcon();
  themeToggle?.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem("quizforge-theme", nextTheme);
    syncThemeIcon();
  });

  const backToTop = document.querySelector("[data-back-to-top]");
  const toggleBackToTop = () => backToTop?.classList.toggle("visible", window.scrollY > 480);
  toggleBackToTop();
  window.addEventListener("scroll", toggleBackToTop, { passive: true });
  backToTop?.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  const showToast = (message, tone = "primary") => {
    const toastArea = document.querySelector("[data-toast-area]");
    if (!toastArea || !window.bootstrap) return;
    toastArea.innerHTML = `<div class="toast align-items-center text-bg-${tone} border-0" role="status"><div class="d-flex"><div class="toast-body">${message}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div></div>`;
    new bootstrap.Toast(toastArea.querySelector(".toast")).show();
  };

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = button.parentElement?.querySelector("input");
      if (!input) return;
      input.type = input.type === "password" ? "text" : "password";
      button.innerHTML = input.type === "password"
        ? '<i class="fa-regular fa-eye" aria-hidden="true"></i>'
        : '<i class="fa-regular fa-eye-slash" aria-hidden="true"></i>';
    });
  });

  document.querySelectorAll("[data-strength-input]").forEach((input) => {
    input.addEventListener("input", () => {
      const value = input.value;
      let score = 0;
      if (value.length >= 8) score += 1;
      if (/[A-Z]/.test(value)) score += 1;
      if (/\d/.test(value)) score += 1;
      if (/[^A-Za-z0-9]/.test(value)) score += 1;
      const bar = input.closest("form")?.querySelector(".strength span");
      if (!bar) return;
      bar.style.width = [18, 40, 62, 82, 100][score] + "%";
      bar.style.background = ["#ef4444", "#f97316", "#f59e0b", "#22c55e", "#16a34a"][score];
    });
  });

  document.querySelectorAll("[data-api-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      if (!form.checkValidity()) return;
      event.preventDefault();
      event.stopImmediatePropagation();

      const button = form.querySelector("[data-loading-button]");
      const originalHtml = button?.innerHTML;
      if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Working...';
      }

      const csrf = form.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
      const data = Object.fromEntries(new FormData(form).entries());
      delete data.csrfmiddlewaretoken;

      try {
        const response = await fetch(form.dataset.apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
          },
          body: JSON.stringify(data),
        });
        const payload = await response.json();
        if (!response.ok || payload.ok === false) {
          throw new Error(payload.detail || "Please check the form and try again.");
        }
        const otpNote = payload.development_otp ? ` Development OTP: ${payload.development_otp}` : "";
        showToast(`${payload.detail || "Saved successfully."}${otpNote}`, "primary");
        if (form.dataset.nextUrl) {
          window.setTimeout(() => {
            window.location.href = form.dataset.nextUrl;
          }, 850);
        }
      } catch (error) {
        showToast(error.message || "Something went wrong.", "danger");
        if (button) {
          button.disabled = false;
          button.innerHTML = originalHtml;
        }
      }
    }, { capture: true });
  });

  document.querySelectorAll("[data-validate-form]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
      const button = form.querySelector("[data-loading-button]");
      if (button && form.checkValidity()) {
        button.disabled = true;
        button.dataset.originalHtml = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Working...';
      }
    });
  });

  document.querySelectorAll("[data-otp-group] input").forEach((input) => {
    input.addEventListener("input", () => {
      input.value = input.value.replace(/\D/g, "").slice(0, 5);
    });
  });

  document.querySelectorAll("[data-file-preview]").forEach((input) => {
    input.addEventListener("change", () => {
      const fileName = input.files?.[0]?.name;
      const label = input.closest(".file-upload-box")?.querySelector("strong");
      if (fileName && label) label.textContent = fileName;
    });
  });

  const reveal = () => {
    document.querySelectorAll(".reveal").forEach((element) => {
      if (element.getBoundingClientRect().top < window.innerHeight - 64) {
        element.classList.add("visible");
      }
    });
  };
  reveal();
  window.addEventListener("scroll", reveal, { passive: true });

  const search = document.querySelector("[data-quiz-search]");
  const filter = document.querySelector("[data-quiz-filter]");
  const applyFilters = () => {
    const query = (search?.value || "").toLowerCase();
    const category = filter?.value || "all";
    document.querySelectorAll(".quiz-item").forEach((item) => {
      const textMatch = item.textContent.toLowerCase().includes(query);
      const categoryMatch = category === "all" || item.dataset.category === category;
      item.hidden = !(textMatch && categoryMatch);
    });
  };
  search?.addEventListener("input", applyFilters);
  filter?.addEventListener("change", applyFilters);

  const newsletter = document.querySelector(".newsletter-form");
  newsletter?.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!newsletter.checkValidity()) return;
    showToast("Thanks for subscribing.", "primary");
    newsletter.reset();
  });
});
