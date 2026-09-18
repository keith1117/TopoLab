type Triple = readonly [number, number, number];

interface FaceDefinition {
  neighbor: Triple;
  corners: readonly [Triple, Triple, Triple, Triple];
}

const FACES: readonly FaceDefinition[] = [
  {
    neighbor: [-1, 0, 0],
    corners: [
      [0, 0, 0],
      [0, 0, 1],
      [0, 1, 1],
      [0, 1, 0],
    ],
  },
  {
    neighbor: [1, 0, 0],
    corners: [
      [1, 0, 0],
      [1, 1, 0],
      [1, 1, 1],
      [1, 0, 1],
    ],
  },
  {
    neighbor: [0, -1, 0],
    corners: [
      [0, 0, 0],
      [1, 0, 0],
      [1, 0, 1],
      [0, 0, 1],
    ],
  },
  {
    neighbor: [0, 1, 0],
    corners: [
      [0, 1, 0],
      [0, 1, 1],
      [1, 1, 1],
      [1, 1, 0],
    ],
  },
  {
    neighbor: [0, 0, -1],
    corners: [
      [0, 0, 0],
      [0, 1, 0],
      [1, 1, 0],
      [1, 0, 0],
    ],
  },
  {
    neighbor: [0, 0, 1],
    corners: [
      [0, 0, 1],
      [1, 0, 1],
      [1, 1, 1],
      [0, 1, 1],
    ],
  },
];

export interface DensitySurface {
  x: number[];
  y: number[];
  z: number[];
  i: number[];
  j: number[];
  k: number[];
  intensity: number[];
  visibleElements: number;
  totalElements: number;
}

export function buildDensitySurface(
  elementCounts: Triple,
  lengths: Triple,
  density: readonly number[],
  threshold: number,
): DensitySurface {
  validateInputs(elementCounts, lengths, density, threshold);
  const [nx, ny, nz] = elementCounts;
  const spacing: Triple = [lengths[0] / nx, lengths[1] / ny, lengths[2] / nz];
  const included = density.map((value) => value >= threshold);
  const surface: DensitySurface = {
    x: [],
    y: [],
    z: [],
    i: [],
    j: [],
    k: [],
    intensity: [],
    visibleElements: included.filter(Boolean).length,
    totalElements: density.length,
  };

  for (let ez = 0; ez < nz; ez += 1) {
    for (let ey = 0; ey < ny; ey += 1) {
      for (let ex = 0; ex < nx; ex += 1) {
        const index = elementIndex(ex, ey, ez, nx, ny);
        if (!included[index]) {
          continue;
        }
        for (const face of FACES) {
          const neighbor = [
            ex + face.neighbor[0],
            ey + face.neighbor[1],
            ez + face.neighbor[2],
          ] as const;
          if (
            inside(neighbor, elementCounts) &&
            included[elementIndex(neighbor[0], neighbor[1], neighbor[2], nx, ny)]
          ) {
            continue;
          }
          appendFace(surface, face.corners, [ex, ey, ez], spacing, density[index]);
        }
      }
    }
  }

  return surface;
}

function appendFace(
  surface: DensitySurface,
  corners: FaceDefinition["corners"],
  element: Triple,
  spacing: Triple,
  density: number,
) {
  const firstVertex = surface.x.length;
  for (const corner of corners) {
    surface.x.push((element[0] + corner[0]) * spacing[0]);
    surface.y.push((element[1] + corner[1]) * spacing[1]);
    surface.z.push((element[2] + corner[2]) * spacing[2]);
    surface.intensity.push(density);
  }
  surface.i.push(firstVertex, firstVertex);
  surface.j.push(firstVertex + 1, firstVertex + 2);
  surface.k.push(firstVertex + 2, firstVertex + 3);
}

function inside(index: Triple, counts: Triple) {
  return index.every((value, axis) => value >= 0 && value < counts[axis]);
}

function elementIndex(ex: number, ey: number, ez: number, nx: number, ny: number) {
  return ex + nx * (ey + ny * ez);
}

function validateInputs(
  elementCounts: Triple,
  lengths: Triple,
  density: readonly number[],
  threshold: number,
) {
  if (elementCounts.some((value) => !Number.isInteger(value) || value <= 0)) {
    throw new Error("element counts must be positive integers");
  }
  if (lengths.some((value) => !Number.isFinite(value) || value <= 0)) {
    throw new Error("mesh lengths must be positive finite values");
  }
  const expected = elementCounts[0] * elementCounts[1] * elementCounts[2];
  if (density.length !== expected) {
    throw new Error(`density field contains ${density.length} values; expected ${expected}`);
  }
  if (density.some((value) => !Number.isFinite(value) || value < 0 || value > 1)) {
    throw new Error("density values must lie within [0, 1]");
  }
  if (!Number.isFinite(threshold) || threshold < 0 || threshold > 1) {
    throw new Error("density threshold must lie within [0, 1]");
  }
}
