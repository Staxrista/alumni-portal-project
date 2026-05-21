document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.querySelector("[data-nav-toggle]");
  const navMenu = document.querySelector("[data-nav-menu]");
  if (navToggle && navMenu) {
    navToggle.addEventListener("click", () => navMenu.classList.toggle("open"));
  }

  const search = document.querySelector("[data-directory-search]");
  const grid = document.querySelector("[data-directory-grid]");
  if (search && grid) {
    search.addEventListener("input", () => {
      const value = search.value.trim().toLowerCase();
      grid.querySelectorAll("[data-profile-card]").forEach((card) => {
        card.style.display = card.textContent.toLowerCase().includes(value) ? "" : "none";
      });
    });
  }
});
