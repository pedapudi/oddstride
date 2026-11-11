import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {RoomEnvironment} from './vendor/RoomEnvironment.js';
import {createCADGeometry} from './cad-shading.js';

const $ = id => document.getElementById(id);
const query = new URLSearchParams(location.search);
const state = {mode: query.get('mode') || 'robot', design: null, data: null, audit: null,
  objects: [], ghosts: [], selected: null, q: null, playing: false, checkSequence: 0, liveAvailable: false};
const scene = new THREE.Scene();
scene.background = new THREE.Color('#e8ece2');
const renderer = new THREE.WebGLRenderer({antialias: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.localClippingEnabled = true;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.92;
$('viewport').append(renderer.domElement);
const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 6000);
camera.up.set(0, 0, 1);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.05).texture;
scene.add(new THREE.HemisphereLight('#ffffff', '#73806b', 1.6));
const light = new THREE.DirectionalLight('#fff8ec', 2);
light.position.set(400, -500, 700); scene.add(light);
const sectionPlane = new THREE.Plane();
let robotBounds = new THREE.Box3(), catalog, loadSequence = 0, appearance = null;
const referenceModels = new Map();

function renderColor(part) {
  if (!appearance || isReservation(part)) return part.color;
  if (part.material === 'steel') return appearance.colors.metal;
  if (part.appearance_role && appearance.colors[part.appearance_role]) return appearance.colors[part.appearance_role];
  const rule = appearance.rules.find(rule => new RegExp(rule.pattern).test(part.name + ' ' + part.mesh));
  return appearance.colors[rule?.role || appearance.material_defaults[part.material]] || part.color;
}

function copyPose(q) { return structuredClone(q); }
function translation(x = 0, y = 0, z = 0) { return new THREE.Matrix4().makeTranslation(x, y, z); }
function rotation(axis, angle) {
  const a = angle * Math.PI / 180;
  return axis === 'x' ? new THREE.Matrix4().makeRotationX(a) : new THREE.Matrix4().makeRotationY(a);
}
function partFrame(p, q = state.q) {
  if (!p.leg) return new THREE.Matrix4();
  const front = p.leg[0] === 'F' ? 1 : -1, side = p.leg[1] === 'L' ? 1 : -1;
  const [roll, hip, knee] = q[p.leg], P = state.data.parameters;
  const mount = translation(front * P.hip_x, side * P.roll_y);
  const rolled = mount.clone().multiply(rotation('x', side * roll));
  const thigh = rolled.clone().multiply(translation(front * (P.pitch_x_offset || 0), side * P.pitch_offset)).multiply(rotation('y', hip));
  if (p.group === 'mount') return mount;
  if (p.group === 'roll') return rolled;
  if (p.group === 'thigh') return thigh;
  if (p.group === 'knee') return thigh.clone().multiply(translation(0, 0, -P.thigh)).multiply(rotation('y', knee));
  const crankAngle = knee + P.crank_phase_deg;
  if (p.group === 'crank') return thigh.clone().multiply(rotation('y', crankAngle));
  if (p.group === 'rod') return thigh.clone().multiply(translation(P.crank_radius * Math.cos(crankAngle * Math.PI / 180), 0, -P.crank_radius * Math.sin(crankAngle * Math.PI / 180)));
  return mount;
}
function makeObjects(data, ghost = false) {
  const geometries = new Map();
  return data.parts.map(p => {
    if (!geometries.has(p.mesh)) {
      const geometry = createCADGeometry(data.meshes[p.mesh]);
      geometries.set(p.mesh, geometry);
    }
    const color = renderColor(p);
    const material = new THREE.MeshStandardMaterial({color: ghost ? '#557767' : color,
      metalness: ['steel', 'aluminum'].includes(p.material) ? 0.4 : 0.03,
      roughness: 0.43, side: THREE.DoubleSide, wireframe: ghost,
      transparent: ghost, opacity: ghost ? 0.13 : 1, depthWrite: !ghost});
    const object = new THREE.Mesh(geometries.get(p.mesh), material);
    object.userData = {...p, color}; object.matrixAutoUpdate = false; scene.add(object);
    return object;
  });
}
function disposeObjects(objects) {
  const geometries = new Set();
  for (const object of objects) { scene.remove(object); object.material.dispose(); geometries.add(object.geometry); }
  geometries.forEach(g => g.dispose());
}
function isReservation(p) { return ['keepout', 'withdrawal'].includes(p.service_role); }
function isActuator(p) { return /_(roll|hip|knee)_motor$/.test(p.name); }
function showInventory(design, data) {
  const physical = data.parts.filter(p => !isReservation(p));
  const motors = physical.filter(isActuator).length;
  const limbs = new Set(physical.map(p => p.leg).filter(Boolean)).size;
  const primary = [design.scope_label || 'Whole robot'];
  if (design.presentation !== 'motor-complex' && limbs) primary.push(`${limbs} limbs`);
  primary.push(`${motors} actuators`);
  if (Number.isFinite(design.estimated_mass_kg)) primary.push(`${design.estimated_mass_kg.toFixed(2)} kg estimated mass`);
  $('design-metrics').textContent = primary.join(' · ');
  const custom = design.parts.filter(p => p.custom);
  const instances = custom.reduce((n, p) => n + p.quantity, 0);
  const customMeshes = new Set(custom.map(p => p.id));
  const definitions = new Set(physical.filter(p => customMeshes.has(p.mesh) && p.native_definition_id).map(p => p.native_definition_id)).size;
  const connectors = physical.filter(p => p.name.includes('_port_')).length;
  const counts = [[definitions ? 'Native CAD definitions' : 'Custom library entries', `${definitions || custom.length} definitions · ${instances} placed instances`],
    ['Actuators', motors], ['Connector representation entries', connectors],
    ['Other hardware and reference entries', physical.length - motors - connectors - instances],
    ['Physical/reference CAD entries', physical.length],
    ['Auxiliary clearance entries', data.parts.length - physical.length]];
  $('inventory-counts').replaceChildren();
  for (const [label, value] of counts) {
    const dt = document.createElement('dt'), dd = document.createElement('dd');
    dt.textContent = label; dd.textContent = value; $('inventory-counts').append(dt, dd);
  }
}
function actuatorName(p) {
  return p.name.endsWith('_roll_motor') ? '1 · Hip roll' : p.name.endsWith('_hip_motor') ? '2 · Hip pitch' : '3 · Knee pitch';
}
const actuatorLabels = new Map();
function drawActuatorLabels() {
  const enabled = $('actuators-only').checked && state.mode !== 'parts';
  $('actuator-labels').hidden = !enabled; $('actuator-count').hidden = !enabled;
  if (!enabled) return;
  const motors = state.objects.filter(o => o.visible && isActuator(o.userData));
  $('actuator-count').textContent = `${motors.length} actuators shown · three per limb. Gray bearing housings are separate structural parts.`;
  for (const node of actuatorLabels.values()) node.hidden = true;
  const width = $('viewport').clientWidth, height = $('viewport').clientHeight;
  for (const object of motors) {
    const p = object.userData;
    let node = actuatorLabels.get(p.name);
    if (!node) { node = document.createElement('span'); $('actuator-labels').append(node); actuatorLabels.set(p.name, node); }
    node.textContent = `${actuatorName(p)}${$('assembly-focus').value === 'all' && p.leg ? ' · ' + p.leg : ''}`;
    const center = new THREE.Vector3(...p.com_mm).applyMatrix4(object.matrixWorld).project(camera);
    node.hidden = center.z > 1 || center.z < -1;
    node.style.left = `${(center.x + 1) * width / 2}px`; node.style.top = `${(1 - center.y) * height / 2}px`;
  }
}
function isOuterShell(p) {
  return ['body_center_0', 'body_nose_surround', 'front_fascia', 'sensor_bezel', 'sensor_window'].includes(p.name)
    || /_(thigh_outer|shin_outer)$/.test(p.name);
}
function focusAllows(p) {
  const focus = $('assembly-focus').value;
  return focus === 'all' || (focus === 'chassis' ? !p.leg || p.group === 'mount' : p.leg === focus);
}
function recordFor(key) { return state.design.parts.find(p => p.id === key); }
function labelFor(name) {
  const p = state.data.parts.find(p => p.name === name);
  return p ? `${recordFor(p.mesh)?.label || name.replaceAll('_', ' ')}${p.leg ? ' · ' + p.leg : ''}` : name;
}
function updateGeometry() {
  if (!state.data) return;
  const partMode = state.mode === 'parts', isolate = state.selected?.mesh;
  let isolated = false;
  for (const object of state.objects) {
    const p = object.userData, reservation = isReservation(p);
    let visible = reservation ? $('reservations').checked : true;
    if (!partMode && !focusAllows(p)) visible = false;
    if (!partMode && $('actuators-only').checked && !isActuator(p)) visible = false;
    if ($('open-shells').checked && isOuterShell(p) && !partMode) visible = false;
    if (partMode) { visible = p.mesh === isolate && !isolated; if (visible) isolated = true; }
    object.visible = visible;
    object.matrix.copy(partMode ? new THREE.Matrix4() : partFrame(p));
    object.matrixWorldNeedsUpdate = true;
    object.material.transparent = reservation;
    object.material.opacity = reservation ? 0.16 : 1;
    object.material.depthWrite = !reservation;
    object.material.emissive.set(p.name === state.selected?.name && !partMode ? '#172c1d' : '#000000');
    object.material.clippingPlanes = $('section').checked ? [sectionPlane] : [];
  }
  for (const object of state.ghosts) {
    object.visible = $('ghost').checked && !partMode && !$('actuators-only').checked && !isReservation(object.userData);
    if (!focusAllows(object.userData)) object.visible = false;
    object.matrix.copy(partFrame(object.userData)); object.matrixWorldNeedsUpdate = true;
    object.material.clippingPlanes = $('section').checked ? [sectionPlane] : [];
  }
  scene.updateMatrixWorld(true);
  updateSection();
}
function visibleBounds() {
  const bounds = new THREE.Box3();
  for (const object of state.objects) if (object.visible && !isReservation(object.userData)) bounds.expandByObject(object);
  return bounds.isEmpty() ? robotBounds.clone() : bounds;
}
function updateSection() {
  const axis = $('section-axis').value, bounds = state.mode === 'parts' ? visibleBounds() : robotBounds;
  const position = THREE.MathUtils.lerp(bounds.min[axis], bounds.max[axis], Number($('section-position').value) / 100);
  const normal = new THREE.Vector3(); normal[axis] = -1;
  sectionPlane.set(normal, position);
}
function fit(view = 'iso', selectionOnly = false) {
  let bounds = visibleBounds();
  if (selectionOnly && state.selected) {
    const object = state.objects.find(o => o.userData.name === state.selected.name);
    if (object) bounds = new THREE.Box3().setFromObject(object);
  }
  const center = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3());
  const span = Math.max(size.x, size.y, size.z, 30), distance = span / (2 * Math.tan(camera.fov * Math.PI / 360)) * 1.45;
  const direction = {iso: [0.65, -1, 0.6], front: [1, 0, 0], side: [0, -1, 0], top: [0, 0, 1]}[view];
  camera.up.set(...(view === 'top' ? [0, 1, 0] : [0, 0, 1]));
  camera.position.copy(center).add(new THREE.Vector3(...direction).normalize().multiplyScalar(distance));
  controls.target.copy(center); controls.update();
}
function clearColors() { for (const object of state.objects) object.material.color.set(object.userData.color); }
function showStatus(title, detail, kind = 'unchecked', pairs = []) {
  state.lastStatus = [title, detail, kind, pairs];
  $('clearance-title').textContent = title; $('clearance-detail').textContent = detail;
  $('clearance').dataset.state = kind; $('collision-list').replaceChildren(); clearColors();
  const hits = new Set(pairs.flat());
  for (const object of state.objects) if ($('collision-paint').checked && hits.has(object.userData.name)) object.material.color.set(appearance?.colors.interference || '#B73882');
  for (const pair of pairs.slice(0, 8)) {
    const item = document.createElement('li'); item.textContent = pair.map(labelFor).join(' ↔ '); $('collision-list').append(item);
  }
  if (pairs.length > 8) { const item = document.createElement('li'); item.textContent = `${pairs.length - 8} more pairs are recorded in the check results.`; $('collision-list').append(item); }
}
function equalPose(a, b) { return ['FL', 'FR', 'RL', 'RR'].every(leg => a[leg].every((v, i) => Math.abs(v - b[leg][i]) < 1e-7)); }
function isReferenceReview() { return state.design.source?.kind === 'generated-reference' && (state.design.archived || state.design.lifecycle === 'reference-only'); }
function showPoseStatus() {
  if (state.mode === 'parts') { showStatus('Individual part', 'Dimensions describe this part in its local CAD axes. Assembly clearance is evaluated in the robot view.'); return; }
  if (state.design.presentation === 'motor-complex') { showStatus('Static motor-complex review', state.design.scope); return; }
  if (state.playing) { showStatus('Motion preview', 'Intermediate frames have not been checked. Pause the animation to check the displayed pose.'); return; }
  const sample = state.audit.motion_samples.find(p => equalPose(p.angles, state.q));
  if (!sample) { showStatus('Pose not checked', 'Use “Check this pose” to evaluate the displayed joint positions.'); return; }
  if (isReferenceReview()) {
    showStatus(sample.hits.length ? `${sample.hits.length} reference interference pairs` : 'Historical pose result',
      'This reference predates native assembly corrections. Its motion check excludes fixed assembly interfaces and does not qualify their fit.', sample.hits.length ? 'collision' : 'unchecked', sample.hits);
    return;
  }
  if (state.design.clearance_scope === 'motion-only') {
    showStatus(sample.hits.length ? `${sample.hits.length} interference pairs in this sampled pose` : 'Sampled motion result',
      'Moving rigid-part check. Fixed assembly contacts and documented design limitations require their separate solid reviews.', sample.hits.length ? 'collision' : 'unchecked', sample.hits);
    return;
  }
  showStatus(sample.hits.length ? `${sample.hits.length} interference pairs in this sampled pose` : 'No reported interference in this sampled pose',
    'Sampled rigid-part check. Flexible cables, manufacturing tolerances, deflection and loaded motion are not validated.', sample.hits.length ? 'collision' : 'clear', sample.hits);
}
function syncControls() {
  if (state.design.motion_available === false) return;
  const leg = $('leg').value === 'all' ? 'FL' : $('leg').value, q = state.q[leg];
  const limits = state.data.parameters.joint_limits_deg;
  const hipLimits = $('leg').value === 'all' ? [Math.max(limits.hip_front[0], limits.hip_rear[0]), Math.min(limits.hip_front[1], limits.hip_rear[1])] : leg.startsWith('F') ? limits.hip_front : limits.hip_rear;
  for (const [i, id, range] of [[0, 'roll', limits.roll], [1, 'hip', hipLimits], [2, 'knee', limits.knee]]) {
    $(id).min = range[0]; $(id).max = range[1]; $(id).value = q[i]; $(id + '-value').textContent = q[i].toFixed(1) + '°';
  }
}
function stopAnimation() { state.playing = false; $('play').textContent = 'Play stance transition'; }
function setMode(mode) {
  if (!['robot', 'motion', 'parts'].includes(mode)) mode = 'robot';
  if (mode === 'motion' && state.design?.motion_available === false) mode = 'robot';
  stopAnimation(); state.mode = mode; state.checkSequence++;
  for (const button of document.querySelectorAll('[data-mode]')) { const active = button.dataset.mode === mode; button.classList.toggle('active', active); button.setAttribute('aria-pressed', active); }
  $('robot-tools').hidden = mode === 'parts'; $('motion-tools').hidden = mode !== 'motion'; $('parts-tools').hidden = mode !== 'parts';
  if (mode === 'parts' && !state.selected) selectPart($('part').value, false);
  updateGeometry(); showPoseStatus(); fit(); updateUrl();
}
function updateUrl() {
  const params = new URLSearchParams({design: state.design.id, mode: state.mode});
  if ($('assembly-focus').value !== 'all') params.set('focus', $('assembly-focus').value);
  if (state.mode === 'parts' && state.selected) params.set('part', state.selected.mesh);
  if ($('actuators-only').checked && state.mode !== 'parts') params.set('actuators', '1');
  if ($('show-archived').checked) params.set('archive', '1');
  history.replaceState(null, '', '?' + params.toString());
}
function populateParts() {
  const search = $('search').value.toLowerCase(), category = $('category').value;
  const previous = $('part').value;
  const rows = state.design.parts.filter(p => (category === 'all' || category === 'custom' && p.custom || p.category === category) && (p.label + ' ' + p.id).toLowerCase().includes(search));
  $('part').replaceChildren(...rows.map(p => { const o = new Option(`${p.label} · Qty ${p.quantity}`, p.id); return o; }));
  if (rows.some(p => p.id === previous)) $('part').value = previous;
}
function selectPart(key, focus = true) {
  const record = recordFor(key); if (!record) return;
  state.selected = state.data.parts.find(p => p.name === record.instances[0]);
  $('selection').hidden = false; $('part-title').textContent = record.label;
  $('part-facts').replaceChildren();
  const facts = [['Material', record.material === 'petg' ? 'PETG design basis' : record.material === 'envelope' ? 'Reference envelope' : record.material],
    ['Dimensions · X × Y × Z', record.dimensions_mm.map(v => v.toFixed(1)).join(' × ') + ' mm'],
    ['Mass per part', record.mass_kg > 0 ? (record.mass_kg * 1000).toFixed(1) + ' g' : 'Not estimated'], ['Quantity', record.quantity]];
  for (const [term, value] of facts) { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = term; dd.textContent = value; $('part-facts').append(dt, dd); }
  $('part-note').textContent = record.note || 'No manufacturing note is recorded for this reference component.';
  $('part-downloads').replaceChildren();
  for (const kind of ['step', 'stl', 'print_stl', 'print_3mf']) if (record[kind]) { const a = document.createElement('a'); a.href = record[kind]; a.className = 'button'; a.textContent = kind === 'print_stl' ? 'Oriented STL' : kind === 'print_3mf' ? 'Print preparation · 3MF' : kind.toUpperCase() + (state.design.source?.kind === 'generated-reference' ? ' · reference' : ''); $('part-downloads').append(a); }
  $('part').value = key; updateGeometry(); if (focus) fit('iso', state.mode !== 'parts'); updateUrl();
}
async function assetBytes(url) {
  const response = await fetch(url);
  if (!response.ok) throw Error(`Could not load ${url} (${response.status}).`);
  if (new URL(url, location.href).pathname.endsWith('.gz')) {
    return new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  }
  return response.arrayBuffer();
}
async function loadDesign(id) {
  const ticket = ++loadSequence; stopAnimation(); state.checkSequence++; $('loading').hidden = false; $('loading').textContent = 'Loading CAD geometry…';
  try {
    const design = catalog.designs.find(d => d.id === id) || catalog.designs.find(d => d.id === catalog.current_design) || catalog.designs[0];
    if (design.detail_url && !design.detail_loaded) {
      const decoded = await assetBytes(design.detail_url);
      const digest = await crypto.subtle.digest('SHA-256', decoded);
      const hash = [...new Uint8Array(digest)].map(v => v.toString(16).padStart(2, '0')).join('');
      if (hash !== design.detail_sha256) throw Error('The archived catalog does not match its recorded hash.');
      if (ticket !== loadSequence) return;
      Object.assign(design, JSON.parse(new TextDecoder().decode(decoded)), {detail_loaded: true});
    }
    const responses = await Promise.all([design.model, design.audit].map(assetBytes));
    if (ticket !== loadSequence) return;
    const digest = await crypto.subtle.digest('SHA-256', responses[0]);
    const modelHash = [...new Uint8Array(digest)].map(v => v.toString(16).padStart(2, '0')).join('');
    if (modelHash !== design.model_sha256) throw Error('The CAD file changed after this catalog was published. Refresh the geometry reports and republish the viewer.');
    const [data, audit] = responses.map(bytes => JSON.parse(new TextDecoder().decode(bytes)));
    if (audit.model_sha256 !== design.model_sha256) throw Error('The model and geometry report are from different exports. Republish the viewer catalog before reviewing clearance.');
    disposeObjects(state.objects); disposeObjects(state.ghosts); state.ghosts = [];
    state.design = design; state.data = data; state.audit = audit; state.q = copyPose(data.poses.stand); state.selected = null;
    if (!query.get('focus') && design.default_focus) $('assembly-focus').value = design.default_focus;
    if (design.archived) $('show-archived').checked = true;
    populateDesigns(design.id);
    state.objects = makeObjects(data); $('design').value = design.id;
    $('archive-notice').hidden = !design.archived;
    $('archive-note').textContent = design.archive_note || '';
    $('design-title').textContent = design.title; $('design-summary').textContent = design.description;
    $('geometry-source').textContent = design.source?.label || 'Generated CAD reference · native Fusion promotion pending';
    showInventory(design, data);
    $('assembly-focus').closest('label').hidden = design.presentation === 'motor-complex';
    if (design.presentation === 'motor-complex') $('assembly-focus').value = 'all';
    const motionButton = document.querySelector('[data-mode="motion"]');
    motionButton.disabled = design.motion_available === false;
    motionButton.title = motionButton.disabled ? 'This export supports static assembly and part inspection.' : '';
    $('check').disabled = !state.liveAvailable || design.live_check_available === false;
    $('scope-text').textContent = design.scope;
    $('assembly-download').hidden = !design.assembly;
    if (design.assembly) $('assembly-download').href = design.assembly;
    else $('assembly-download').removeAttribute('href');
    $('audit-download').href = design.audit;
    $('design-reports').replaceChildren(...(design.reports || []).map(report => {
      const row = document.createElement('p'), link = document.createElement('a');
      link.href = report.url; link.textContent = report.title; row.append(link); return row;
    }));
    $('selection').hidden = true; $('ghost').checked = false; $('ghost').disabled = design.id === 'v0' || design.presentation === 'motor-complex';
    $('actuators-only').checked = query.get('actuators') === '1';
    $('section').checked = false; $('section-tools').hidden = true;
    $('pose').replaceChildren(...Object.keys(data.poses).map(k => new Option(k.replaceAll('_', ' '), k)), new Option('Custom position', 'custom'));
    for (const sample of audit.motion_samples) if (!data.poses[sample.pose]) { data.poses[sample.pose] = sample.angles; $('pose').add(new Option(sample.pose.replace('sample_', 'Sample: ').replaceAll('_', ' / '), sample.pose)); }
    $('pose').value = 'stand'; populateParts(); syncControls(); updateGeometry(); robotBounds = visibleBounds();
    const desired = query.get('part'); if (desired && recordFor(desired)) selectPart(desired, false);
    setMode(state.mode); $('loading').hidden = true;
  } catch (error) { if (ticket === loadSequence) { $('loading').hidden = false; $('loading').textContent = error.message; } throw error; }
}
function populateDesigns(selectedId) {
  const active = catalog.designs.filter(d => !d.archived);
  $('design').replaceChildren(...active.map(d => new Option(d.title, d.id)));
  if ($('show-archived').checked) {
    const group = document.createElement('optgroup'); group.label = 'Archived proposals';
    group.append(...catalog.designs.filter(d => d.archived).slice().reverse().map(d => new Option(d.title, d.id)));
    $('design').append(group);
  }
  if (selectedId) $('design').value = selectedId;
}
async function checkPose() {
  if (!state.liveAvailable || state.playing || state.design.live_check_available === false) return;
  const ticket = ++state.checkSequence, design = state.design.id, modelHash = state.design.model_sha256, q = copyPose(state.q);
  showStatus('Checking this pose…', 'Evaluating the displayed rigid-part geometry.');
  try {
    const response = await fetch('/api/check', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({design, model_sha256: modelHash, poses: q})});
    if (!response.ok) { const failure = await response.json().catch(() => ({})); throw Error(failure.error || 'The local geometry check failed. The displayed pose remains unchecked.'); }
    const result = await response.json();
    if (ticket !== state.checkSequence || design !== state.design.id || !equalPose(q, state.q) || state.playing || state.mode === 'parts') return;
    if ((result.model_sha256 && result.model_sha256 !== modelHash) || (state.design.source?.kind === 'fusion-native' && result.model_sha256 !== modelHash)) throw Error('The check used different geometry. Reload the viewer before checking this pose.');
    if (isReferenceReview()) {
      showStatus(result.pairs.length ? `${result.pairs.length} reference interference pairs in this pose` : 'Reference result for this pose',
        'Historical geometry; fixed assembly interfaces are excluded and current native corrections are absent.', result.pairs.length ? 'collision' : 'unchecked', result.pairs);
      return;
    }
    if (state.design.clearance_scope === 'motion-only') {
      showStatus(result.pairs.length ? `${result.pairs.length} interference pairs in this pose` : 'Motion result for this pose',
        result.scope + ' Fixed assembly contacts and documented design limitations require separate solid reviews.', result.pairs.length ? 'collision' : 'unchecked', result.pairs);
      return;
    }
    showStatus(result.pairs.length ? `${result.pairs.length} interference pairs in this pose` : 'No reported interference in this pose', result.scope, result.pairs.length ? 'collision' : 'clear', result.pairs);
  } catch (error) { if (ticket === state.checkSequence) showStatus('Pose not checked', error.message); }
}

for (const button of document.querySelectorAll('[data-mode]')) button.onclick = () => setMode(button.dataset.mode);
for (const button of document.querySelectorAll('[data-view]')) button.onclick = () => fit(button.dataset.view);
$('design').onchange = () => loadDesign($('design').value).catch(console.error);
$('show-archived').onchange = () => {
  if (!$('show-archived').checked && state.design?.archived) {
    loadDesign(catalog.current_design).catch(console.error);
  } else { populateDesigns(state.design?.id); if (state.design) updateUrl(); }
};
$('open-current').onclick = () => {
  $('show-archived').checked = false; loadDesign(catalog.current_design).catch(console.error);
};
$('reset').onclick = () => fit(); $('fit-part').onclick = () => fit();
$('show-in-robot').onclick = () => { setMode('robot'); fit('iso', true); };
$('search').oninput = populateParts; $('category').onchange = populateParts;
$('part').onchange = () => selectPart($('part').value);
$('pose').onchange = () => { if ($('pose').value === 'custom') return; stopAnimation(); state.checkSequence++; state.q = copyPose(state.data.poses[$('pose').value]); syncControls(); updateGeometry(); showPoseStatus(); };
$('leg').onchange = syncControls;
for (const [i, id] of ['roll', 'hip', 'knee'].entries()) $(id).oninput = () => {
  stopAnimation(); state.checkSequence++; const legs = $('leg').value === 'all' ? ['FL', 'FR', 'RL', 'RR'] : [$('leg').value];
  for (const leg of legs) state.q[leg][i] = Number($(id).value);
  $('pose').value = 'custom'; syncControls(); updateGeometry(); showPoseStatus();
};
$('play').onclick = () => { if (state.playing) { stopAnimation(); showPoseStatus(); return; } state.checkSequence++; state.playing = true; state.playStart = performance.now(); $('play').textContent = 'Pause motion'; $('pose').value = 'custom'; showPoseStatus(); };
$('check').onclick = checkPose;
$('save-pose').onclick = () => { const url = URL.createObjectURL(new Blob([JSON.stringify({design: state.design.id, units: 'degrees', poses: state.q}, null, 2)], {type: 'application/json'})); const link = document.createElement('a'); link.href = url; link.download = `tinfox-${state.design.id}-pose.json`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); };
for (const id of ['open-shells', 'reservations', 'actuators-only', 'section', 'section-axis', 'section-position']) $(id).oninput = () => { $('section-tools').hidden = !$('section').checked; updateGeometry(); if (id === 'actuators-only') { fit(); updateUrl(); } };
$('ghost').onchange = async () => {
  if ($('ghost').checked && !state.ghosts.length) {
    const id = state.design.id;
    const referenceId = state.design.reference_design || 'v0';
    if (!referenceModels.has(referenceId)) referenceModels.set(referenceId, JSON.parse(new TextDecoder().decode(await assetBytes(catalog.designs.find(d => d.id === referenceId).model))));
    const referenceData = referenceModels.get(referenceId);
    if (state.design.id !== id || !$('ghost').checked) return;
    const changed = new Set(state.design.comparison_parts || ['body_center_0', 'thigh_inner', 'thigh_outer', 'shin_inner', 'shin_outer', 'motor_carrier_1', 'motor_carrier_-1']);
    state.ghosts = makeObjects({...referenceData, parts: referenceData.parts.filter(p => changed.has(p.mesh.replace(/_right$/, '')))}, true);
  }
  updateGeometry();
};
const ray = new THREE.Raycaster(); let pointerStart;
renderer.domElement.addEventListener('pointerdown', event => { pointerStart = [event.clientX, event.clientY]; });
renderer.domElement.addEventListener('pointerup', event => {
  if (!pointerStart || Math.hypot(event.clientX - pointerStart[0], event.clientY - pointerStart[1]) > 5) return;
  const bounds = renderer.domElement.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2((event.clientX - bounds.left) / bounds.width * 2 - 1, 1 - (event.clientY - bounds.top) / bounds.height * 2), camera);
  const hit = ray.intersectObjects(state.objects.filter(o => o.visible && !isReservation(o.userData)))[0];
  if (hit) selectPart(hit.object.userData.mesh, false);
});
new ResizeObserver(() => { const width = $('viewport').clientWidth, height = $('viewport').clientHeight; renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix(); }).observe($('viewport'));
function animate(now) {
  requestAnimationFrame(animate);
  if (state.playing) {
    const t = (1 - Math.cos((now - state.playStart) / 1800)) / 2, a = state.data.poses.stand, b = state.data.poses.raised;
    for (const leg of ['FL', 'FR', 'RL', 'RR']) state.q[leg] = a[leg].map((v, i) => THREE.MathUtils.lerp(v, b[leg][i], t));
    syncControls(); updateGeometry();
  }
  controls.update(); renderer.render(scene, camera); drawActuatorLabels();
}
requestAnimationFrame(animate);
try {
  const appearanceResponse = await fetch('../design/appearance.json');
  if (appearanceResponse.ok) appearance = await appearanceResponse.json();
  if (['chassis','FL','FR','RL','RR'].includes(query.get('focus'))) $('assembly-focus').value = query.get('focus');
  $('assembly-focus').onchange = () => { updateGeometry(); fit(); updateUrl(); };
  $('collision-paint').onchange = () => { if (state.lastStatus) showStatus(...state.lastStatus); };
  const response = await fetch('catalog.json'); if (!response.ok) throw Error('Viewer catalog is missing. Run publish_viewer.py as described in the viewer guide.');
  catalog = await response.json(); $('show-archived').checked = query.get('archive') === '1'; populateDesigns();
  fetch('releases.json').then(r => {
    if (!r.ok) throw Error('Release links are unavailable.');
    return r.json();
  }).then(index => {
    $('current-releases').replaceChildren(...index.releases.map(release => {
      const row = document.createElement('p'), link = document.createElement('a'), scope = document.createElement('small');
      link.href = release.archive; link.textContent = release.title;
      scope.textContent = release.source_label; scope.className = 'muted';
      row.append(link, document.createElement('br'), scope); return row;
    }));
  }).catch(() => { $('current-releases').textContent = 'See the fit and assembly guide for current package locations.'; });
  await loadDesign(query.get('design') || catalog.current_design);
  fetch('/api/health').then(r => r.ok ? r.json() : null).then(result => { state.liveAvailable = Boolean(result?.collision_checks); $('check').disabled = !state.liveAvailable || state.design.live_check_available === false; $('check').title = state.design.live_check_available === false ? 'See the recorded native assembly checks for this static export.' : state.liveAvailable ? '' : 'Start viewer/serve.py to enable live checks.'; }).catch(() => { $('check').disabled = true; });
  window.tinfoxReview = {state, setMode, selectPart, loadDesign, fit, checkPose, renderer};
} catch (error) { $('loading').hidden = false; $('loading').textContent = error.message; }
