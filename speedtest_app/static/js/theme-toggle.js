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
    if (theme === 'dark') document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
    updateThemeIcon(theme === 'dark');

    themeToggle.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        const isDark = document.documentElement.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateThemeIcon(isDark);
        if (typeof applyChartTheme === 'function') applyChartTheme(isDark);
    });
});