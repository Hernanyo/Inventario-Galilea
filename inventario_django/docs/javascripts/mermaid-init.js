document.addEventListener('DOMContentLoaded', () => {
  if (window.mermaid) {
    mermaid.initialize({
      startOnLoad: true,
      securityLevel: 'loose',     // permite <br/> si lo usas
      flowchart: { htmlLabels: true }
    });
  } else {
    console.warn('Mermaid no está cargado (window.mermaid undefined).');
  }
});