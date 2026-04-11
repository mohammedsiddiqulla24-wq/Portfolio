const toggleBtn = document.getElementById("themeToggle");

const currentTheme = localStorage.getItem("theme");

if (currentTheme) {
    document.body.setAttribute("data-theme", currentTheme);
    toggleBtn.textContent = currentTheme === "dark" ? "🌙" : "☀";
}

toggleBtn.addEventListener("click", () => {
    let theme = document.body.getAttribute("data-theme");

    if (theme === "dark") {
        document.body.setAttribute("data-theme", "light");
        localStorage.setItem("theme", "light");
        toggleBtn.textContent = "☀";
    } else {
        document.body.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
        toggleBtn.textContent = "🌙";
    }
});