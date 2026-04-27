const previewImage = document.getElementById('previewImage');
const previewFrame = document.querySelector('.preview-frame');
const previewTitle = document.getElementById('previewTitle');
const previewSize = document.getElementById('previewSize');
const previewFit = document.getElementById('previewFit');
const previewFitToggle = document.getElementById('previewFitToggle');
const topRuler = document.getElementById('topRuler');
const leftRuler = document.getElementById('leftRuler');
const bridgeBadge = document.getElementById('bridgeBadge');
const machineState = document.getElementById('machineState');
const positionState = document.getElementById('positionState');
const rotaryState = document.getElementById('rotaryState');
const rotaryToggle = document.getElementById('rotaryToggle');
const rotaryDiameter = document.getElementById('rotaryDiameter');
const setRotaryDiameter = document.getElementById('setRotaryDiameter');
const filesTableBody = document.getElementById('filesTableBody');
const selectedFileName = document.getElementById('selectedFileName');
const rdPath = document.getElementById('rdPath');
const laser1Toggle = document.getElementById('laser1Toggle');
const laser2Toggle = document.getElementById('laser2Toggle');
const laser1State = document.getElementById('laser1State');
const laser2State = document.getElementById('laser2State');
const unusedSettingsList = document.getElementById('unusedSettingsList');
const lastResult = document.getElementById('lastResult');
const versionPill = document.getElementById('versionPill');
const setupWarning = document.getElementById('setupWarning');
const setupMissingList = document.getElementById('setupMissingList');
const dismissSetupWarning = document.getElementById('dismissSetupWarning');
const dashboardGrid = document.getElementById('dashboardGrid');

let selectedFile = null;
let lastPreviewStamp = '';
let userEditedPreviewPath = false;
let setupWarningDismissed = localStorage.getItem('ruidaSetupWarningDismissed') === 'true';
let currentRotaryDiameter = null;
let currentPreviewFitMode = normalizePreviewFitMode(localStorage.getItem('ruidaPreviewFitMode') || 'geometry');

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'unknown';
  return Number(value).toFixed(digits);
}

function formatDimension(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return Number(value).toFixed(1);
}

function normalizePreviewFitMode(value) {
  const normalized = String(value || '').trim().toLowerCase();
  return normalized === 'bed' ? 'bed' : 'geometry';
}

function updatePreviewFitUi(mode) {
  const normalized = normalizePreviewFitMode(mode);
  currentPreviewFitMode = normalized;
  localStorage.setItem('ruidaPreviewFitMode', normalized);

  if (previewFitToggle) {
    previewFitToggle.checked = normalized === 'bed';
  }

  if (previewFit) {
    previewFit.textContent = normalized === 'bed' ? 'BED VIEW' : 'EXTENTS';
  }
}

function niceRulerValue(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return '—';
  if (Math.abs(number - Math.round(number)) < 0.05) {
    return String(Math.round(number));
  }
  return number.toFixed(1);
}

function buildRulerLabels(minValue, maxValue, count = 5) {
  const minNumber = Number(minValue);
  const maxNumber = Number(maxValue);

  if (!Number.isFinite(minNumber) || !Number.isFinite(maxNumber) || maxNumber < minNumber) {
    return ['0', '—', '—', '—', '— mm'];
  }

  const labels = [];
  const span = maxNumber - minNumber;

  for (let i = 0; i < count; i += 1) {
    let value = minNumber + (span * i) / (count - 1);
    let label = niceRulerValue(value);
    if (i === count - 1) {
      label = `${label} mm`;
    }
    labels.push(label);
  }

  return labels;
}

function setRulerLabels(rulerEl, labels) {
  if (!rulerEl) return;

  rulerEl.innerHTML = '';
  for (const label of labels) {
    const span = document.createElement('span');
    span.textContent = label;
    rulerEl.appendChild(span);
  }
}

function updatePreviewRulers(data) {
  const preview = data?.preview || {};
  const settings = data?.attributes?.settings || {};
  const axis = data?.axis || {};

  const mode = normalizePreviewFitMode(currentPreviewFitMode);

  let xMin;
  let xMax;
  let yMin;
  let yMax;

  if (mode === 'bed') {
    xMin = 0;
    yMin = 0;
    xMax = axis?.x?.max_travel_mm ?? settings.x_max_travel;
    yMax = axis?.y?.max_travel_mm ?? settings.y_max_travel;
  } else {
    xMin = preview.min_x_mm;
    yMin = preview.min_y_mm;
    xMax = preview.max_x_mm;
    yMax = preview.max_y_mm;
  }

  setRulerLabels(topRuler, buildRulerLabels(xMin, xMax, 5));
  setRulerLabels(leftRuler, buildRulerLabels(yMin, yMax, 5));
}

function updateSetupWarning(configStatus) {
  const configured = configStatus?.configured !== false;
  const missing = Array.isArray(configStatus?.missing) ? configStatus.missing : [];

  if (!setupWarning || !dashboardGrid || !setupMissingList) return;

  setupWarning.hidden = configured || setupWarningDismissed;

  // Safety lock remains active until setup is actually complete.
  dashboardGrid.classList.toggle('configuration-blocked', !configured);

  setupMissingList.innerHTML = '';

  for (const item of missing) {
    const li = document.createElement('li');
    li.textContent = item;
    setupMissingList.appendChild(li);
  }
}

function normalizeBridgeBadgeValue(value) {
  if (!value) return 'Unknown';

  if (typeof value === 'object') {
    return value.status_text || value.bridge_status || value.status || 'Unknown';
  }

  const text = String(value).trim();

  if (text.startsWith('{')) {
    try {
      const parsed = JSON.parse(text);
      return parsed.status_text || parsed.bridge_status || parsed.status || 'Unknown';
    } catch (error) {
      return 'Unknown';
    }
  }

  return text;
}

function setBadge(value) {
  const displayValue = normalizeBridgeBadgeValue(value);
  const normalized = String(displayValue || 'unknown').toLowerCase();

  bridgeBadge.classList.remove('online', 'offline', 'unknown');
  bridgeBadge.classList.add(
    normalized === 'online' || normalized === 'idle'
      ? 'online'
      : normalized === 'offline' || normalized === 'not_configured'
        ? 'offline'
        : 'unknown'
  );

  bridgeBadge.querySelector('strong').textContent =
    normalized === 'not_configured' ? 'Needs setup' : displayValue || 'Unknown';
}

function showResult(payload, isError = false) {
  if (!lastResult) return;

  lastResult.classList.toggle('error', isError || payload?.ok === false);
  lastResult.textContent = typeof payload === 'string' ? payload : JSON.stringify(payload);
}

async function postCommand(payload) {
  showResult({ queued: true, ...payload });

  const response = await fetch('api/command', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok || data.ok === false) {
    showResult(data, true);
  }

  return data;
}


function syncJogHeightToPreview() {
  const previewCard = document.querySelector('.preview-card');
  const axisControls = document.querySelector('.axis-controls');

  if (!previewCard || !axisControls) return;

  if (window.matchMedia('(min-width: 1101px)').matches) {
    const previewHeight = Math.round(previewCard.getBoundingClientRect().height);
    const jogHeight = Math.round(previewHeight * 0.70);
    if (jogHeight > 0) {
      axisControls.style.height = `${jogHeight}px`;
    }
  } else {
    axisControls.style.height = '';
  }
}

window.addEventListener('resize', syncJogHeightToPreview);


function syncPlaceholderHeightToMachine() {
  const machineCard = document.querySelector('.machine-card');
  const placeholderCard = document.querySelector('.placeholder-card');

  if (!machineCard || !placeholderCard) return;

  if (window.matchMedia('(min-width: 1101px)').matches) {
    const machineHeight = Math.round(machineCard.getBoundingClientRect().height);
    if (machineHeight > 0) {
      placeholderCard.style.height = `${machineHeight}px`;
    }
  } else {
    placeholderCard.style.height = '';
  }
}

window.addEventListener('resize', syncPlaceholderHeightToMachine);

function refreshPreviewImage(force = false) {
  const hasPreviewLoaded = previewFrame.classList.contains('has-image');

  if (!force && !hasPreviewLoaded) {
    return;
  }

  if (force) {
    previewImage.src = `api/preview.png?v=${Date.now()}`;
    return;
  }

  const nextStamp = String(Date.now()).slice(0, -4);
  if (nextStamp !== lastPreviewStamp) {
    lastPreviewStamp = nextStamp;
    previewImage.src = `api/preview.png?v=${Date.now()}`;
  }
}

function getSelectedPath() {
  return rdPath.value.trim();
}

function safeControllerFilename(name) {
  const cleaned = String(name || '').trim().replace(/[^A-Za-z0-9_.-]/g, '');
  if (!cleaned) return '';
  return cleaned.toLowerCase().endsWith('.rd') ? cleaned : `${cleaned}.rd`;
}

function normalizeControllerFilePath(name) {
  const safeName = safeControllerFilename(name);
  if (!safeName) return '';
  return `/homeassistant/www/ruida_bridge/downloads/${safeName}`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForDownloadResult(slot, attempts = 30) {
  for (let i = 0; i < attempts; i += 1) {
    await sleep(1000);

    const response = await fetch(`api/state?t=${Date.now()}`);
    const data = await response.json().catch(() => ({}));
    const result = data.last_result || {};

    if (result.cmd === 'download_file' && Number(result.slot) === Number(slot)) {
      showResult(result, result.ok === false);
      return result;
    }
  }

  const timeout = { ok: false, cmd: 'download_file', slot, error: 'download_timeout' };
  showResult(timeout, true);
  return timeout;
}

async function downloadSelectedFile(file) {
  if (!file || file.slot === undefined || file.slot === null) {
    return { ok: false, error: 'file_slot_required' };
  }

  const queued = await postCommand({
    cmd: 'download_file',
    slot: Number(file.slot),
    name: file.name || '',
  });

  if (queued?.ok === false) {
    return queued;
  }

  return waitForDownloadResult(file.slot);
}

function updateSelectedRowHighlight() {
  for (const row of filesTableBody.querySelectorAll('tr')) {
    row.classList.toggle('selected', Number(row.dataset.slot) === Number(selectedFile?.slot));
  }
}

function selectFile(file, options = {}) {
  const { updatePath = true } = options;

  selectedFile = file;
  selectedFileName.textContent = file?.name || 'None';

  if (updatePath) {
    const path = file?.path || normalizeControllerFilePath(file?.name);
    if (path) {
      rdPath.value = path;
      userEditedPreviewPath = false;
    }
  }

  updateSelectedRowHighlight();
}

function renderFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    filesTableBody.innerHTML = '<tr class="empty-row"><td colspan="3">No file data loaded.</td></tr>';
    return;
  }

  filesTableBody.innerHTML = '';

  for (const file of files) {
    const row = document.createElement('tr');
    row.dataset.slot = file.slot ?? `local-${file.name ?? ''}`;
    const sourceLabel = file.source === 'local' ? 'local' : String(file.slot ?? '').padStart(3, '0');
    row.innerHTML = `
      <td>${sourceLabel}</td>
      <td class="file-name">${file.name ?? ''}</td>
      <td>${file.runtime_text ?? ''}</td>
    `;
    row.addEventListener('click', async () => {
      selectFile(file, { updatePath: true });

      if (file.source !== 'local') {
        const download = await downloadSelectedFile(file);
        if (download?.ok === false) return;
      }

      await renderSelectedFile();
    });
    filesTableBody.appendChild(row);
  }

  // Do not auto-fill Preview File Path on startup.
  // File clicks still populate the path through selectFile(file, { updatePath: true }).
  if (!selectedFile && files.length > 0) {
    updateSelectedRowHighlight();
    return;
  }

  if (selectedFile) {
    const match = files.find((file) => {
      if (selectedFile.source === 'local') {
        return file.source === 'local' && file.name === selectedFile.name;
      }
      return Number(file.slot) === Number(selectedFile.slot);
    });
    if (match) {
      selectedFile = match;
      selectedFileName.textContent = match?.name || 'None';
    }
  }

  updateSelectedRowHighlight();
}

async function renderSelectedFile() {
  const path = getSelectedPath();

  if (!path) {
    showResult({ ok: false, error: 'preview_path_required' }, true);
    return { ok: false, error: 'preview_path_required' };
  }

  const result = await postCommand({
    cmd: 'render_rd',
    path,
    fit_mode: currentPreviewFitMode,
  });

  if (result?.ok !== false) {
    setTimeout(() => refreshPreviewImage(true), 750);
  }

  return result;
}

function setRotaryDiameterControlsEnabled(enabled) {
  const disabled = !enabled;

  if (rotaryDiameter) {
    rotaryDiameter.disabled = disabled;
    rotaryDiameter.classList.toggle('disabled', disabled);
    rotaryDiameter.title = disabled ? 'Enable rotary before changing diameter' : '';
  }

  if (setRotaryDiameter) {
    setRotaryDiameter.disabled = disabled;
    setRotaryDiameter.classList.toggle('disabled', disabled);

    if (disabled) {
      setRotaryDiameter.classList.remove('synced', 'dirty');
      setRotaryDiameter.title = 'Enable rotary before setting diameter';
    }
  }
}

function updateRotarySetButtonState() {
  if (!setRotaryDiameter || !rotaryDiameter) return;

  if (setRotaryDiameter.disabled || rotaryDiameter.disabled) {
    setRotaryDiameter.classList.remove('synced', 'dirty');
    return;
  }

  const typedValue = Number(rotaryDiameter.value);
  const machineValue = currentRotaryDiameter;

  const synced = (
    Number.isFinite(typedValue)
    && Number.isFinite(machineValue)
    && Math.abs(typedValue - machineValue) < 0.005
  );

  setRotaryDiameter.classList.toggle('synced', synced);
  setRotaryDiameter.classList.toggle('dirty', !synced);

  if (Number.isFinite(machineValue)) {
    setRotaryDiameter.title = synced
      ? `Diameter matches machine: ${machineValue.toFixed(2)} mm`
      : `Machine diameter: ${machineValue.toFixed(2)} mm`;
  } else {
    setRotaryDiameter.title = 'Machine diameter unknown';
  }
}

function parseRotaryEnabled(value) {
  const normalized = String(value || '').trim().toUpperCase();
  return normalized === 'ON' || normalized === 'TRUE' || normalized === 'ENABLED' || normalized === '1';
}

function getRotaryDiameterFromState(data) {
  const candidates = [
    data?.attributes?.settings?.diameter,
    data?.attributes?.settings?.rotary_diameter,
    data?.last_result?.diameter_mm,
  ];

  for (const candidate of candidates) {
    if (candidate !== null && candidate !== undefined && !Number.isNaN(Number(candidate))) {
      return Number(candidate);
    }
  }

  return null;
}

const UNUSED_MACHINE_SETTINGS = [
  { key: 'focus_distance', label: 'Focus distance', unit: 'mm' },
  { key: 'x_max_speed', label: 'X max speed', unit: 'mm/s' },
  { key: 'x_max_travel', label: 'X max travel', unit: 'mm' },
  { key: 'x_home_offset', label: 'X home offset', unit: 'mm' },
  { key: 'y_max_speed', label: 'Y max speed', unit: 'mm/s' },
  { key: 'y_max_travel', label: 'Y max travel', unit: 'mm' },
  { key: 'y_home_offset', label: 'Y home offset', unit: 'mm' },
  { key: 'z_max_speed', label: 'Z max speed', unit: 'mm/s' },
  { key: 'z_max_travel', label: 'Z max travel', unit: 'mm' },
  { key: 'z_home_offset', label: 'Z home offset', unit: 'mm' },
  { key: 'laser_1_minimum_power', label: 'Laser 1 min power', unit: '%' },
  { key: 'laser_1_maximum_power', label: 'Laser 1 max power', unit: '%' },
  { key: 'laser_1_frequency', label: 'Laser 1 frequency', unit: 'Hz' },
  { key: 'laser_2_minimum_power', label: 'Laser 2 min power', unit: '%' },
  { key: 'laser_2_maximum_power', label: 'Laser 2 max power', unit: '%' },
  { key: 'laser_2_frequency', label: 'Laser 2 frequency', unit: 'Hz' },
];

function formatUnusedSettingValue(value, unit = '') {
  if (value === null || value === undefined || value === '') {
    return 'unknown';
  }

  const num = Number(value);
  let text = String(value);

  if (!Number.isNaN(num)) {
    const digits = unit === 'Hz'
      ? 0
      : (Math.abs(num - Math.round(num)) < 0.005 ? 0 : 2);
    text = num.toFixed(digits);
  }

  return unit ? `${text} ${unit}` : text;
}

function updateLaserSwitch(toggleEl, stateEl, laserData) {
  if (!toggleEl || !stateEl) return;

  const enabled = Boolean(
    laserData?.enabled === true
    || String(laserData?.state || '').trim().toUpperCase() === 'ON'
  );

  toggleEl.checked = enabled;
  stateEl.textContent = enabled ? 'ON' : 'OFF';
  stateEl.classList.toggle('on', enabled);
  stateEl.classList.toggle('off', !enabled);
}

function renderUnusedSettings(settings) {
  if (!unusedSettingsList) return;

  const items = UNUSED_MACHINE_SETTINGS.filter(item => item.key !== 'diameter');

  if (!settings || typeof settings !== 'object') {
    unusedSettingsList.innerHTML = '<div class="unused-settings-empty">No machine settings loaded.</div>';
    return;
  }

  unusedSettingsList.innerHTML = '';

  for (const item of items) {
    const row = document.createElement('div');
    row.className = 'unused-setting-row';
    row.innerHTML = `
      <span class="unused-setting-label">${item.label}</span>
      <span class="unused-setting-value">${formatUnusedSettingValue(settings[item.key], item.unit)}</span>
    `;
    unusedSettingsList.appendChild(row);
  }
}

async function loadState() {
  const response = await fetch(`api/state?t=${Date.now()}`);
  const data = await response.json();

  setBadge(data.bridge || 'unknown');

  versionPill.textContent = data.app_version ? `v${data.app_version}` : 'v—';
  updateSetupWarning(data.config_status);
  machineState.textContent = data.attributes?.status_text || 'unknown';

  const x = data.axis?.x?.position_mm ?? data.attributes?.x_mm;
  const y = data.axis?.y?.position_mm ?? data.attributes?.y_mm;
  const z = data.axis?.z?.position_mm ?? data.attributes?.z_mm;

  if (positionState) {
    if (x !== undefined && y !== undefined && z !== undefined) {
      positionState.innerHTML = `<span class="position-group"><span class="position-number">${formatNumber(x)}</span><span class="axis-label">x</span>,</span><span class="position-group"><span class="position-number">${formatNumber(y)}</span><span class="axis-label">y</span>,</span><span class="position-group"><span class="position-number">${formatNumber(z)}</span><span class="axis-label">z</span></span>`;
    } else if (x !== undefined && y !== undefined) {
      positionState.innerHTML = `<span class="position-group"><span class="position-number">${formatNumber(x)}</span><span class="axis-label">x</span>,</span><span class="position-group"><span class="position-number">${formatNumber(y)}</span><span class="axis-label">y</span>,</span><span class="position-group"><span class="position-number">unknown</span><span class="axis-label">z</span></span>`;
    } else {
      positionState.textContent = 'unknown';
    }
  }
  const rotaryEnabled = parseRotaryEnabled(data.rotary);
  if (rotaryState) {
    rotaryState.textContent = rotaryEnabled ? 'ON' : 'OFF';
    rotaryState.classList.toggle('on', rotaryEnabled);
    rotaryState.classList.toggle('off', !rotaryEnabled);
  }

  if (rotaryToggle) {
    rotaryToggle.checked = rotaryEnabled;
  }

  setRotaryDiameterControlsEnabled(rotaryEnabled);

  const diameter = getRotaryDiameterFromState(data);
  currentRotaryDiameter = diameter;

  if (rotaryDiameter && document.activeElement !== rotaryDiameter) {
    if (diameter !== null) {
      rotaryDiameter.value = diameter.toFixed(2);
    }
  }

  updateRotarySetButtonState();

  updateLaserSwitch(laser1Toggle, laser1State, data.laser?.['1'] || {});
  updateLaserSwitch(laser2Toggle, laser2State, data.laser?.['2'] || {});
  renderUnusedSettings(data.attributes?.settings || {});

  const preview = data.preview || {};
  updatePreviewFitUi(currentPreviewFitMode);
  updatePreviewRulers(data);

  if (previewFrame.classList.contains('has-image') && preview.file_name) {
    previewTitle.textContent = preview.file_name;
    previewSize.textContent = `${formatDimension(preview.width_mm)} mm × ${formatDimension(preview.height_mm)} mm`;
  } else if (!previewFrame.classList.contains('has-image')) {
    previewTitle.textContent = 'No preview loaded';
    previewSize.textContent = '— mm × — mm';
  }

  renderFiles(data.file_list || []);
  syncJogHeightToPreview();
  syncPlaceholderHeightToMachine();

  if (data.last_result && Object.keys(data.last_result).length > 0) {
    showResult(data.last_result);
  }
}


if (dismissSetupWarning) {
  dismissSetupWarning.addEventListener('click', () => {
    setupWarningDismissed = true;
    localStorage.setItem('ruidaSetupWarningDismissed', 'true');
    if (setupWarning) {
      setupWarning.hidden = true;
    }
  });
}

rdPath.addEventListener('input', () => {
  userEditedPreviewPath = true;
});

for (const button of document.querySelectorAll('[data-action]')) {
  button.addEventListener('click', () => postCommand({ cmd: button.dataset.action }));
}

const refreshAll = document.getElementById('refreshAll');
if (refreshAll) {
  refreshAll.addEventListener('click', () => {
    loadState();
setTimeout(syncJogHeightToPreview, 250);
setTimeout(syncPlaceholderHeightToMachine, 250);
    if (previewFrame.classList.contains('has-image')) {
      refreshPreviewImage(true);
    }
  });
}

document.getElementById('useSelected').addEventListener('click', async () => {
  await renderSelectedFile();
});

if (previewFitToggle) {
  previewFitToggle.addEventListener('change', async () => {
    const nextMode = previewFitToggle.checked ? 'bed' : 'geometry';
    updatePreviewFitUi(nextMode);

    if (getSelectedPath()) {
      await renderSelectedFile();
    }
  });
}

if (rotaryToggle) {
  rotaryToggle.addEventListener('change', async () => {
    await postCommand({
      cmd: 'set_rotary_enabled',
      enabled: rotaryToggle.checked,
    });
    setTimeout(loadState, 750);
  });
}

if (setRotaryDiameter && rotaryDiameter) {
  setRotaryDiameter.addEventListener('click', async () => {
    const value = Number(rotaryDiameter.value);

    if (!Number.isFinite(value) || value <= 0) {
      showResult({ ok: false, error: 'invalid_rotary_diameter' }, true);
      return;
    }

    await postCommand({
      cmd: 'set_rotary_diameter',
      diameter_mm: value,
    });
    setTimeout(loadState, 1000);
  });

  rotaryDiameter.addEventListener('keydown', async (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      setRotaryDiameter.click();
    }
  });

  rotaryDiameter.addEventListener('input', updateRotarySetButtonState);
}

previewImage.addEventListener('load', () => previewFrame.classList.add('has-image'));
previewImage.addEventListener('error', () => previewFrame.classList.remove('has-image'));

loadState();
setInterval(loadState, 2000);
setInterval(() => refreshPreviewImage(false), 12000);