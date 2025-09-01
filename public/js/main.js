import { estimarHoras } from "./utils.js";
import { initDetailsModal, renderHeader, renderSummary, renderCards } from "./ui.js";

document.addEventListener("DOMContentLoaded", () => {
  const setupModal = document.getElementById("setup-modal");
  const setupForm = document.getElementById("setup-form");
  const hoursInput = document.getElementById("hours-input");
  const mainContainer = document.querySelector(".container");
  const recalibrateBtn = document.getElementById("recalibrate-btn");

  // Helper function to run the typing animation, making it reusable.
  function runSetupAnimation(title, paragraph, startDelay = 1200) {
    const titleEl = document.getElementById("setup-title");
    const paragraphEl = document.getElementById("setup-paragraph");

    // Reset content to allow Typed.js to re-run correctly.
    titleEl.innerHTML = "";
    paragraphEl.innerHTML = "";
    setupForm.classList.remove("visible");

    // Animate title
    new Typed(titleEl, {
      strings: [title],
      typeSpeed: 15,
      showCursor: false,
    });

    // Animate paragraph and show form on completion
    new Typed(paragraphEl, {
      strings: [paragraph],
      typeSpeed: 15,
      startDelay: startDelay,
      showCursor: true,
      cursorChar: "▋",
      onComplete: (self) => {
        self.cursor.remove();
        setupForm.classList.add("visible");
      },
    });
  }

  // Function to show the recalibration screen, simulating component destruction and creation.
  function showRecalibrateModal() {
    // "Destroy" the main report view by hiding it and clearing its dynamic content.
    mainContainer.style.display = "none";
    document.getElementById("report-header").innerHTML = "";
    document.getElementById("summary-metrics").innerHTML = "";
    document.getElementById("cards").innerHTML = "";
    // The chart canvases are recreated by renderSummary, so this is a safe reset.
    document.getElementById("points-chart").parentElement.innerHTML =
      '<canvas id="points-chart"></canvas>';
    document.getElementById("complexity-chart").parentElement.innerHTML =
      '<canvas id="complexity-chart"></canvas>';

    // Prepare and show the setup/recalibration modal.
    const currentHours = localStorage.getItem("horasParaComplejidad5") || 16;
    hoursInput.value = currentHours;

    setupModal.style.display = "flex";
    setTimeout(() => {
      setupModal.style.opacity = "1";
    }, 10);

    // "Create" the recalibration view by running the animations again.
    runSetupAnimation(
      "Recalibrar Estimaciones",
      "Ajusta el número de horas para una historia de <strong>complejidad máxima (5)</strong> para recalcular el reporte.",
      500 // Use a shorter delay for a snappier feel.
    );
  }

  const storedHours = localStorage.getItem("horasParaComplejidad5");
  if (storedHours) {
    setupModal.style.display = "none";
    mainContainer.style.display = "block";
    startApp(parseFloat(storedHours));
  } else {
    // Initial setup uses the same animation function.
    runSetupAnimation(
      "✦ Asistente de Calibración IA ✦",
      "Para optimizar las estimaciones, necesito entender la capacidad de tu equipo. La complejidad de las historias se mide en una escala de 1 (muy simple) a 5 (muy compleja).<br><br>Por favor, define tu punto de referencia: ¿cuántas <strong>horas</strong> de trabajo reales representa una historia de <strong>complejidad máxima (5)</strong>?"
    );
  }

  setupForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const horasParaComplejidad5 = parseFloat(hoursInput.value);
    if (isNaN(horasParaComplejidad5) || horasParaComplejidad5 <= 0) {
      alert("Por favor, introduce un número válido de horas.");
      return;
    }

    localStorage.setItem("horasParaComplejidad5", horasParaComplejidad5);

    setupModal.style.opacity = "0";
    setTimeout(() => {
      setupModal.style.display = "none";
      mainContainer.style.display = "block";
      // Usamos requestAnimationFrame para asegurar que el navegador ha procesado el cambio de 'display'
      // y está listo para pintar. Esto garantiza que Chart.js detecte que el canvas es visible
      // y ejecute las animaciones de entrada correctamente al recalibrar.
      requestAnimationFrame(() => {
        startApp(horasParaComplejidad5);
      });
    }, 500); // Espera a que la transición de opacidad del modal termine
  });

  recalibrateBtn.addEventListener("click", showRecalibrateModal);
});

function startApp(horasParaComplejidad5) {
  fetch("/data")
    .then((r) => r.json())
    .then((response) => {
      const metadata = response.metadata;
      const data = response.data; // El array de historias ahora está en la clave 'data'

      // Recalculate estimations based on user input
      const horasPorComplejidad = horasParaComplejidad5 / 5;
      const totalHistorias = data.length;

      const recalibratedData = data.map((historia) => {
        const nuevaEstimacion = estimarHoras(
          historia.complejidad,
          totalHistorias,
          horasPorComplejidad
        );
        return { ...historia, estimacion_horas: nuevaEstimacion };
      });

      // Initialize UI components
      const showModal = initDetailsModal();
      init(recalibratedData, showModal, metadata);
    });
}

function init(data, showModal, metadata) {
  // Get CSS variables for charts
  const computedStyles = getComputedStyle(document.documentElement);
  const colors = {
    primary: computedStyles.getPropertyValue("--primary-color").trim(),
    primaryLight: computedStyles
      .getPropertyValue("--primary-color-light")
      .trim(),
    accent: computedStyles.getPropertyValue("--accent-color").trim(),
    secondary: computedStyles.getPropertyValue("--secondary-color").trim(),
    danger: computedStyles.getPropertyValue("--danger-color").trim(),
    textColor: computedStyles.getPropertyValue("--text-color").trim(),
    borderColor: computedStyles.getPropertyValue("--border-color").trim(),
    lightTextColor: computedStyles
      .getPropertyValue("--light-text-color")
      .trim(),
  };

  renderHeader(metadata);
  renderSummary(data, colors);
  renderCards(data, colors, showModal);
}
