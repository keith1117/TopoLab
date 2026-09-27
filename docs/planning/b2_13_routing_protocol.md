# B2.13 frozen workload routing and safe rejection

Status: frozen before any B2.13 reference or learned outcome. This is one
development-only **query-time policy** intervention, not a new fit or a final
acceleration claim. Plan version `topolab.b2_13.routing.v1` has canonical
SHA-256 `8be542da851cdb6e45325ddd94a3cde8cf6867df8d13a2d4c6b49f484a9d9d37`.

## Hypothesis and fixed decision

B2.12's exposed screen showed complementary behavior. Its context models
improved small-z refinement, while the older vector model was substantially
faster on large z. Every context model failed the quality check on the
high-volume large-y case. B2.13 uses only public case metadata to select one
already frozen checkpoint or reject to uniform:

| Mesh and direction | Volume | Decision |
|---|---:|---|
| Small `(12,6,3)`, y | 0.30–0.61 | B2.9 vector seed 29 |
| Small `(12,6,3)`, z | 0.30–0.61 | B2.12 context seed 17 |
| Large `(24,12,6)`, z | 0.30–0.61 | B2.9 vector seed 29 |
| Large `(24,12,6)`, y | Below 0.55 | B2.12 context seed 43 |
| Large `(24,12,6)`, y | At least 0.55 | Reject to fresh uniform |

The policy rejects unsupported mesh, support, load, budget, and volume
metadata to fresh uniform. It cannot inspect a density prediction, uniform
answer, test outcome, or runtime when routing. For accepted learned attempts,
the existing B2.9 vector encoding, filtered-volume projection, 360-update
physical-plateau SIMP refinement, independent quality check, and fresh full
uniform fallback are unchanged. Charge the routing decision and all model
setup, inference, projection, refinement, quality, and fallback time. A policy
rejection is recorded separately from a failed learned attempt and charges
its decision plus fresh complete uniform work. Model loading is a separately
reported one-time cost.

The unchanged B2.9 fit-index SHA-256 is
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`;
B2.12 fit-index SHA-256 is
`0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce`.
Verify every selection and checkpoint byte before screening. The exposed
B2.12 screen-index SHA-256 motivating the policy is
`cb671b2e9b5194606964faed0c6022c4a9a181b978827f906bfe416f72516443`.
The B2.5 control fit-index and control-43 checkpoint SHA-256 values remain
`a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`
and `d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d`.
No new fitting, label generation, checkpoint selection, model ensemble,
threshold search, or numerical tolerance change is allowed in this slice.

## Fresh reference, screen, and exposure boundary

Freeze twelve physically disjoint development cases: volumes
`0.3075,0.4575,0.6075`, both y/z point-load directions and both small/large
mesh scales, one case per scale/direction/volume stratum. Use fixed x-min
support and small-mesh load node `(x=max,y=5,z=1)`, doubled physically on
the large mesh. All use the 360-update B2.11 comparison budget and unchanged
physical-plateau solver. The volumes and physical case IDs must be absent
from all fitting, checkpoint selection, earlier development screens, M2
catalog, and design-exposed M3 v1 case definitions. M2 test/OOD and any new
final labels/outcomes remain sealed.

Before loading any learned model, run all twelve uniform references. Require
12/12 convergence, positive finite compliance, independent final-state
quality, and physical-volume error `<=0.005`; retain any failure and stop the
learned Gate. Reference resource caps are 1,800 s and 2 GiB peak RSS. The
screen later runs a fresh uniform per case for paired timing.

After reference feasibility, compare twelve methods per new case: fresh
uniform, physics heuristic, B2.4 training-only nearest neighbor, B2.5 MSE
control seed 43, all three fixed B2.9 vector seeds, all three fixed B2.12
context seeds, the single routed policy, and the impossible exact
own-trajectory oracle. The older models and baselines provide matched
diagnosis; their outcomes do not change the policy or its Gate. Retain all
twelve cases and **144 outcomes** atomically. A failed candidate retains its
failure and pays a fresh uniform fallback. Report every case, stratum, route,
rejection, phase cost, fallback, oracle generation cost, and resource use.
The complete screen cap is 14,400 s and 2 GiB peak RSS.

The **B2.13 development feasibility Gate** requires complete references,
cases, and outcomes; zero accepted compliance, convergence, or volume quality
violations; and both resource caps. The single routed policy must have a
fallback/rejection-inclusive arithmetic mean paired time ratio `<=0.90` at
**each** mesh scale and `<=1.0` in **every** scale/direction stratum. A pass
still requires a separately frozen larger development confirmation before
B3. Failure preserves all evidence and calls for a new bounded intervention.
Neither result is final acceleration evidence.

Run the read-only plan, references, and screen from one clean committed
revision with one CPU/BLAS thread. Keep generated indices and logs outside Git.
