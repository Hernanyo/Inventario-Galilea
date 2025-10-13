// javascripts/mermaid-init.js
document.addEventListener("DOMContentLoaded", function () {
  mermaid.initialize({
    startOnLoad: true,
    securityLevel: "loose",
    theme: "default",
    themeVariables: {
      fontSize: "26px"   // ← sube el tamaño base (ajusta a gusto: 24–30px)
    },
    flowchart: { useMaxWidth: false },
    er:        { useMaxWidth: false, diagramPadding: 20 } // padding extra
  });
});
