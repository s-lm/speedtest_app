document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    // Ensure the icon span exists
    let iconSpan = themeToggle.querySelector('.theme-icon');
    if (!iconSpan) {
        iconSpan = document.createElement('span');
        iconSpan.className = 'theme-icon';
        themeToggle.insertBefore(iconSpan, themeToggle.firstChild);
    }

    // No need to set iconSpan.textContent; CSS mask handles the icon

    // Initial state
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    if (theme === 'dark') document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');

    themeToggle.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        const isDark = document.documentElement.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        if (typeof applyChartTheme === 'function') applyChartTheme(isDark);
    });
});