document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const menuContent = document.getElementById('menuContent');

    // Toggle menu when burger icon is clicked
    menuToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        menuContent.classList.toggle('hidden');
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!menuContent.contains(e.target) && !menuToggle.contains(e.target)) {
            menuContent.classList.add('hidden');
        }
    });
});