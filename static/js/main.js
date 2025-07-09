// minimal js for cherrybot dashboard
console.log('cherrybot dashboard loaded');

// basic page loading overlay
window.addEventListener('load', () => {
  const loader = document.getElementById('page-loader');
  if (loader) {
    loader.classList.add('hidden');
    setTimeout(() => loader.remove(), 450);
  }
});
