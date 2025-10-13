(function () {
  // Solo en la página de impresión del plugin
  if (!/\/print_page\/?$/.test(location.pathname)) return;

  function killTOC(root) {
    if (!root) return false;
    let removed = false;

    // Contenedores conocidos
    root.querySelectorAll(
      '.print-site-toc, .md-print-toc, .md-print__toc, #print-site-toc'
    ).forEach(n => { n.remove(); removed = true; });

    // Patrón H1 + (nav|ul|ol)
    const h1 = root.querySelector('h1');
    if (h1) {
      const txt = (h1.textContent || '').trim().toLowerCase();
      if (/(table of contents|contenido|índice|indice|contents)/.test(txt)) {
        const next = h1.nextElementSibling;
        h1.remove();
        removed = true;
        if (next && /^(nav|ul|ol)$/i.test(next.tagName)) next.remove();
      }
    }
    return removed;
  }

  function run() {
    const root = document.querySelector('.md-content__inner') || document.querySelector('main');
    if (!root) return;

    // Intenta borrar ya
    if (killTOC(root)) return;

    // Si el TOC aparece luego, bórralo al vuelo
    const obs = new MutationObserver(() => {
      if (killTOC(root)) obs.disconnect();
    });
    obs.observe(root, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
