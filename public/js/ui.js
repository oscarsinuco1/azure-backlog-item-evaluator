let pointsChartInstance = null;
let complexityChartInstance = null;
let radarChartInstances = [];

export function initDetailsModal() {
  const modalContainer = document.getElementById("modal-container");
  const modalClose = document.getElementById("modal-close");
  const modalTitle = document.getElementById("modal-title");
  const modalBody = document.getElementById("modal-body");

  const showModal = (title, content) => {
    modalTitle.innerHTML = title;
    modalBody.innerHTML = content;
    modalContainer.classList.remove("hidden");
  };

  const hideModal = () => modalContainer.classList.add("hidden");

  modalClose.addEventListener("click", hideModal);
  modalContainer.addEventListener("click", (e) => {
    if (e.target === modalContainer) {
      hideModal();
    }
  });

  return showModal;
}

export function renderHeader(metadata) {
  const headerDiv = document.getElementById("report-header");
  if (!headerDiv || !metadata) return;

  const { organizacion, proyecto, sprint } = metadata;

  // Construct URLs to Azure DevOps
  const orgUrl = `https://dev.azure.com/${organizacion}`;
  const projectUrl = `${orgUrl}/${proyecto}`;
  // The full iteration path doesn't map to a direct URL, so we link to the general backlogs page
  //Esto sirve pero porfa convierte sprint en algo valido para la url.
  // https://dev.azure.com/XM-Mercado/ModeloDatosComun/_backlogs/backlog/ModeloDatosComun/MDC%20-%20PAR%C3%81METROS/A%C3%B1o%202020/Release%202/Sprint%2014

  // El path del sprint usa '\', lo reemplazamos por '/' y codificamos cada parte para la URL.
  const sprintPath = sprint
    .split("\\")
    .map((part) => encodeURIComponent(part))
    .join("/");

  headerDiv.innerHTML = `
    <div class="metadata-item">
      <span>Organización</span>
      <a href="${orgUrl}" target="_blank" rel="noopener noreferrer" title="Ir a la organización en Azure DevOps">${organizacion}</a>
    </div>
    <div class="metadata-item">
      <span>Proyecto</span>
      <a href="${projectUrl}" target="_blank" rel="noopener noreferrer" title="Ir al proyecto en Azure DevOps">${proyecto}</a>
    </div>
    <div class="metadata-item">
      <span>Sprint</span>
      <a href="${projectUrl}" target="_blank" rel="noopener noreferrer" title="Ir a los backlogs del proyecto">${sprint}</a>
    </div>
  `;
}

export function renderSummary(data, colors) {
  const summaryMetricsDiv = document.getElementById("summary-metrics");
  if (!summaryMetricsDiv) return;

  const totalStories = data.length;
  const totalHoras = data.reduce((sum, h) => sum + h.estimacion_horas, 0);
  const weightedComplexitySum = data.reduce(
    (sum, h) => sum + h.complejidad * h.estimacion_horas,
    0
  );
  const avgComplexity =
    totalHoras > 0 ? (weightedComplexitySum / totalHoras).toFixed(2) : 0;

  // Destruir instancias de gráficos anteriores para evitar fugas de memoria y permitir la re-animación
  if (pointsChartInstance) {
    pointsChartInstance.destroy();
  }
  if (complexityChartInstance) {
    complexityChartInstance.destroy();
  }

  // Forzar la re-animación de los gráficos al recalibrar, siguiendo tu idea.
  // La forma más robusta es eliminar los canvas antiguos y volver a crearlos.
  // Esto asegura que Chart.js los trate como elementos nuevos y ejecute la animación de entrada.
  const pointsChartWrapper =
    document.getElementById("points-chart").parentElement;
  const complexityChartWrapper =
    document.getElementById("complexity-chart").parentElement;

  pointsChartWrapper.innerHTML = '<canvas id="points-chart"></canvas>';
  complexityChartWrapper.innerHTML = '<canvas id="complexity-chart"></canvas>';

  summaryMetricsDiv.innerHTML = `
      <div class="summary-card"><h3>Total Historias</h3><div class="value">${totalStories}</div></div>
      <div class="summary-card"><h3>Total Horas Estimadas</h3><div class="value">${totalHoras.toFixed(
        1
      )}</div></div>
      <div class="summary-card"><h3>Complejidad Promedio</h3><div class="value">${avgComplexity}</div></div>
    `;

  // Helper function to unify color logic based on complexity
  const getComplexityColor = (complexity) => {
    if (complexity > 4) return colors.danger; // Very complex (e.g., 5)
    if (complexity > 2.5) return colors.accent; // Complex (e.g., 3, 3.5, 4)
    return colors.primary; // Normal (e.g., 1, 1.5, 2, 2.5)
  };

  // Chart 1: Estimated hours per HU
  pointsChartInstance = new Chart(document.getElementById("points-chart"), {
    type: "bar",
    data: {
      labels: data.map((h) => `HU ${h.id}`),
      datasets: [
        {
          label: "Horas Estimadas",
          data: data.map((h) => h.estimacion_horas),
          backgroundColor: data.map((h) => getComplexityColor(h.complejidad)),
          borderColor: data.map((h) => getComplexityColor(h.complejidad)),
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: colors.lightTextColor },
          grid: { color: colors.borderColor },
        },
        x: {
          ticks: { color: colors.lightTextColor },
          grid: { display: false },
        },
      },
      plugins: {
        legend: { display: false },
      },
      animation: {
        duration: 800,
        easing: "easeOutQuart",
      },
    },
  });

  // Chart 2: Complexity distribution
  const complexityCounts = data.reduce((acc, h) => {
    const key = h.complejidad;
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  const sortedComplexityKeys = Object.keys(complexityCounts).sort(
    (a, b) => parseFloat(a) - parseFloat(b)
  );

  complexityChartInstance = new Chart(
    document.getElementById("complexity-chart"),
    {
      type: "doughnut",
      data: {
        labels: sortedComplexityKeys.map((c) => `Complejidad ${c}`),
        datasets: [
          {
            label: "Nº de Historias",
            data: sortedComplexityKeys.map((key) => complexityCounts[key]),
            backgroundColor: sortedComplexityKeys.map((key) =>
              getComplexityColor(parseFloat(key))
            ),
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: { color: colors.textColor },
          },
        },
        animation: {
          duration: 800,
          easing: "easeOutQuart",
        },
      },
    }
  );
}

export function renderCards(data, colors, showModal) {
  const cardsDiv = document.getElementById("cards");
  if (!cardsDiv) return;

  // Destruir instancias de gráficos de radar anteriores
  radarChartInstances.forEach((chart) => chart.destroy());
  radarChartInstances = [];

  cardsDiv.innerHTML = ""; // Clear previous cards

  data.forEach((historia, i) => {
    const card = document.createElement("div");
    card.className = "card";

    const investData = historia.evaluacion_invest;

    const cardHeader = document.createElement("div");
    cardHeader.className = "card-header";

    const title = document.createElement("h2");
    // Si la historia tiene una URL, crea un enlace. Si no, solo muestra el texto.
    if (historia.url) {
      const titleLink = document.createElement("a");
      titleLink.href = historia.url;
      titleLink.target = "_blank";
      titleLink.rel = "noopener noreferrer";
      titleLink.title = "Ver historia en Azure DevOps";
      titleLink.textContent = `HU ${historia.id}: ${historia.titulo}`;
      title.appendChild(titleLink);
    } else {
      title.textContent = `HU ${historia.id}: ${historia.titulo}`;
    }
    cardHeader.appendChild(title);

    const badges = document.createElement("div");
    badges.className = "badges";
    badges.innerHTML = `
        <span class="badge horas">Horas: ${historia.estimacion_horas}</span>
        <span class="badge complejidad">Complejidad: ${historia.complejidad}</span>
      `;
    cardHeader.appendChild(badges);
    card.appendChild(cardHeader);

    const cardContent = document.createElement("div");
    cardContent.className = "card-content";

    const canvasContainer = document.createElement("div");
    canvasContainer.className = "chart-container";
    const canvas = document.createElement("canvas");
    canvas.id = "chart-" + i;
    canvasContainer.appendChild(canvas);

    let detailsHtml = `<div class="details-container"><h3>Evaluación INVEST</h3><div class="invest-details">`;
    const labels = Object.keys(investData);
    const scores = labels.map((key) => investData[key].puntaje);
    const justifications = labels.map((key) => investData[key].justificacion);

    labels.forEach((label, index) => {
      detailsHtml += `<p><strong>${label} (${scores[index]}/5):</strong> ${justifications[index]}</p>`;
    });

    detailsHtml += `</div>`;

    if (historia.posibles_mejoras && historia.posibles_mejoras.length > 0) {
      detailsHtml += `<h3>Posibles Mejoras</h3><ul class="improvements-list">`;
      historia.posibles_mejoras.forEach((mejoras) => {
        detailsHtml += `<li>${mejoras}</li>`;
      });
      detailsHtml += `</ul>`;
    }
    detailsHtml += `</div>`; // Close .details-container

    const cardActions = document.createElement("div");
    cardActions.className = "card-actions";

    const detailsButton = document.createElement("button");
    detailsButton.className = "details-toggle-btn";
    detailsButton.textContent = "Ver Detalles";

    detailsButton.addEventListener("click", () => {
      showModal(`HU ${historia.id}: ${historia.titulo}`, detailsHtml);
    });

    cardActions.appendChild(detailsButton);

    cardContent.appendChild(canvasContainer);
    card.appendChild(cardContent);
    card.appendChild(cardActions);

    const avgInvestScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    if (historia.complejidad > 2.5 || avgInvestScore < 2.5) {
      card.classList.add("is-problematic");
    }

    cardsDiv.appendChild(card);

    // Initialize radar chart
    const radarChart = new Chart(canvas, {
      type: "radar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Puntaje INVEST",
            data: scores,
            backgroundColor: colors.primaryLight,
            borderColor: colors.primary,
            pointBackgroundColor: colors.primary,
          },
        ],
      },
      options: {
        scales: {
          r: {
            min: 0,
            max: 5,
            ticks: {
              stepSize: 1,
              color: colors.lightTextColor,
              backdropColor: "transparent",
            },
            grid: { color: colors.borderColor },
            angleLines: { color: colors.borderColor },
            pointLabels: {
              color: colors.textColor,
              font: { size: 12 },
            },
          },
        },
        plugins: { legend: { display: false } },
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 800,
          easing: "easeOutQuart",
        },
      },
    });
    radarChartInstances.push(radarChart);
  });
}
