/**
 * AI Engineering Lab - Main Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initSidebar();
  initSearchModal();
  initCopyButtons();
  initMermaid();
});

// --- Theme Management ---
function initTheme() {
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  if (!themeToggleBtn) return;

  themeToggleBtn.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-bs-theme") || "dark";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    
    document.documentElement.setAttribute("data-bs-theme", newTheme);
    localStorage.setItem("ai_lab_theme", newTheme);
    updateThemeIcon(newTheme);

    // Persist to server
    fetch("/api/theme", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme: newTheme })
    }).catch(err => console.debug("Could not persist theme preference:", err));
  });

  const saved = localStorage.getItem("ai_lab_theme");
  if (saved) {
    document.documentElement.setAttribute("data-bs-theme", saved);
    updateThemeIcon(saved);
  }
}

function updateThemeIcon(theme) {
  const icon = document.getElementById("themeIcon");
  if (!icon) return;
  if (theme === "dark") {
    icon.className = "bi bi-moon-stars-fill text-warning";
  } else {
    icon.className = "bi bi-sun-fill text-warning";
  }
}

// --- Sidebar Management ---
function initSidebar() {
  const toggleBtn = document.getElementById("sidebarToggleBtn");
  const sidebar = document.getElementById("appSidebar");
  if (!toggleBtn || !sidebar) return;

  toggleBtn.addEventListener("click", () => {
    if (window.innerWidth <= 992) {
      sidebar.classList.toggle("show");
    } else {
      sidebar.classList.toggle("collapsed");
    }
  });

  // Close sidebar on mobile when clicking outside
  document.addEventListener("click", (e) => {
    if (window.innerWidth <= 992 && sidebar.classList.contains("show")) {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove("show");
      }
    }
  });
}

// --- Global Search (Ctrl + K) ---
function initSearchModal() {
  const searchInput = document.getElementById("globalSearchInput");
  const searchResults = document.getElementById("globalSearchResults");
  const searchModalEl = document.getElementById("searchModal");

  // Keyboard shortcut Ctrl+K / Cmd+K
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (searchModalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(searchModalEl);
        modal.show();
      }
    }
  });

  if (searchModalEl) {
    searchModalEl.addEventListener("shown.bs.modal", () => {
      if (searchInput) searchInput.focus();
    });
  }

  if (searchInput && searchResults) {
    let debounceTimer = null;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      const query = searchInput.value.trim();
      if (!query) {
        searchResults.innerHTML = '<div class="text-muted p-3 text-center">Type a keyword to search lessons and projects...</div>';
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`/search?q=${encodeURIComponent(query)}&format=json`, {
          headers: { "X-Requested-With": "XMLHttpRequest" }
        })
          .then(r => r.json())
          .then(data => {
            let html = "";
            if (data.lessons && data.lessons.length > 0) {
              html += '<h6 class="text-uppercase text-muted px-3 mt-2 font-monospace" style="font-size:0.75rem;">Lessons</h6>';
              data.lessons.forEach(l => {
                html += `
                  <a href="${l.url}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                    <div>
                      <div class="fw-bold">${escapeHtml(l.title)}</div>
                      <small class="text-muted">${escapeHtml(l.summary)}</small>
                    </div>
                    <span class="badge bg-primary rounded-pill">${escapeHtml(l.module)}</span>
                  </a>
                `;
              });
            }

            if (data.projects && data.projects.length > 0) {
              html += '<h6 class="text-uppercase text-muted px-3 mt-3 font-monospace" style="font-size:0.75rem;">Capstone Projects</h6>';
              data.projects.forEach(p => {
                html += `
                  <a href="${p.url}" class="list-group-item list-group-item-action">
                    <div class="fw-bold text-info">${escapeHtml(p.title)}</div>
                    <small class="text-muted">${escapeHtml(p.description)}</small>
                  </a>
                `;
              });
            }

            if (!data.lessons.length && !data.projects.length) {
              html = '<div class="text-muted p-3 text-center">No results found for "' + escapeHtml(query) + '"</div>';
            }

            searchResults.innerHTML = html;
          })
          .catch(err => {
            searchResults.innerHTML = '<div class="text-danger p-3 text-center">Error fetching search results.</div>';
          });
      }, 250);
    });
  }
}

// --- Copy Code Functionality ---
function initCopyButtons() {
  document.querySelectorAll(".copy-code-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const codeTargetId = btn.getAttribute("data-target");
      const codeEl = document.getElementById(codeTargetId);
      if (!codeEl) return;

      navigator.clipboard.writeText(codeEl.innerText)
        .then(() => {
          const origHtml = btn.innerHTML;
          btn.innerHTML = '<i class="bi bi-check2"></i> Copied!';
          btn.classList.add("btn-success");
          setTimeout(() => {
            btn.innerHTML = origHtml;
            btn.classList.remove("btn-success");
          }, 2000);
        })
        .catch(err => showToast("Failed to copy code to clipboard.", "danger"));
    });
  });
}

// --- Mermaid Diagram Initialization ---
function initMermaid() {
  if (typeof mermaid !== "undefined") {
    const isDark = document.documentElement.getAttribute("data-bs-theme") !== "light";
    mermaid.initialize({
      startOnLoad: true,
      theme: isDark ? "dark" : "default",
      securityLevel: "loose",
      fontFamily: "Inter, sans-serif"
    });
  }
}

// --- Global Toast Notification Helper ---
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toastId = "toast_" + Date.now();
  const bgClass = type === "danger" ? "bg-danger text-white" :
                  type === "success" ? "bg-success text-white" :
                  type === "warning" ? "bg-warning text-dark" : "bg-primary text-white";

  const toastHtml = `
    <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi ${type === 'danger' ? 'bi-exclamation-octagon' : type === 'success' ? 'bi-check-circle' : 'bi-info-circle'}"></i>
          <span>${escapeHtml(message)}</span>
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
  `;

  container.insertAdjacentHTML("beforeend", toastHtml);
  const toastEl = document.getElementById(toastId);
  const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
  bsToast.show();
  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
