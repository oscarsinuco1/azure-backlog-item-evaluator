/**
 * Replicates the Python estimation logic in JavaScript.
 * @param {number} complejidad - The complexity value of the story.
 * @param {number} totalHistorias - The total number of stories in the sprint.
 * @param {number} horasPorComplejidad - The calculated hours per complexity unit.
 * @returns {number} The estimated hours for the story, rounded to one decimal place.
 */
export function estimarHoras(complejidad, totalHistorias, horasPorComplejidad) {
  const sprintHoras = 78; // Based on user input: "sprint de 10 usualmente es de 78 horas"
  const cargaEquipo = -20; // Based on get-hist.py hardcoded value for team capacity adjustment

  // Base days according to complexity
  const base = horasPorComplejidad * complejidad;

  // Overhead for ceremonies, distributed among all stories
  const overheadTotal = sprintHoras * 0.15;
  const overheadPorHistoria = overheadTotal / Math.max(1, totalHistorias);

  // Adjustment based on team load (%)
  const ajuste = base * (1 + cargaEquipo / 100);

  // Final days
  const horasFinales = ajuste + overheadPorHistoria;
  return Math.round(horasFinales * 10) / 10;
}
