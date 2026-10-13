const $ = selector => document.querySelector(selector);
const form = $('#assumptions');
let latest = null;
let baseline = null;
let selectedMonth = null;
let running = false;
const number = (value, digits = 2) => value.toLocaleString('en-US', {
  minimumFractionDigits: digits, maximumFractionDigits: digits,
});

function controls() {
  form.querySelectorAll('input, select, button').forEach(input => input.disabled = running);
  $('#restore').disabled = running || !baseline;
  $('.results').setAttribute('aria-busy', running);
  document.querySelectorAll('[data-rate-control]').forEach(input => input.disabled = running);
}

function modelNote() {
  const random = form.elements.model.value === 'random';
  document.querySelectorAll('[data-chart-vasicek]').forEach(label => label.hidden = random);
  $('#model-note').textContent = random
    ? 'Random walk: shocks accumulate with no pull toward a target. This model adds an upward drift of 0.05 percentage points per year.'
    : 'Vasicek: rates fluctuate but are pulled toward a long-term level.';
}

function histogram(values) {
  let min = Math.min(...values), max = Math.max(...values);
  if (max - min < .000001) { min -= .5; max += .5; }
  const bins = Array(24).fill(0);
  const width = (max - min) / bins.length;
  values.forEach(value => bins[Math.min(23, Math.floor((value - min) / width))]++);
  const top = Math.max(...bins);
  const x = value => 44 + (value - min) / (max - min) * 650;
  let svg = '';
  for (let i = 0; i <= 3; i++) {
    const y = 20 + i * 50;
    svg += `<line x1="44" x2="694" y1="${y}" y2="${y}" stroke="#2a323e"/><text x="35" y="${y + 4}" text-anchor="end">${Math.round(top * (1 - i / 3))}</text>`;
  }
  bins.forEach((count, i) => {
    const height = count / top * 150;
    svg += `<rect x="${44 + i * 650 / 24}" y="${170 - height}" width="${650 / 24 - 3}" height="${height}" rx="2" fill="#7ea5da"><title>${number(min + i * width)} to ${number(min + (i + 1) * width)}: ${count} scenarios</title></rect>`;
  });
  for (let i = 0; i <= 4; i++) {
    const value = min + (max - min) * i / 4;
    svg += `<text x="${x(value)}" y="193" text-anchor="middle">${number(value, 1)}</text>`;
  }
  if (min < 0 && max > 0) {
    svg += `<line x1="${x(0)}" x2="${x(0)}" y1="20" y2="170" stroke="#e6a36f" stroke-dasharray="4 4"/>`;
  }
  svg += '<text x="369" y="222" text-anchor="middle">Surplus · model units</text>';
  $('#histogram').innerHTML = svg;
  $('#histogram').setAttribute('aria-label', `Surplus distribution across ${values.length} scenarios, ranging from ${number(Math.min(...values))} to ${number(Math.max(...values))} model units`);
}

function render() {
  selectedMonth = Math.min(selectedMonth ?? latest.rates.years.length - 1, latest.rates.years.length - 1);
  drawRates();
  for (const key of ['assets', 'liabilities', 'surplus']) {
    $('#' + key).textContent = number(latest[key]);
    const difference = latest[key] - baseline[key];
    $('#' + key + '-delta').textContent = `${difference >= 0 ? '+' : ''}${number(difference)} vs starting assumptions`;
  }
  const rows = [['Assets', 'asset_pv01'], ['Liabilities', 'liability_pv01'], ['Surplus', 'surplus_pv01']];
  const signedChange = pv01 => {
    const change = -pv01;
    if (Math.abs(change) < .0005) return '≈ 0.000';
    return `${change > 0 ? '+' : '−'}${number(Math.abs(change), 3)}`;
  };
  $('#pv01').innerHTML = rows.map(([label, key]) =>
    `<tr><td>${label}</td><td>${signedChange(baseline[key])}</td><td>${signedChange(latest[key])}</td></tr>`
  ).join('');
  const surplusChange = -latest.surplus_pv01;
  const assetChange = -latest.asset_pv01;
  const liabilityChange = -latest.liability_pv01;
  let takeaway;
  if (Math.abs(surplusChange) < .0005) {
    takeaway = 'Assets and liabilities change by nearly the same amount, so surplus changes by less than 0.001 model units.';
  } else if (assetChange < 0 && liabilityChange < 0) {
    takeaway = surplusChange > 0
      ? 'Liabilities fall more than assets, so surplus increases.'
      : 'Assets fall more than liabilities, so surplus decreases.';
  } else {
    takeaway = `Surplus ${surplusChange > 0 ? 'increases' : 'decreases'} because it equals assets minus liabilities.`;
  }
  $('#pv01-note').textContent = takeaway;
  const sorted = [...latest.surplus_values].sort((a, b) => a - b);
  const percentile = q => {
    const index = (sorted.length - 1) * q;
    const low = Math.floor(index), high = Math.ceil(index);
    return sorted[low] + (sorted[high] - sorted[low]) * (index - low);
  };
  $('#p5').textContent = number(percentile(.05));
  $('#p95').textContent = number(percentile(.95));
  $('#deficit').textContent = number(sorted.filter(v => v < 0).length / sorted.length * 100, 1) + '%';
  histogram(latest.surplus_values);
  const names = {model: 'Model', r0: 'Initial rate (%)', b: 'Long-term rate (%)', a: 'Mean reversion', sigma: 'Volatility (%)', payment: 'Annual payment', years: 'Horizon', paths: 'Scenarios', seed: 'Seed'};
  const changes = Object.keys(names).filter(key => Number(latest.assumptions[key]) !== Number(baseline.assumptions[key]) && latest.assumptions[key] !== baseline.assumptions[key]);
  $('#comparison-note').textContent = changes.length
    ? 'Changed from starting assumptions: ' + changes.map(key => `${names[key]} ${baseline.assumptions[key]} → ${latest.assumptions[key]}`).join(' · ')
    : 'The current run matches your starting assumptions. Change an assumption to explore its effect.';
  if (changes.some(key => ['model', 'years', 'paths', 'seed'].includes(key))) {
    $('#comparison-note').textContent += ' The scenario setup or random draws differ between runs.';
  }
}

async function run(event) {
  event?.preventDefault();
  if (running || !form.reportValidity()) return;
  const assumptions = Object.fromEntries(new FormData(form));
  clearTimeout(updateTimer);
  running = true;
  controls();
  $('#error').textContent = '';
  $('#status').textContent = 'Calculating scenarios and sensitivities…';
  $('#chart-update-note').textContent = 'Recalculating curves and balance sheet…';
  try {
    const response = await fetch('/api/simulate', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(assumptions),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Simulation failed');
    latest = result;
    if (!baseline) baseline = structuredClone(result);
    render();
    $('#chart-update-note').textContent = 'Curves and balance sheet updated. Blue paths show individual simulated futures.';
    $('#status').textContent = `${assumptions.paths} scenarios · ${assumptions.years} years · seed ${assumptions.seed}`;
  } catch (error) {
    $('#error').textContent = error.message;
    $('#chart-update-note').textContent = 'Update failed; the chart still shows the previous run.';
    $('#status').textContent = latest ? 'Previous results · current update failed' : 'Simulation unavailable';
  } finally {
    running = false;
    controls();
  }
}

function fill(assumptions) {
  Object.entries(assumptions).forEach(([key, value]) => form.elements.namedItem(key).value = value);
  syncSliders();
  modelNote();
}
form.addEventListener('submit', run);
form.addEventListener('input', event => {
  const key = event.target.dataset.control || event.target.dataset.rateControl;
  if (key) form.elements[key].value = event.target.value;
  syncSliders();
  if (latest) {
    $('#status').textContent = 'Assumptions changed · updating';
    $('#chart-update-note').textContent = 'Updating after you pause; paths and values still show the previous completed run.';
    drawRates();
  }
  modelNote();
  controls();
  clearTimeout(updateTimer);
  updateTimer = setTimeout(() => run(), 600);
});
$('#restore').addEventListener('click', () => { fill(baseline.assumptions); run(); });
let updateTimer;

// Sliders share the number fields; only named fields are sent to Python.
for (const key of ['payment']) {
  const field = form.elements[key];
  const slider = document.createElement('input');
  slider.type = 'range';
  slider.min = field.min;
  slider.max = field.max;
  slider.step = field.step;
  slider.value = field.value;
  slider.dataset.control = key;
  slider.className = 'assumption-slider';
  slider.setAttribute('aria-label', field.closest('label').childNodes[0].textContent.trim() + ' slider');
  field.after(slider);
}
function syncSliders() {
  document.querySelectorAll('[data-rate-control]').forEach(slider => {
    const key = slider.dataset.rateControl;
    slider.value = form.elements[key].value;
    $('#chart-' + key + '-value').textContent = form.elements[key].value + (key === 'a' ? '' : '%');
  });
  form.querySelectorAll('[data-control]').forEach(slider => {
    slider.value = form.elements[slider.dataset.control].value;
  });
}

function drawRates() {
  if (!latest) return;
  const r = latest.rates;
  const selected = selectedMonth;
  // Smooth pointwise 90% range from the rate model, as in the original explorer.
  const r0 = Number(latest.assumptions.r0) / 100;
  const b = Number(latest.assumptions.b) / 100;
  const a = Number(latest.assumptions.a);
  const sigma = Number(latest.assumptions.sigma) / 100;
  const random = latest.assumptions.model === 'random';
  const envelopeMean = r.years.map(t => random ? r0 + .0005 * t : b + (r0 - b) * Math.exp(-a * t));
  const spread = r.years.map(t => 1.644853626951 * sigma * Math.sqrt(
    random || a === 0 ? t : -Math.expm1(-2 * a * t) / (2 * a)
  ));
  const lower = envelopeMean.map((m, i) => m - spread[i]);
  const upper = envelopeMean.map((m, i) => m + spread[i]);
  const values = [...lower, ...upper, ...r.p5, ...r.p95, ...r.samples.flat(), ...baseline.rates.mean];
  let low = Math.min(...values) * 100, high = Math.max(...values) * 100;
  const padding = Math.max((high - low) * .08, .1);
  low -= padding; high += padding;
  const x = i => 72 + i / (r.years.length - 1) * 622;
  const y = value => 210 - (value * 100 - low) / (high - low) * 190;
  const line = values => values.map((value, i) => `${i ? 'L' : 'M'}${x(i)},${y(value)}`).join(' ');
  let svg = '<text x="8" y="115" text-anchor="middle" transform="rotate(-90 8 115)">Interest rate (%)</text>';
  for (let i = 0; i <= 4; i++) {
    const value = low + (high - low) * i / 4;
    const height = y(value / 100);
    svg += `<line x1="72" x2="694" y1="${height}" y2="${height}" stroke="#2a323e"/><text x="64" y="${height + 4}" text-anchor="end">${number(value, 1)}%</text>`;
    const index = Math.round((r.years.length - 1) * i / 4);
    svg += `<text x="${x(index)}" y="232" text-anchor="middle">${number(r.years[index], 1)}</text>`;
  }
  if ($('#show-band').checked) {
    const cx = x(selected), top = y(upper[selected]), bottom = y(lower[selected]);
    svg += `<path d="M${cx},${top} V${bottom} M${cx - 7},${top} H${cx + 7} M${cx - 7},${bottom} H${cx + 7}" fill="none" stroke="#7ea5da" stroke-width="3"><title>Model 90% rate range at year ${number(r.years[selected], 1)}: ${number(lower[selected] * 100)}% to ${number(upper[selected] * 100)}%</title></path>`;
  }
  if ($('#show-paths').checked) r.samples.forEach(values => {
    svg += `<path d="${line(values)}" fill="none" stroke="#7ea5da" stroke-width="1" opacity=".4"/>`;
  });
  const baselinePoints = baseline.rates.mean.map((v, i) => {
    const bx = 72 + baseline.rates.years[i] / r.years[r.years.length - 1] * 622;
    return `${i ? 'L' : 'M'}${bx},${y(v)}`;
  }).filter((point, i) => baseline.rates.years[i] <= r.years[r.years.length - 1]).join(' ');
  if ($('#show-baseline').checked) svg += `<path d="${baselinePoints}" fill="none" stroke="#e5e8ed" stroke-width="2" stroke-dasharray="6 5" opacity=".7"/>`;
  if ($('#show-mean').checked) svg += `<path d="${line(r.mean)}" fill="none" stroke="#e6a36f" stroke-width="2.5"/>`;
  if ($('#show-paths').checked) r.samples.forEach(values => {
    svg += `<circle cx="${x(selected)}" cy="${y(values[selected])}" r="2.5" fill="#7ea5da"/>`;
  });
  const last = r.years.length - 1;
  const currentY = y(r.mean[last]);
  const startingIndex = Math.min(last, baseline.rates.mean.length - 1);
  let startingY = y(baseline.rates.mean[startingIndex]);
  if (Math.abs(startingY - currentY) < 18) startingY = Math.min(201, currentY + 20);
  if ($('#show-mean').checked) svg += `<text class="curve-label" x="688" y="${Math.max(14, currentY - 9)}" text-anchor="end" style="fill:#e6a36f">Current scenario average</text>`;
  if ($('#show-baseline').checked) svg += `<text class="curve-label" x="${Math.min(688, 72 + baseline.rates.years[startingIndex] / r.years[last] * 622)}" y="${Math.max(14, startingY - 9)}" text-anchor="end" style="fill:#e5e8ed">Original scenario average</text>`;
  svg += `<line x1="${x(selected)}" x2="${x(selected)}" y1="20" y2="210" stroke="#e5e8ed" stroke-dasharray="4 4"/><circle cx="${x(selected)}" cy="${y(r.mean[selected])}" r="4" fill="#e6a36f"/><text x="371" y="254" text-anchor="middle">Projection year</text>`;
  $('#rate-chart').innerHTML = svg;
  const year = r.years[selected];
  const baselineIndex = Math.round(year * 12);
  const baselineDiscount = baseline.rates.discount[baselineIndex];
  const latestDiscount = r.discount[selected];
  $('#payment-year').textContent = number(year, 1);
  $('#latest-discount').textContent = '$' + number(latestDiscount, 4);
  $('#baseline-discount').textContent = baselineDiscount === undefined ? 'Outside starting horizon' : '$' + number(baselineDiscount, 4);
  const difference = latestDiscount - baselineDiscount;
  $('#discount-change').textContent = baselineDiscount === undefined ? '—' : `${difference >= 0 ? '+' : '−'}$${number(Math.abs(difference), 4)}`;
  $('#discount-explanation').textContent = year === 0
    ? '$1 paid today is worth $1 today.'
    : `Example: $1 paid at this time is worth $${number(latestDiscount, 4)} today.`;
  $('#time-value').textContent = number(year, 1);
  $('#rate-mean').textContent = number(r.mean[selected] * 100) + '%';
  $('#rate-range').textContent = `${number(r.p5[selected] * 100)}% – ${number(r.p95[selected] * 100)}%`;
  $('#rate-chart').setAttribute('aria-label', `Interest rate scenarios. Year ${number(r.years[selected], 1)}, mean ${number(r.mean[selected] * 100)} percent.`);
}
for (const id of ['show-mean', 'show-band', 'show-paths', 'show-baseline']) $('#' + id).addEventListener('change', drawRates);
function inspectPointer(event) {
  if (!latest) return;
  const rect = $('#rate-chart').getBoundingClientRect();
  // SVG has 15px of CSS padding on each side.
  const svgX = (event.clientX - rect.left - 15) / (rect.width - 30) * 720;
  selectedMonth = Math.round(Math.max(0, Math.min(1, (svgX - 72) / 622)) * (latest.rates.years.length - 1));
  drawRates();
}
$('#rate-chart').addEventListener('pointerdown', event => {
  $('#rate-chart').setPointerCapture(event.pointerId);
  inspectPointer(event);
});
$('#rate-chart').addEventListener('pointermove', inspectPointer);
$('#rate-chart').addEventListener('keydown', event => {
  if (!latest || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
  event.preventDefault();
  selectedMonth = Math.max(0, Math.min(latest.rates.years.length - 1, selectedMonth + (event.key === 'ArrowRight' ? 1 : -1)));
  drawRates();
});
modelNote();
run();
