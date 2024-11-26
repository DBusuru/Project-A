document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".section-tab-nav li a").forEach((tab) => {
    tab.addEventListener("click", (e) => {
      e.preventDefault();

      const section = tab.closest(".section");
      const filter = tab.textContent.toLowerCase();

      section.querySelectorAll(".section-tab-nav li").forEach((li) =>
        li.classList.remove("active")
      );
      tab.parentElement.classList.add("active");

      section.querySelectorAll(".product").forEach((product) => {
        const categories = product.dataset.category.toLowerCase().split(",");
        product.style.display =
          filter === "all" || categories.includes(filter) ? "block" : "none";
      });
    });
  });
});
