/**
 * Menza Theme Management
 * Handles theme initialization and persistence across all pages
 */

(function() {
    // Initialize theme before page renders
    const savedTheme = localStorage.getItem('menza-theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
        // Default to system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
})();

// Theme toggle function (can be called from any page)
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('menza-theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function getTheme() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
}


