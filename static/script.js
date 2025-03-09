document.addEventListener("DOMContentLoaded", function () {
    const menuButton = document.querySelector(".menu-button");
    const sidePanel = document.querySelector(".side-panel");
  
    menuButton.addEventListener("click", function () {
      sidePanel.classList.toggle("active");
    });
  });
  