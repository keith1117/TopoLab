# B4.25 bounded active-set objective-method review

Date: 2026-10-06 (America/New_York). Version: topolab.b4_25.active-set-method-review.v1.

**Read-only method-review acceptance passed.** The complete saved panel
passed 448 predicates, and the separate auditor agreed on
2222 independently reconstructed scalar/identity/disposition fields.
All 64 rows, 35 mask failures, 34 FD failures and 69 original failed positions
remain, with 34 overlapping failed rows. All failed FD rows cross the central
clipping set and are compatible with the frozen clipping-departure explanation.
Original B4.23 integrity remains failed 3907/3976 and cost
57546.072069>7200; B4.20 remains failed. This review clears no scientific Gate.

One candidate review and one independent auditor completed under the
[prospective protocol](../planning/b4_25_active_set_method_review_protocol.md).
The new charge is **80.34<=180 seconds**, including the entire paid
60-second reserve. Reserve use is **40.406297375/60** and observed new peak
RSS is **26492928 bytes**, below 1 GiB. Historical missing RSS and whole-slice
memory compliance from B4.24 remain unknown; its original memory proof is not
completed by this slice. Full training-memory feasibility remains pending.

Next: **B4.26 bounded active-set-aware correctness and cost preregistration**, not started and requiring a separate prospective contract
and explicit research/execution boundary. No new objective, derivative,
correctness rule, root/projection/FEM, fit or final access follows from B4.25.
Uniform remains default, fixed P/17 unrepaired; all final evidence and 48 unused
B4.10 cases stay sealed. Stop after this slice.

## Frozen source, roles and complete retained evidence

Source merged through [PR #153](https://github.com/keith1117/TopoLab/pull/153).
Tested head `c42beb9f1752ab030e1298b1131c73d1021d3cd6`; production main `9139952930ffd727d2d309b6df2aa8b9fb69b6ce`; identical Git trees.
All applicable exact-head CI passed before protected merge, followed by all
three [merged-main checks](https://github.com/keith1117/TopoLab/actions/runs/37559985125) before production. The source release
binds 165 runtime/source/convention/protocol files. Frozen plan
SHA-256: `01361d39e22b8603b226c4b5943385eee9d9d5b9ba467d8c9333a69a68fa2fa3`. Locked Python 3.12 and all five one-thread settings
were enforced at every numerical-free production entry.

Only fifteen literal compact B4.24 v3 scalar/audit/CI/native receipt bindings
and their referenced native profiles/logs/source identities were read. Its
accepted 2104 predicates, 1728 field comparisons, 72 central states, 128 sides,
216 first-inclusive timings and full original cost object remain prior evidence,
not repeated numerical/timing/journal checks in B4.25. No original B4.23 arrays
or journals, production labels/models, B3 payload, screening/final evidence or
unused fresh cases were opened. Default planning reads no evidence and writes
no output. Before-call attempts and exclusive output names prevent retries.

The separately enumerated original positions use frozen mesh/direction/within-
group case order, states 0/4, sine/cosine directions and both 1e-4/2e-4 steps.
All original row fields, exact-FEM diagnostics, offsets/residuals and full cost
object are byte-identical. Signed FD/central-derivative gaps, normalized errors,
clipping/volume/value/gradient decomposition terms, saved arithmetic envelopes
and explanation flags were independently recomputed at scalar rtol/atol1e-12.
The original FD 1e-4 and floor 1e-8 remain unchanged. No favorable subset is selected.

| Original state / step | Rows | Mask failures | FD failures | Overlap |
|---|---:|---:|---:|---:|
| 0/0.0001 | 16 | 14 | 14 | 14 |
| 0/0.0002 | 16 | 15 | 15 | 15 |
| 4/0.0001 | 16 | 0 | 0 | 0 |
| 4/0.0002 | 16 | 6 | 5 | 5 |

## Fixed-set derivative and finite crossing intervals

For the existing map x_i=clip(z_i+s, rho_min, 1), take a strictly fixed
lower/free/upper partition, with A its free indices and D=sum_{i in A} w_i>0. Differentiating
sum_i w_i*x_i=v along a raw direction d gives

    ds/dt = -sum_{i in A}(w_i*d_i)/D
    dL/dt = sum_{i in A}(g_i*d_i)
             - sum_{i in A}(g_i)*sum_{i in A}(w_i*d_i)/D.

This follows directly from the frozen mathematical projection and signed
cotangent. The direction of clipped coordinates is zero; the shared offset
supplies the volume correction. It implements no derivative or numerical
candidate in B4.25. D=0 and kink-adjacent states are outside this strictly
fixed-set derivation and require prospective treatment in any later contract.

The original central secant may traverse several affine pieces, whereas this
derivative belongs to the central piece. A retained interval crossing a set
boundary therefore need not have its secant equal to the central derivative.
The saved clipping-departure decomposition describes those finite intervals.
Its compatibility cannot prove a global cause, validate every pointwise
gradient, change the original FD acceptance rule, establish local fidelity or
clear either failed scientific Gate.

## Six method dispositions and next boundary

| Method | Frozen disposition and implication |
|---|---|
| Existing v3 / original criteria | B4.23 integrity and cost remain failed; stop before fitting. |
| Active-set-aware correctness evidence | One preregistration hypothesis, requiring independent pointwise and transition evidence, preserved legacy failures, local fidelity, complete first-inclusive cost and full training-memory boundaries before any numerical permission. |
| Smooth bounded volume map | Deferred: it changes the map and needs its own mathematical, root, correctness, fidelity and cost contract. |
| Detached offset / straight-through clipping | Incompatible with the volume-constrained fixed-set derivative; neither can certify the existing objective. |
| Exact current-prediction FEM | Existing cost failure remains; no alternate cache, ordering or solver search. |
| Startup retiming / schedule or population reduction | No first-observation removal, retiming, epoch/population/physics-frequency search or replacement of the original failed Gate. |

Only the separately frozen ordered rule selects the next read-only slice.
B4.26 must make its prospective criteria and research/execution boundary
reviewable through a separate frozen contract. B4.25 selects no implemented
new objective, derivative, root, step, tolerance, model or training schedule.
Uniform remains the operational default and P/17 remains unrepaired.

## Original full cost and two fixed diagnostic scenarios

Keep the exact original first-inclusive maxima, preparation, all three seeds,
200 FULL epochs, 432 small/76 large cases, factor1.25, twelve B4.1 fits
3870.204341 seconds and all B4.15–23 charges 851.38 seconds. B4.24's 200.98
and this slice are additional in a separate accounting view, never changes
to the original B4.23 proxy. No cold timing is removed or retimed.

| Preserved term | Seconds |
|---|---:|
| Maximum small prediction unit | 0.159795667 |
| Maximum large prediction unit | 0.005527875 |
| Maximum small setup | 0.2308165 |
| Maximum large setup | 1.269052625 |
| Full-population preparation | 735.602728153 |
| Original additional prediction work | 52088.884999626 |
| Fixed preparation / twelve fits / prior charges | 5457.187069153 |

| Fixed scenario | Total prospective seconds | Interpretation |
|---|---:|---|
| Original complete maximum | 57546.072068779 | original failed Gate unchanged |
| Zero small, recorded large maximum | 5772.275946258 | fixed sample deletion; not a measured method |
| Zero prediction at both scales | 5457.187069153 | fixed setup/fits/prior charges retained |

The separate accounting view adds B4.24 and this complete slice to the original
maximum, giving 57827.392068779 seconds. It does not replace the original
failed proxy or omit any historical failure/charge.

Before B4.25's new charge, the conditional prediction budget is
1541.832930847 seconds and the corresponding population-weighted common
unit budget is 0.004046806 seconds; common prediction reduction would
need factor 33.783741388 under the unchanged sampled maxima/fixed costs.
After this entire slice, the separate conditional remaining budget is
1461.492930847 seconds. These are sample arithmetic, not an optimized-method
bound, observed saving, achievable speedup or revised Gate. Full future
training, screening, fallback, final and confirmation costs still matter.
Static retained-array estimate 127992304 bytes excludes network, optimizer,
activations, data and transient factors. Its signed difference to 4 GiB is
4166974992 bytes; neither this arithmetic nor sequential native RSS certifies
full fitting memory. Displayed decimals are rounded; the bound JSON retains
the complete original precision and cost object.

## Native resource closure and software checks

| Process | Native wall | User CPU | System CPU | Peak RSS bytes | Charge seconds |
|---|---:|---:|---:|---:|---|
| plan | 0.07 | 0.04 | 0.01 | 22609920 | within paid 60 reserve |
| review | 0.17 | 0.09 | 0.05 | 25772032 | 10.17 |
| independent | 0.17 | 0.1 | 0.06 | 26492928 | 10.17 |
| closure | 0.15 | 0.07 | 0.04 | 23363584 | within paid 60 reserve |
| verification | 0.12 | 0.07 | 0.04 | 23166976 | within paid 60 reserve |

Review/audit each pay max(native wall+10, internal). Plan, closure, verification
and post-exit metadata envelope remain inside the fully paid 60 reserve.
All five native profiles contain wall/user/system/RSS through exit, every
command exited zero, and the closure's ledger SHA is unchanged afterward.
The final metadata proof binds verification's own final profile, native and
controller peaks and its own observed RSS/envelope. No profiling trial,
budget reset, frozen-output overwrite or numerical retry occurred. Post-exit
metadata adds its measured elapsed plus 10 envelope, 10.066297375 seconds;
the native reserve component is 30.34.

All B4.24 failures, old 76.19 charge, old 50.53/60 reserve, complete200.98 and
missing historic RSS remain unchanged. B4.19's actual case/gap/counts stay
unknown; B4.20's 983/984 failure and complete cost remain. This is a new bounded
read-only resource proof, not historical/full-training memory evidence or
learned repair/independent confirmation.

Source passed locked dev sync, Ruff, mypy on 68 source files, all 1158 tests
(650.56 seconds), whitespace and 177 relative links. Fifty focused
regressions cover default no-access planning, literal producer case order,
independent condition enumeration/cost, retained fields, forged acceptance/
unknowns, failure route, metadata roles, caps/contained native hashes and no
retry. The preproduction static review corrected both global-sorting of public
case IDs and an exact binary-float comparison against the displayed 200.98
charge: the old published closure expression evaluates 200.98000000000002.
The correction uses the already frozen arithmetic 1e-12 and leaves hash-bound
old bytes and all scientific tolerances unchanged. Original cache/lint failures,
the deliberately interrupted pre-fix software run, superseded source commits,
their checks and the GitHub connector 403/create fallback remain external.
Neither production review nor audit had started during these corrections.

Evidence passed locked dev sync, Ruff, mypy, all 1158 tests (670.62 seconds)
and whitespace checks. The documentation guard checked 383 relative links and
all historical identities. Protected exact-head/main CI remain required before
release; final logs, guards and CI receipts stay external.

The first metadata-only report renderer stopped on an unresolved resource-table
placeholder before writing its output. The corrected report uses the already
closed profiles; its failure record is preserved externally. No review, audit,
native resource process or numerical experiment was repeated.
A separate metadata history comparison stopped on an obsolete expected heading;
the corrected comparison confirmed the older history body byte-for-byte. Both
metadata failure records remain external.

Every staged path and every pending upload commit is reviewed by publication
guards. Exact-head protected PR/main CI precede release, with no protection
lowered. All 139 historical source/protocol/report identities, old handoff and
two untracked user documents remain. Status, one history entry, English/Chinese
roadmap and indices are updated; README usage/claims stay unchanged. Generated
evidence, native/CI/software logs and controllers remain external or ignored.

## External evidence, reproduction and immutable bindings

Evidence: `/Users/keith1117/Documents/TopoLab-data/b4-25-active-set-method-review`.
Software: `/Users/keith1117/Documents/TopoLab-data/b4-25-software-validation`.
Prepublication backup: `/Users/keith1117/Documents/TopoLab-data/backups/b4-25-01a113d9/prepublication`; 90 files verified,
manifest SHA-256 `f2110501ecacbc84cd9e5f6f9ecfba36793168e2fe2533edd7fedc543c4f845a`. Final publication audit, main CI and a
separate postpublication backup are linked by the external release/closure
receipts. The old B4.24 roots/backups/handoff remain untouched.

```bash
PYTHONPATH=src .venv/bin/python scripts/b4_25_active_set_method_review.py \
  --mode plan \
  --review-root ../TopoLab-data/b4-24-registered-continuation-v3 \
  --output-root ../TopoLab-data/b4-25-active-set-method-review
```

Default planning is safe and output-free. The already completed exclusive
production names must not be reused. Any future execution needs a separately
compatible source/CI/contract/native boundary; controller snapshots and exact
argv/attempt/exit receipts retain the observed reproduction path.

| Artifact | SHA-256 |
|---|---|
| `audit_receipts/production_release.json` | `1aa597de4e0229b7a994678e3cd37e885f0dea5198e74bf0fbe4f1b3908e3ef9` |
| `audit_receipts/source_final_head_ci.json` | `5d8572054770e2159590e2c9f061cfcc4867eb96e3ef865d73d0831c3a1eeac9` |
| `audit_receipts/source_main_ci.json` | `d5aed360e52e1977e1708f1ba505a600bb2a09e1fcf2dfcafeca78ac9c8ebe08` |
| `audit_receipts/plan.json` | `4a8f64fed8991a8f4a5ee5d9f244dba88b8ed891cdb24c6a79532a647f1f3350` |
| `review.json` | `c6b2679cd7ec678cb6a763c2edcb650f7493c8fb927c838144bf7598145ce0b1` |
| `independent_audit.json` | `61f11e68014b48498ae4c1e17eb5e6a564118cc43ede58ecd036d7b23f7fa248` |
| `resource_close.json` | `1465a562a8c30e66b56a2af712672d1e82307f0f259b0186918fa54f5a9ee68e` |
| `resource_verification.json` | `001c37942b3b302ebe8d0dbdd7a17bc086f091123c1c153c6af783251b8dd091` |
| `audit_receipts/execution_commands.json` | `8ec9ed42de47562f12e120f2c9bde76045253b4578a52f2bf9cb4427b3012221` |
| `audit_receipts/postexit_reservation.json` | `a9ba2f7e29a49eee33bbdd6dab1479ee72781860c56686d3c04680347873d6e6` |
| `audit_receipts/plan_attempt.json` | `f40c7b350860eec5102f4d16dd6d8ca2c00c5c95236b62584db4623a33948b2d` |
| `audit_receipts/plan_command.json` | `afa6c9b4629740615aabb694a28fdace2e792e7564fbc1a671f66b7362437b3a` |
| `profiles/plan.time` | `9eeb7f6645222175ebeefe662de080b6c3aee2d0c503eaf14b725746895e0490` |
| `logs/plan.log` | `4a8f64fed8991a8f4a5ee5d9f244dba88b8ed891cdb24c6a79532a647f1f3350` |
| `audit_receipts/review_attempt.json` | `e3eb155027029141c5a11fab95c532f1d16255487952e8cafc4eefbc95a3a067` |
| `audit_receipts/review_command.json` | `4396feff0aff76b44ca2388b213ac963f19ea811c6cd84a243b8c5560859c2f7` |
| `profiles/review.time` | `1ba7d3b993b07b042a410edfd7056f0d7e0e48f6ab7d183712126204620f4fb3` |
| `logs/review.log` | `f6c287638cdcb598c88be9610fcbbbf818c89238d1ea1772369f8b046fd9dc70` |
| `audit_receipts/independent_attempt.json` | `d5d889588fbd7e15024af7e56ee99163a73a32fb6ba79df35bb3e2db81247791` |
| `audit_receipts/independent_command.json` | `45485664180be7860fd52b6f71bfc6349cb8d1647a00e4be2a8c587c4403c88a` |
| `profiles/independent.time` | `746c7b9309c7c6306e0d1789148baf61ded562e2685a7165bd9fa52b55d995a7` |
| `logs/independent.log` | `88ded44b7c4f1e3c0bccc4f287fc59f9ea92446939d8d047b3c980153e243380` |
| `audit_receipts/closure_attempt.json` | `33bcfa3dd14605ce09119b38f9fd0c5f35a083c3492876064b7b2b9b67a36d8c` |
| `audit_receipts/closure_command.json` | `10ffaff0f24cdbcb0d7cff413ad5d7684c1779f3a3fe167fdbb3ac8142a1920b` |
| `profiles/closure.time` | `e227a256b6c8d650084aed0b32fb03990fd53eb853269352b7cae96e8300729d` |
| `logs/closure.log` | `550cdef2724ea4a5e5c56c3feab3cb336724a8a834101567b8fa55f1fbc21d94` |
| `audit_receipts/verification_attempt.json` | `605e5c65e7d3a805f3644d4d739f20871758bf1347e97b12f0c10d9e3bb0bd61` |
| `audit_receipts/verification_command.json` | `cb53e54684ba5a5fde3bd27cfd38a4b8f3bbf3fb44302f3a8049ec663f5095c4` |
| `profiles/verification.time` | `60e3db5ec909ed52b0591fcee37be9892d2643812b837d33d35ea7d9ef172fc8` |
| `logs/verification.log` | `d5d05d223e46da05d0e2cb125987171dfcbecf901ae478171d8f8ffa010813cc` |
| `audit_sources/native_controller.py` | `d13cf09b8df6510085e709cb129d3331a1502829da160c7faeaa941fd66daf53` |
| `audit_sources/publication_controller.py` | `bdc4cc9180510fab9398b373a0ce73a1f2b4d7f4f976fabd6d99a58d860c9b85` |
| `audit_sources/final_controller.py` | `5a239e4572cb4a3b97283a72e9d0687f6b4703004f280871511d3c2a9b0b88b7` |
