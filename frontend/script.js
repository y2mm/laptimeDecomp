/*
 * Frontend logic for the Lap Time Bottleneck Finder.
 *
 * Handles uploading the telemetry CSV, sending it to the Flask API,
 * processing the returned JSON and rendering both a results table
 * and a bar chart summarising where time is lost across segments.
 */

// Keep a reference to the current Chart.js chart instance so it can be
// destroyed when new data arrives (Chart.js does not automatically
// overwrite an existing chart).
let bottleneckChart = null;

/**
 * Format a floating point value to a fixed number of decimals.
 * Uses three decimals by default.
 *
 * @param {number|string} value The numeric value to format.
 * @param {number} decimals Number of decimal places.
 * @returns {string} Formatted string.
 */
function formatNumber(value, decimals = 3) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "";
  return n.toFixed(decimals);
}

/**
 * Render the analysis table with the given data.
 *
 * @param {Array<Object>} data Array of segment analysis objects.
 */
function renderTable(data) {
  const tbody = document.querySelector("#results-table tbody");
  tbody.innerHTML = "";

  if (!data || data.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="10" style="text-align:left">No results. Upload a CSV with at least 2 laps.</td>`;
    tbody.appendChild(tr);
    return;
  }

  data.forEach((row, idx) => {
    const tr = document.createElement("tr");
    if (idx === 0) {
      tr.style.fontWeight = "700";
    }

    tr.innerHTML = `
      <td style="text-align:left">${row.segment}</td>
      <td>${formatNumber(row.avg_dt)}</td>
      <td>${formatNumber(row.best_dt)}</td>
      <td>${formatNumber(row.time_loss ?? row.loss)}</td>
      <td>${formatNumber(row.brake_time_loss)}</td>
      <td>${formatNumber(row.exit_time_loss)}</td>
      <td>${formatNumber(row.exit_throttle_delay_loss)}</td>
      <td style="text-align:left">${row.top_cause || ""}</td>
    `;

    tbody.appendChild(tr);
  });
}

/**
 * Render a bar chart of time losses per segment using Chart.js.
 *
 * @param {Array<Object>} data Array of segment analysis objects.
 */
function renderChart(data) {
  const ctx = document.getElementById("chart").getContext("2d");

  if (bottleneckChart) bottleneckChart.destroy();

  const labels = (data || []).map((d) => d.segment);
  const overall = (data || []).map((d) => Number(d.time_loss ?? d.loss) || 0);
  const brakeLoss = (data || []).map((d) => Number(d.brake_time_loss) || 0);
  const exitLoss = (data || []).map((d) => Number(d.exit_time_loss) || 0);

  bottleneckChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Overall loss (s)", data: overall },
        { label: "Brake loss (s)", data: brakeLoss },
        { label: "Exit loss (s)", data: exitLoss },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        tooltip: { mode: "index", intersect: false },
        legend: { position: "top" },
      },
      interaction: { mode: "index", intersect: false },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: "seconds" },
        },
        x: {
          title: { display: true, text: "Segment" },
        },
      },
    },
  });
}

/**
 * Handle the click event on the Analyze button.
 */
async function handleAnalyse() {
  const fileInput = document.getElementById("file-input");
  const segmentCountInput = document.getElementById("segment-count");
  const brakeThresholdInput = document.getElementById("brake-threshold");
  const throttleThresholdInput = document.getElementById("throttle-threshold");
  const loadingIndicator = document.getElementById("loading");
  if (!fileInput.files || fileInput.files.length === 0) {
    alert("Please select a CSV file before analysing.");
    return;
  }
  const file = fileInput.files[0];
  const nSegments = parseInt(segmentCountInput.value, 10) || 4;
  const brakeThreshold = brakeThresholdInput ? Number(brakeThresholdInput.value) : 0.15;
  const throttleThreshold = throttleThresholdInput ? Number(throttleThresholdInput.value) : 0.25;
  const formData = new FormData();
  formData.append("file", file);
  // Accept both names; backend supports `segments` (preferred) and `n_segments` (legacy)
  formData.append("segments", nSegments);
  formData.append("n_segments", nSegments);
  formData.append("brake_threshold", brakeThreshold);
  formData.append("throttle_threshold", throttleThreshold);
  // Show loading
  loadingIndicator.style.display = "block";
  try {
    const response = await fetch("http://127.0.0.1:5001/analyze", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Server error: ${response.status} - ${text}`);
    }
    const data = await response.json();
    renderTable(data);
    renderChart(data);
  } catch (err) {
    console.error(err);
    alert(
      "An error occurred while analysing the telemetry. Please check the console for details."
    );
  } finally {
    loadingIndicator.style.display = "none";
  }
}

// Attach event listener to the Analyze button once the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  document
    .getElementById("analyze-btn")
    .addEventListener("click", handleAnalyse);
});