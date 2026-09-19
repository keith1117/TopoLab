import { useState, type FormEvent } from "react";

import { createRun } from "./api";
import type {
  Axis,
  FaceSide,
  RunSnapshot,
  TopologyProblem,
} from "./types";

const AXES: Axis[] = ["x", "y", "z"];
const SIDES: FaceSide[] = ["min", "max"];

export function RunSubmissionForm({
  onCreated,
  disabled = false,
}: {
  onCreated: (run: RunSnapshot) => void;
  disabled?: boolean;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [submittedId, setSubmittedId] = useState<string | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmissionError(null);
    setSubmittedId(null);

    let problem: TopologyProblem;
    try {
      problem = problemFromForm(new FormData(event.currentTarget));
    } catch (error) {
      setSubmissionError(errorMessage(error));
      return;
    }

    setIsSubmitting(true);
    try {
      const run = await createRun(problem);
      setSubmittedId(run.run_id);
      onCreated(run);
    } catch (error) {
      setSubmissionError(errorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="run-form" onSubmit={(event) => void submit(event)}>
      <fieldset disabled={disabled || isSubmitting}>
        <legend>Mesh</legend>
        <p>Hex8 elements and physical domain lengths in metres.</p>
        <div className="form-grid form-grid-six">
          <NumberField
            label="Elements X"
            name="nx"
            defaultValue={8}
            min={1}
            step={1}
          />
          <NumberField
            label="Elements Y"
            name="ny"
            defaultValue={4}
            min={1}
            step={1}
          />
          <NumberField
            label="Elements Z"
            name="nz"
            defaultValue={3}
            min={1}
            step={1}
          />
          <NumberField
            label="Length X"
            name="lx"
            defaultValue={1}
            min={Number.MIN_VALUE}
          />
          <NumberField
            label="Length Y"
            name="ly"
            defaultValue={0.4}
            min={Number.MIN_VALUE}
          />
          <NumberField
            label="Length Z"
            name="lz"
            defaultValue={0.3}
            min={Number.MIN_VALUE}
          />
        </div>
      </fieldset>

      <fieldset disabled={disabled || isSubmitting}>
        <legend>Material</legend>
        <p>Isotropic, linear-elastic material in SI units.</p>
        <div className="form-grid form-grid-three">
          <NumberField
            label="Solid modulus (Pa)"
            name="solidModulus"
            defaultValue={2e11}
            min={Number.MIN_VALUE}
          />
          <NumberField
            label="Minimum modulus (Pa)"
            name="minimumModulus"
            defaultValue={2e5}
            min={Number.MIN_VALUE}
          />
          <NumberField
            label="Poisson ratio"
            name="poissonRatio"
            defaultValue={0.3}
            min={-0.999}
            max={0.499}
          />
        </div>
      </fieldset>

      <fieldset disabled={disabled || isSubmitting}>
        <legend>Boundary and load</legend>
        <p>One fully fixed face and one signed, equally distributed face resultant.</p>
        <div className="form-grid form-grid-six">
          <SelectField
            label="Fixed axis"
            name="supportAxis"
            options={AXES}
            defaultValue="x"
          />
          <SelectField
            label="Fixed side"
            name="supportSide"
            options={SIDES}
            defaultValue="min"
          />
          <SelectField
            label="Load face axis"
            name="loadAxis"
            options={AXES}
            defaultValue="x"
          />
          <SelectField
            label="Load face side"
            name="loadSide"
            options={SIDES}
            defaultValue="max"
          />
          <SelectField
            label="Load direction"
            name="loadDirection"
            options={AXES}
            defaultValue="y"
          />
          <NumberField label="Total load (N)" name="loadTotal" defaultValue={-1000} />
        </div>
      </fieldset>

      <fieldset disabled={disabled || isSubmitting}>
        <legend>Optimization</legend>
        <p>Density-filtered SIMP settings for this run.</p>
        <div className="form-grid form-grid-four">
          <NumberField
            label="Volume fraction"
            name="volumeFraction"
            defaultValue={0.3}
            min={Number.MIN_VALUE}
            max={1}
          />
          <NumberField
            label="Filter radius (m)"
            name="filterRadius"
            defaultValue={0.15}
            min={Number.MIN_VALUE}
          />
          <NumberField label="Penalty" name="penalty" defaultValue={3} min={1} />
          <NumberField
            label="Minimum density"
            name="minimumDensity"
            defaultValue={0.001}
            min={Number.MIN_VALUE}
            max={0.999}
          />
          <NumberField
            label="Move limit"
            name="moveLimit"
            defaultValue={0.2}
            min={Number.MIN_VALUE}
            max={1}
          />
          <NumberField
            label="Convergence tolerance"
            name="convergenceTolerance"
            defaultValue={0.01}
            min={Number.MIN_VALUE}
          />
          <NumberField
            label="Maximum iterations"
            name="maxIterations"
            defaultValue={40}
            min={1}
            step={1}
          />
        </div>
      </fieldset>

      <div className="form-actions">
        <div className="submission-feedback" aria-live="polite">
          {submissionError ? (
            <span className="form-error" role="alert">
              {submissionError}
            </span>
          ) : submittedId ? (
            <span className="form-success">
              Run {shortId(submittedId)} submitted.
            </span>
          ) : (
            <span>Runs execute asynchronously and appear at the top of history.</span>
          )}
        </div>
        <button
          className="submit-run-button"
          type="submit"
          disabled={disabled || isSubmitting}
        >
          {isSubmitting
            ? "Submitting…"
            : disabled
              ? "Loading history…"
              : "Submit optimization"}
        </button>
      </div>
    </form>
  );
}

function NumberField({
  label,
  name,
  defaultValue,
  min,
  max,
  step = "any",
}: {
  label: string;
  name: string;
  defaultValue: number;
  min?: number;
  max?: number;
  step?: number | "any";
}) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input
        name={name}
        type="number"
        defaultValue={defaultValue}
        min={min}
        max={max}
        step={step}
        required
      />
    </label>
  );
}

function SelectField<T extends string>({
  label,
  name,
  options,
  defaultValue,
}: {
  label: string;
  name: string;
  options: T[];
  defaultValue: T;
}) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <select name={name} defaultValue={defaultValue} required>
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </label>
  );
}

function problemFromForm(form: FormData): TopologyProblem {
  const nx = integer(form, "nx", "Elements X");
  const ny = integer(form, "ny", "Elements Y");
  const nz = integer(form, "nz", "Elements Z");
  const solidModulus = finiteNumber(form, "solidModulus", "Solid modulus");
  const minimumModulus = finiteNumber(form, "minimumModulus", "Minimum modulus");
  const poissonRatio = finiteNumber(form, "poissonRatio", "Poisson ratio");
  const loadTotal = finiteNumber(form, "loadTotal", "Total load");
  const volumeFraction = finiteNumber(form, "volumeFraction", "Volume fraction");
  const minimumDensity = finiteNumber(form, "minimumDensity", "Minimum density");
  const moveLimit = finiteNumber(form, "moveLimit", "Move limit");

  positive(nx, "Elements X");
  positive(ny, "Elements Y");
  positive(nz, "Elements Z");
  positive(solidModulus, "Solid modulus");
  positive(minimumModulus, "Minimum modulus");
  if (minimumModulus >= solidModulus) {
    throw new Error("Minimum modulus must be less than solid modulus.");
  }
  if (poissonRatio <= -1 || poissonRatio >= 0.5) {
    throw new Error("Poisson ratio must be between -1 and 0.5.");
  }
  if (loadTotal === 0) {
    throw new Error("Total load must be nonzero.");
  }
  within(volumeFraction, 0, 1, "Volume fraction", true);
  within(minimumDensity, 0, 1, "Minimum density", false);
  if (minimumDensity >= volumeFraction) {
    throw new Error("Minimum density must be less than volume fraction.");
  }
  within(moveLimit, 0, 1, "Move limit", true);

  return {
    mesh: {
      element_counts: [nx, ny, nz],
      lengths: [
        positiveNumber(form, "lx", "Length X"),
        positiveNumber(form, "ly", "Length Y"),
        positiveNumber(form, "lz", "Length Z"),
      ],
    },
    material: {
      solid_modulus: solidModulus,
      minimum_modulus: minimumModulus,
      poisson_ratio: poissonRatio,
    },
    supports: [{
      axis: axis(form, "supportAxis"),
      side: side(form, "supportSide"),
      directions: ["x", "y", "z"],
    }],
    loads: [{
      kind: "face",
      axis: axis(form, "loadAxis"),
      side: side(form, "loadSide"),
      direction: axis(form, "loadDirection"),
      total: loadTotal,
    }],
    optimization: {
      volume_fraction: volumeFraction,
      filter_radius: positiveNumber(form, "filterRadius", "Filter radius"),
      penalty: atLeast(form, "penalty", "Penalty", 1),
      minimum_density: minimumDensity,
      move_limit: moveLimit,
      convergence_tolerance: positiveNumber(
        form,
        "convergenceTolerance",
        "Convergence tolerance",
      ),
      max_iterations: positiveInteger(form, "maxIterations", "Maximum iterations"),
    },
    initial_density: null,
  };
}

function finiteNumber(form: FormData, name: string, label: string): number {
  const value = Number(form.get(name));
  if (!Number.isFinite(value)) {
    throw new Error(`${label} must be a finite number.`);
  }
  return value;
}

function integer(form: FormData, name: string, label: string): number {
  const value = finiteNumber(form, name, label);
  if (!Number.isInteger(value)) {
    throw new Error(`${label} must be an integer.`);
  }
  return value;
}

function positiveInteger(form: FormData, name: string, label: string): number {
  const value = integer(form, name, label);
  positive(value, label);
  return value;
}

function positiveNumber(form: FormData, name: string, label: string): number {
  const value = finiteNumber(form, name, label);
  positive(value, label);
  return value;
}

function atLeast(form: FormData, name: string, label: string, minimum: number) {
  const value = finiteNumber(form, name, label);
  if (value < minimum) {
    throw new Error(`${label} must be at least ${minimum}.`);
  }
  return value;
}

function positive(value: number, label: string) {
  if (value <= 0) {
    throw new Error(`${label} must be greater than zero.`);
  }
}

function within(
  value: number,
  minimum: number,
  maximum: number,
  label: string,
  includeMaximum: boolean,
) {
  if (value <= minimum || (includeMaximum ? value > maximum : value >= maximum)) {
    const closing = includeMaximum ? "]" : ")";
    throw new Error(`${label} must lie in (${minimum}, ${maximum}${closing}.`);
  }
}

function axis(form: FormData, name: string): Axis {
  const value = form.get(name);
  if (value === "x" || value === "y" || value === "z") {
    return value;
  }
  throw new Error("Axis selection is invalid.");
}

function side(form: FormData, name: string): FaceSide {
  const value = form.get(name);
  if (value === "min" || value === "max") {
    return value;
  }
  throw new Error("Face side selection is invalid.");
}

function shortId(runId: string) {
  return runId.length > 12 ? `${runId.slice(0, 8)}…${runId.slice(-4)}` : runId;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected request failure";
}
