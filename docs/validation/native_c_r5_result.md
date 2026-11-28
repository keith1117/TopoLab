# R5 formal B and the fixed 18-case C panel

On the 18 exposed development cases, C completed production and independent numerical review. The fixed H/17 candidate failed 9 of 11 registered predicates. Quality checks rejected three large-grid attempts, and all three used fallback. H/17 exceeded the target timing threshold on both registered timing measures. The numerical auditor checked all 360 rows. Its numerical result was `FAIL_SCIENCE_GATE`. The final command exited 0, and a separate checker verified the returned decision. Uniform remains the default. The H/17 confirmation on independent physical cases remains closed.

## Scientific release and input

R5 used scientific revision `cfe17999406abc1627734cc4f652d7cd636b557b`, contract SHA-256 `dc658f4ef38d9af93b6dd0bc80f7eb29986c5e3a967fa0851cd09156e88c2b6d` and the 445-file software manifest `edba26942a5bc2dc65aeab7ae85c2c89ce6c0030472308bafd02cbe297c7741c`. All four jobs passed on the PR and on the protected merge. On that merge the independent reviewer exercised the public row writer, checked the failure paths and reconstructed the journal. The exact-merge release command returned 0. Its original envelope has SHA-256 `f5f615b6a1d83a30a859227d134552e80ba10de0323f99a577b607abc6e41ca3`. [PR 276](https://github.com/keith1117/TopoLab/pull/276) · [PR checks](https://github.com/keith1117/TopoLab/actions/runs/46105250359) · [Main checks](https://github.com/keith1117/TopoLab/actions/runs/46108423763)

The B1 certificate supplied plan `d26d69bb62ff1488e12a52f2872f07ce00eac92eb4bd30413b53925411d4f739` and version `94e1ccdd7629cfbb697797da4235351c1fdefbcde8c40085dd0876ab3b6b23a7`. The owner assigned the exhausted quotas and R1-only clauses to the sealed B4.51 contract. R5 used its own one-shot reservations, clocks and reader slot. [Owner ruling and contract](../planning/native_c_owner_authorization.md) · [R4 refusal and ledger](native_c_reservation_approval_stop.md)

## Formal B and producer handoff

The single R5 B returned `PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL`. Its caller observed the terminal after 65.242 seconds. The complete measured charge was 75.242 seconds and the booked charge was 180 FULL seconds. Peak RSS was 1,115,504,640 bytes under the 4 GiB limit. Independent replay verified the raw terminal, exit, clocks, release and input version at exit 0. The raw B clock return has SHA-256 `be12735ae3134e03c59ab40b70dd634a62a44b40a1a25da25ab2398e6595eb50`, and the original independent check has SHA-256 `fb90a51d6dd1732ad33fb9dd408f9bcaabdf6c8377135aa3ed7eef1d4c9b8eec`.

Normal platform approval admitted the C producer reservation. The producer filed 18 reference packets and 342 query packets with matching cost records. The controller journal retained all 265 original tool replies. Its reader acknowledgement reached the caller and released the R5 producer lease. The independent reviewer verified the original acknowledgement before reserving the numerical auditor. The acknowledgement has SHA-256 `b43ff48b69182ce8e175489005611e9788c274de0fbca744d6202c8a72045ac2`. The independent handoff check has SHA-256 `47d1b71ce0e4290b3240a7c6e54395019798ddf75a27e8cf8dfcb8c968790ef2`.

## Independent numerical result

The numerical auditor checked all 18 fresh same-host uniform references and 342 queries, including the independent terminal solves. The auditor logged 5,538 terminal and window analyses, 988 homotopy prefix and transition analyses and 1,056 nearest-neighbor label reanalyses. The independent final checker returned `INDEPENDENT_COMPLETE_C_ORIGINAL_AND_OUTCOME_VERIFIED` at exit 0 with empty stderr. It verified the original decision packet, resource evidence and released reader slot against the formal scientific commit and contract. The raw final tool envelope has SHA-256 `9dedf93a692d2fdda256c93374bbd534f0a061bd1d5447245324b89e3b471ef7`. The independent check in `independent-formal-C-terminal-check-actual.json` has SHA-256 `e99c396fb4722d611a47f1cdad752aabe3d1a0614c613d2be558638312495053`.

For each population, the mean is the arithmetic mean of case-level charged-time ratios against the matched uniform run. The aggregate is the sum of candidate charges divided by the sum of uniform charges. The charges include fallback work. Ratios below 1 indicate less charged time than uniform.

| Fixed H/17 population | Failed attempts | Mean case ratio | Aggregate ratio | Registered timing limit |
| --- | ---: | ---: | ---: | --- |
| All 18 | 3 | 1.140286 | 1.181889 | Control comparisons |
| 13 targets | 3 | 1.309997 | 1.312840 | Both ≤ 1.00 |
| Grid 12 × 6 × 3 | 0 | 0.755339 | 0.753484 | Both ≤ 0.90 |
| Grid 24 × 12 × 6 | 3 | 1.217276 | 1.188250 | Both ≤ 0.90 |

Two predicates passed. The run reproduced the fixed plain-P/17 counterexample and retained both old small-grid z-direction negative controls. The remaining nine predicates failed.

- **Quality and reliability (4).** Fixed H/17 failed the zero-failure, zero-fallback gate. The panel did not repair all seven designated historical case/seed predicates, preserve all 49 historical P acceptances, or preserve all matched plain-P and P-keep acceptances.
- **Speed and attribution (4).** H/17 missed both ratios on the 13 targets and failed the two-scale threshold on the large grid. It also failed the required superiority predicates for the fixed controls and for W/17. W/17 had three failed attempts and mean and aggregate ratios of 0.895766 and 0.852761.
- **Seed generalization (1).** None of H/17, H/29 or H/43 passed its registered seed gate. H/29 and H/43 had five and two failed attempts, respectively. The contract required at least two passing seeds including 17.

## Diagnosis on the exposed cases

The three large-grid attempts satisfied the registered physical convergence and volume conditions. Their terminal compliance ratios against the new uniform references were 1.001752 on `033f380c`, 1.002060 on `55c1b3e6`, and 1.001207 on `838e2ccc`. All exceeded the 1.001 quality limit. Across the registered comparisons, H preserved 43 of the 49 historical P acceptances and passed two of the seven designated case/seed combinations.

The three fallback runs added 74.833 seconds. Subtracting their entire recorded wall time while keeping every failed attempt in the comparison gives a lower bound on the cost of a repair that only removes fallback. The resulting mean and aggregate ratios are 1.1114 and 1.0730 on the 13 targets, and 1.0452 and 0.9913 on the large grid. Both populations still exceed their respective limits. On the ten directly accepted targets alone, the aggregate ratio is 1.2407. Input preparation across all 13 targets took 0.328 seconds.

R5's eight-step stages at each of the first two homotopy exponents and the earlier B4.30 reflection approach both retained the difficult `55c1b3e6` case and the target-speed blocker. The route review closed the fixed 8+8 H/17 candidate. The exposed records do not support freezing a specific successor. Uniform remains the default and confirmation samples remain unopened. The paired diagnosis is under `h17-exposed-diagnosis-20261128-a1`. Its quality report has SHA-256 `c0b9c5e1720b0ea4bd8c962afcc6dfce8867309d0ea6319b9859713cb0229d4b`, and the timing analysis output has SHA-256 `9e5e1927c0d65111d7628c8649cf41ad6a8303839572e09e4221ad207354d391`. The independent diagnostic signoff has SHA-256 `b2896ebc4d96778d24ce0d975aefc5c6e1c646d0f74774fdc41bd576e7f6eab9`, and the route review has SHA-256 `ef6feb4e3ac09e29ea2fe55501f5a848db70c189e7423ab161e4bd78863ecfab`. [Prior reflection result](b4_30_paid_continuation.md) · [Registered predicates](../planning/p17_m2_native_homotopy_proposal.md) · [Confirmation rules](../planning/native_c_row_return_authorization.md)

## Accounts and custody

| Account | Measured complete charge (s) | Peak RSS (bytes) | Booked FULL seconds |
| --- | ---: | ---: | ---: |
| B | 75.242 | 1,115,504,640 | 180 |
| C producer | 8,550.449 | 1,761,591,296 | 10,800 |
| C numerical auditor | 1,933.105 | 1,796,210,688 | 3,600 |
| C shared preparation, control and closeout | 174.591 | 654,098,432 | 180 |

The formal ledger booked 14,760 FULL seconds, including 14,580 for C. All four accounts closed with zero unused balance. The cumulative known floor rose from 451,899 to **466,659 FULL seconds**, plus historical unpriced costs. R5's two scientific readers acknowledged release. The R2 and R3 stopped scientific leases remain `HELD_NO_MANUAL_RELEASE`. R4 acquired none. The B1 lease remains released and the seven historical leases remain held.

The paired R5 terminal archives contain 37,156 indexed files totaling 571,195,989 bytes per copy. The index `formal-BC-terminal-index.json` has SHA-256 `dc5c5acdf3373b187dda3894e99d2198f05534e00d99a42edfa9c7ab0632582c`. The closed `formal-terminal-ledger.json` has SHA-256 `047ba3b0efe4d6dcaf6339719e11ecf069f7cf012af275c5e433eef80accaa98`. Both are under the external `native-bc-entry-20261127-r5` evidence root and its `-backup` sibling.
