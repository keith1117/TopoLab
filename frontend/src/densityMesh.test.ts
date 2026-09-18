import { describe, expect, it } from "vitest";

import { buildDensitySurface } from "./densityMesh";

describe("buildDensitySurface", () => {
  it("maps x-fast density indices to physical element coordinates", () => {
    const surface = buildDensitySurface(
      [2, 2, 1],
      [2, 4, 1],
      [0.1, 0.2, 0.7, 0.8],
      0.5,
    );

    expect(surface.visibleElements).toBe(2);
    expect(surface.totalElements).toBe(4);
    expect(Math.min(...surface.x)).toBe(0);
    expect(Math.max(...surface.x)).toBe(2);
    expect(Math.min(...surface.y)).toBe(2);
    expect(Math.max(...surface.y)).toBe(4);
    expect(Math.min(...surface.z)).toBe(0);
    expect(Math.max(...surface.z)).toBe(1);
  });

  it("removes the shared face between adjacent visible elements", () => {
    const surface = buildDensitySurface([2, 1, 1], [2, 1, 1], [0.6, 0.8], 0.5);

    expect(surface.x).toHaveLength(40);
    expect(surface.i).toHaveLength(20);
    expect(surface.j).toHaveLength(20);
    expect(surface.k).toHaveLength(20);
  });

  it("returns an empty surface when no element reaches the threshold", () => {
    const surface = buildDensitySurface([1, 1, 1], [1, 1, 1], [0.2], 0.5);

    expect(surface.visibleElements).toBe(0);
    expect(surface.x).toEqual([]);
    expect(surface.i).toEqual([]);
  });

  it("rejects a density field that does not match the mesh", () => {
    expect(() =>
      buildDensitySurface([2, 1, 1], [2, 1, 1], [0.5], 0.25),
    ).toThrow("density field contains 1 values; expected 2");
  });
});
