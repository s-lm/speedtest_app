document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    // Find the icon span inside the button, or create one
    let iconSpan = themeToggle.querySelector('.theme-icon');
    if (!iconSpan) {
        iconSpan = document.createElement('span');
        iconSpan.className = 'theme-icon';
        themeToggle.insertBefore(iconSpan, themeToggle.firstChild);
    }

    function updateThemeIcon(isDark) {
        iconSpan.textContent = isDark ? '☀️' : '🌙';
    }

    // Initial state
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    if (theme === 'dark') document.body.classList.add('dark');
    updateThemeIcon(theme === 'dark');

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark');
        const isDark = document.body.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateThemeIcon(isDark);
        if (typeof applyChartTheme === 'function') applyChartTheme(isDark);
    });
});