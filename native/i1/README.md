# I1 bounded native query software

Opt-in software capability under the [I1 contract](../../docs/planning/i1_bounded_native_software_contract.json)
and [protocol](../../docs/planning/i1_bounded_native_software_protocol.md). It does
not replace TopoLab's default solver, carry a research-input grant, repair P/17,
or admit a scientific pilot. Full v2 and its original Gates remain open.

`query.c` implements the frozen Hex8/filter/projection/OC equations, the13-channel
ContextCNN forward graph, fixed8/8/p=3 homotopy, plain controls, physics and
streaming10-channel nearest-neighbor initialization, legacy P-keep continuation,
and failure-preserving uniform fallback. Selected and performed updates are
separate; every attempted analysis, transition and re-solve is charged in counts.
There is no fitting, schedule search, reflection or H polish. Two mesh bounds are
12×6×3 and24×12×6; smaller public N1 software cases are accepted for regression.
The fixed model-role selector returns C/P/W or same-seed S. The public interface
receives an explicitly selected checkpoint; it does not authenticate old role
membership or discover/checkpoint-select through an index. Future literal hashes,
role views and portability remain separately unregistered.

`audit.c`, freshly authored by the independent audit role, derives Hex8 stiffness
from analytic tensor-product integrals of the one-dimensional basis and solves
with unit-diagonal LDLᵀ. It calls no candidate numerical/filter/classification/cost
helper. `audit_main.c` reconstructs terminal windows and checks counts, density,
volume, penalty and compliance. The independent audit role also freshly authored
`controller.c`; it had read the primary draft, so the distinct authorship is
explicitly not blinded. No draft implementation was reused. The primary
separately inspected these roles. Source review is not complete binary/resource
admission. It is a public terminal check, not full
B4 reference/policy/cost acceptance.

The Linux x86-64 programs have their own `_start`, fixed global storage and
explicit syscalls, without libc/libm/Torch/SciPy/BLAS or an ELF interpreter.
They reset floating-point rounding state and install syscall filters. JSON depth,
tokens and strings, safetensors shapes/offsets/finite values, read/write counts,
and NN population<=528 are bounded. B3's escaped `topolab` metadata is an opaque
bounded string; no pointer is followed. The controller hashes/copies each named
child into an immutable sealed executable before fork/execveat, waits for exits,
preserves failed output prefixes and refuses to overwrite an output. Sealed
carriers, image buffers and the controller's fork copy belong in the bound.

Build into a **new** ignored/output directory on the selected Ubuntu24.04 x86-64
surface:

```bash
python3 scripts/i1_native_build.py build/i1-public
python3 scripts/i1_native_inspect.py build/i1-public
env -i build/i1-public/i1-controller --public-preflight \
  build/i1-public/i1-query build/i1-public/i1-audit
```

Run `uv run pytest tests/test_i1_native.py` for public numerical/parser/failure
regression. On Linux it also compiles and executes the actual three freestanding
roles; on other hosts that one platform test is explicitly skipped. The full
repository regression remains mandatory. The manual
`I1 native software preflight` workflow refuses a source that is not clean,
merged current main with successful normal CI. It reads no research input and
uploads only this run's new software metadata/binaries/logs. The direct C root
bounds and wipes its incoming CI environment, includes that initial storage in
startup obligations, and records no environment values. Child environments are
empty. Before root entry the workflow verifies a non-piped core pattern; native
setup disables dumping. Actual selected auxv/limits/maps, argv/cwd, one-thread
observation and executable self hashes accompany source/ELF/frame evidence.

The `--public-case`, `--public-terminal`, `--public-run`,
`--public-evaluate` and `--public-evaluation` modes are developer
software interfaces, not production entrypoints. JSON schema
`topolab.i1.public-case.v1` has exactly14 fields demonstrated in the test factory;
method is uniform/uniformH/H/plainP/Pkeep/C/W/physics/NN. Physical scalar/length
values are16-digit IEEE754 binary64 hex bit strings, preserving case bits without
a library decimal conversion; mesh/load indices and limits remain JSON integers.
Public model inputs have
the fixed10 F32 tensor descriptors and optional bounded B3 metadata. NN stream
`I1NN0001` has uint32 count/elements, then repeated75-byte NUL-terminated IDs,
10N float32 inputs and N float32 labels, in increasing ID order. The wire is
little-endian x86-64 only. No such stream of old labels is created or granted.

Public result `I1PUB003` contains the9993960-byte declared history, followed
by6825 float64 displacement and6825 reaction slots in physical node order. The
independent binary case layout is120 bytes. These developer wire layouts
are checked by compile-time assertions and tests, not a B3 artifact relabeling.
Unpopulated history slots have no evidential meaning. A partial prefix is never
a p=3 terminal certificate. Scalar reference quality and complete charged wall
accounting are not certified by the public terminal interface. A public
`I1EVAL01` bundle adds four int32 fields (success/fallback/retained attempt
status/evaluation return), the complete attempted history, then the unchanged
terminal frame when evaluation returns zero. The independently parsed public
reference is one positive finite binary64 scalar, exactly8 bytes.
Failed evaluation preserves its header/attempt prefix plus `I1FAIL01` and the
failed returned/fallback history, then exits66. Valid-weight inference overflow
and a failed physics initializer are retained attempts and enter full fallback;
malformed inputs remain input rejection. A later
successful uniform fallback never clears the attempt flag. The checker verifies
both histories, unchanged quality thresholds and fresh uniform initialization.
This public scalar is not an old reference-access grant or a scientific result.

`inspection.json` records actual ELF segments, helpers, compiler stack records
and origins, with **UNKNOWN** admission. ELF/static capacities, snapshots, syscall
filters and software CI do not substitute for a complete independently reviewed
startup/native/stack/lifetime/overlap bound and actual independent preflight.
No old/full-fit memory gap is filled by this new software.
