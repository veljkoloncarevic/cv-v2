// Only enhancement on the public site: the mobile nav toggle.
// Nothing here is required to render or index the page.
(function () {
  var toggle = document.querySelector('.topbar__toggle');
  var nav = document.getElementById('topnav');
  if (!toggle || !nav) return;

  toggle.addEventListener('click', function () {
    var open = nav.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
  });

  // Close the menu when a link is tapped or the viewport grows past the breakpoint.
  nav.addEventListener('click', function (e) {
    if (e.target.closest('a')) {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });

  window.matchMedia('(min-width: 721px)').addEventListener('change', function (e) {
    if (e.matches) {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
})();
