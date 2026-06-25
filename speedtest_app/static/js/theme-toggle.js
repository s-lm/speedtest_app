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

    // Make the user dropdown work on touch devices (hover is unreliable there)
    const dropdown = document.querySelector('.toolbar-dropdown');
    const dropBtn = dropdown && dropdown.querySelector('.toolbar-dropbtn');
    if (dropdown && dropBtn) {
        dropBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const open = dropdown.classList.toggle('open');
            dropBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target)) {
                dropdown.classList.remove('open');
                dropBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }
});