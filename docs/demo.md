# A1.3 local demo video

[Watch the recorded local demo](assets/topolab-local-demo.mp4) ·
[View the architecture diagram](assets/architecture.svg)

The silent, on-screen walkthrough uses the real local Compose stack and the existing
React workspace. It presents the architecture, submits a small problem, observes
run progress, cancels a separate bounded run, restarts the API and reads durable
terminal history, then inspects convergence and the final 3D physical-density field.
The video is a presentation artifact; numerical acceptance and runtime evidence
remain in the linked validation reports.

The video runs for 3 minutes 39 seconds. It uses short scene captions and
real browser and terminal footage. The convergence view at 3:18 is a still frame
captured from that same live browser session and held for eight seconds so the
plots can be read; no result values were synthesized.

| Time | What appears |
|---|---|
| 0:00–0:20 | Implemented local architecture |
| 0:20–1:00 | Submit the default `8 × 4 × 3` case and observe its terminal result |
| 1:00–2:10 | Submit a larger bounded case, observe progress, and cancel it |
| 2:10–3:18 | Restart the API and read the persisted successful and cancelled records |
| 3:18–3:26 | State-consistent convergence plots and final metrics |
| 3:26–3:39 | Interactive 3D physical-density result |

## Reproduce the path

From the repository root, with Docker and Compose installed:

```bash
docker compose up --build -d
```

Open <http://127.0.0.1:8080>. The successful demo uses the workspace's default
`8 × 4 × 3` mesh and one fixed face with an opposite face-resultant load. The
cancellation segment uses a `32 × 12 × 6` mesh to keep a run active long enough for
the real progress and cancellation controls to be visible. These are demonstration
inputs, not performance benchmarks or new numerical fixtures. The versioned A1.1
canonical case remains in
[`src/topolab/examples/canonical_demo_v1.json`](../src/topolab/examples/canonical_demo_v1.json)
and can be posted unchanged to the same API; its fixed validation is in
[`docs/validation/a1_1_canonical_demo.md`](validation/a1_1_canonical_demo.md).

The video restarts the API while completed and cancelled records are on the named
volume. It does not show optimizer resume: an active run interrupted by process exit
would be marked failed. End the local stack with `docker compose down`; add `-v` only
if you intend to remove the SQLite volume and run history.

The [A1.3 validation report](validation/a1_3_architecture_demo.md) records video
duration, capture environment, scene coverage, and checks. A clean Linux run and
Gate A1 decision remain the separate A1.4 slice.
