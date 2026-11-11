import * as THREE from 'three';

// CAD meshes share positions across both curved surfaces and sharp corners.
// Split rendering normals at creases without changing any triangle positions.
export function createCADGeometry(data, creaseAngle = Math.PI / 5) {
  const adjacency = data.vertices.map(() => []);
  const normals = new Float64Array(data.faces.length * 3);
  const areas = new Float64Array(data.faces.length);
  for (let i = 0; i < data.faces.length; i++) {
    const face = data.faces[i], a = data.vertices[face[0]], b = data.vertices[face[1]], c = data.vertices[face[2]];
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
    const vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const length = Math.hypot(nx, ny, nz);
    areas[i] = length;
    if (length) { normals[i * 3] = nx / length; normals[i * 3 + 1] = ny / length; normals[i * 3 + 2] = nz / length; }
    for (const vertex of face) adjacency[vertex].push(i);
  }
  const positions = new Float32Array(data.faces.length * 9), shading = new Float32Array(positions.length);
  const threshold = Math.cos(creaseAngle);
  let offset = 0;
  for (let i = 0; i < data.faces.length; i++) {
    const nx = normals[i * 3], ny = normals[i * 3 + 1], nz = normals[i * 3 + 2];
    for (const vertex of data.faces[i]) {
      positions.set(data.vertices[vertex], offset);
      let x = 0, y = 0, z = 0;
      for (const adjacent of adjacency[vertex]) {
        const j = adjacent * 3;
        if (nx * normals[j] + ny * normals[j + 1] + nz * normals[j + 2] > threshold) {
          x += normals[j] * areas[adjacent]; y += normals[j + 1] * areas[adjacent]; z += normals[j + 2] * areas[adjacent];
        }
      }
      const length = Math.hypot(x, y, z);
      shading.set(length ? [x / length, y / length, z / length] : [nx, ny, nz], offset);
      offset += 3;
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.BufferAttribute(shading, 3));
  return geometry;
}
