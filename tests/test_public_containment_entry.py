"""Actual public entry must cover final filing and owned controller faults."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts/public_containment_entry.py"


def test_expired_entry_never_opens_plan(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(ENTRY), "--plan", str(tmp_path / "missing"),
         "--sha256", "0" * 64, "--requested-ms", str(time.time_ns() // 1_000_000 - 60000)],
        start_new_session=True, capture_output=True, timeout=3,
    )
    assert result.returncode == 2
    assert b"expired original entry" in result.stderr
    assert not list(tmp_path.iterdir())


def test_harmless_preflight_has_actual_isolated_return(tmp_path):
    output = tmp_path / "preflight.json"
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(ENTRY), "--preflight", str(output),
         "--requested-ms", str(time.time_ns() // 1_000_000)],
        start_new_session=True, capture_output=True, timeout=3,
    )
    assert result.returncode == 0, result.stderr
    value = json.loads(output.read_bytes())
    assert value["pid"] == value["pgid"] == value["sid"]
    assert value["guardian"]["process_group"] == value["pid"]
    assert value["guardian_future_cancel_reap"] == "PENDING_ACTUAL_ENTRY_EXIT0"
    assert value["Original_reads"] == value["Foundation_helpers"] == 0
    assert value["guardian"]["deadline_unix_ns"] == value["start_unix_ns"] + 45 * 10**9
    assert result.stdout == b""
    assert not os.path.exists(tmp_path / "payload")


def test_final_filing_failure_retains_actual_nonzero(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(ENTRY), "--preflight", str(tmp_path),
         "--requested-ms", str(time.time_ns() // 1_000_000)],
        start_new_session=True, capture_output=True, timeout=3,
    )
    assert result.returncode != 0
    assert b"FileExistsError" in result.stderr


def test_guardian_kills_entry_blocked_in_last_fsync(tmp_path):
    # FIFO opening is a real blocking IO at the same final-write boundary.
    # Copy only the public tools and replace the public filesystem boundary;
    # no role, Docker, native source or historical evidence is entered.
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("public_containment_entry.py", "public_deadline_guardian.py",
                 "public_containment_driver.py"):
        (scripts / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    driver = scripts / "public_containment_driver.py"
    driver.write_text(driver.read_text().replace('.open("xb")', '.open("wb")'))
    target = tmp_path / "blocked-filing"
    os.mkfifo(tmp_path / "blocked-filing.pending")
    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(scripts / ENTRY.name), "--preflight", str(target),
         "--deadline-unix-ns", str(time.time_ns() + 1_000_000_000),
         "--deadline-monotonic-ns", str(time.monotonic_ns() + 1_000_000_000)],
        start_new_session=True, capture_output=True, timeout=3,
    )
    assert result.returncode == -9, result.stderr
    assert time.monotonic() - start < 3


def run_fake_entry(tmp_path, *, late_controller_fault=False):
    import hashlib

    source_root = ROOT
    if late_controller_fault:
        source_root = tmp_path / "declared-public-source-copy"
        (source_root / "scripts").mkdir(parents=True)
        for name in ("public_containment_entry.py", "public_containment_driver.py",
                     "public_deadline_guardian.py", "public_worker_deadline.py",
                     "public_containment_audit.py"):
            (source_root / "scripts" / name).write_bytes((ROOT / "scripts" / name).read_bytes())
        path = source_root / "scripts/public_containment_driver.py"
        text = path.read_text()
        needle = '            new_json(output / "controller-kill-request.json",'
        assert text.count(needle) == 1
        path.write_text(text.replace(needle, "            time.sleep(9)\n" + needle))
    # A declared fake Docker CLI tests public argv/process/file integration only.
    # It supplies no kernel namespace or actual Docker acceptance evidence.
    fake = tmp_path / "fake-docker"
    fake.write_text("#!" + sys.executable + r'''
import hashlib, json, pathlib, sys, time
root=pathlib.Path(__file__).parent
args=sys.argv[2:]
cmd=args[0]
def read(cid): return json.loads((root/(cid+'.json')).read_bytes())
def write(value):
    path=root/(value['Id']+'.json')
    temp=root/(value['Id']+'.'+str(__import__('os').getpid())+'.tmp')
    temp.write_text(json.dumps(value)); temp.replace(path)
if cmd=='create':
    name=args[args.index('--name')+1]
    cid=hashlib.sha256(name.encode()).hexdigest()
    image=next(x for x in args if x.startswith('sha256:'))
    labels=dict(x[len('--label='):].split('=',1) for x in args if x.startswith('--label='))
    payload=args[args.index(image)+1:]
    value=dict(Id=cid,Name='/'+name,Image=image,Mounts=[],
      Config=dict(Image=image,Entrypoint=None,Cmd=payload,Labels=labels),
      HostConfig=dict(Privileged=False,PidMode='',CgroupnsMode='private',CapAdd=None,
        CapDrop=['CAP_SYS_ADMIN'],SecurityOpt=['no-new-privileges'],Binds=None,
        Memory=3221225472,MemorySwap=3221225472,NanoCpus=1000000000,PidsLimit=256,
        NetworkMode='none',RestartPolicy=dict(Name='no'),AutoRemove=False),
      State=dict(Running=False,Pid=0,ExitCode=0,Status='created'))
    write(value); print(cid)
else:
    cid=args[-1]; value=read(cid)
    if cmd=='inspect': print(json.dumps([value]))
    elif cmd=='start':
        value['State']=(dict(Running=False,Pid=0,ExitCode=23,Status='exited')
          if value['Config']['Cmd'][-1]=='pid1-death'
          else dict(Running=True,Pid=123,ExitCode=0,Status='running'))
        write(value); print(cid)
    elif cmd=='kill':
        value['State']=dict(Running=False,Pid=0,ExitCode=137,Status='exited')
        write(value); print(cid)
    elif cmd=='wait':
        for _ in range(1000):
            value=read(cid)
            if value['State']['Status']=='exited': break
            time.sleep(.01)
        print(value['State']['ExitCode'])
    elif cmd=='logs':
        print(json.dumps(dict(role='pid1',pid=1,ppid=0,pgid=1,sid=1,namespace='pid:[99]')))
        print(json.dumps(dict(role='detached-grandchild',pid=3,ppid=1,pgid=3,sid=3,
                              namespace='pid:[99]')))
    else: raise SystemExit(72)
''')
    fake.chmod(0o700)
    names = ["public_containment_entry.py", "public_containment_driver.py",
             "public_deadline_guardian.py", "public_worker_deadline.py",
             "public_containment_audit.py"]
    pins = {name: hashlib.sha256((source_root / "scripts" / name).read_bytes()).hexdigest()
            for name in names}
    modes = ["pid1-death", "host-controller-death"]
    plan = dict(schema="topolab.public-containment-static.v1",
                identity="topolab.container-full60-input-admission.20261116.v1", FULL=60,
                image="sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a",
                modes=modes, binding_state="FROZEN_REVIEWED_PUBLISHED", Original_reads=0,
                fixture_authority="DECLARED_FAKE_CLI_SOFTWARE_ONLY",
                owner_budget_sha256="cfa8ac55d9f1879fdc9242db76b78c6661f38649e97162d0fe39339600629ec0",
                Foundation_helpers=0, attempt=1, docker=str(fake),
                python=sys.executable,
                python_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                docker_sha256=hashlib.sha256(fake.read_bytes()).hexdigest(),
                source_sha256=pins, driver_sha256=pins["public_containment_driver.py"],
                cwd=str(source_root), output=str(tmp_path / "output"),
                global_end_unix_ns=time.time_ns() + 8 * 3600 * 10**9,
                cases=[dict(mode=mode, name="topolab-full60-20261116-fixture-" + str(i),
                            owner=str(i + 1) * 64) for i, mode in enumerate(modes)])
    raw = (json.dumps(plan, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path = tmp_path / "plan.json"
    path.write_bytes(raw)
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(source_root / "scripts" / ENTRY.name),
         "--plan", str(path), "--sha256",
         hashlib.sha256(raw).hexdigest(), "--requested-ms", str(time.time_ns() // 1_000_000)],
        cwd=source_root, start_new_session=True, capture_output=True, timeout=50,
    )
    return result, tmp_path / "output"


def test_both_cases_observe_actual_helper_entry_and_work_exits(tmp_path):
    result, output = run_fake_entry(tmp_path)
    assert result.returncode == 0, result.stderr.decode()
    report = json.loads((output / "driver/driver-before-return.json").read_bytes())
    assert report["status"] == "TWO_SUBCASES_RETURNED"
    for i, expected in enumerate([0, -9]):
        row = report["cases"][i]
        assert row["helpers"]["controller"]["actual_exit"] == 0
        assert row["helpers"]["watchdog"]["actual_exit"] == 0
        actual = json.loads((output / f"driver/{i}/controller-work-actual.json").read_bytes())
        assert actual["work_actual_exit"] == expected
        assert actual["work_reaped"] is True
        assert actual["prescribed_fault_requested"] is (i == 1)
        assert row["stopped_state"]["Pid"] == 0
        assert row["container_removed"] is False


def test_watchdog_termination_before_controller_death_cannot_pass(tmp_path):
    result, output = run_fake_entry(tmp_path, late_controller_fault=True)
    assert result.returncode == 1, result.stderr.decode()
    report = json.loads((output / "driver/driver-before-return.json").read_bytes())
    assert report["status"] == "STOP"
    case = report["cases"][1]
    assert case["controller_work_actual"]["work_actual_exit"] == -9
    assert case["post_controller_death_state"]["ExitCode"] == 137
    assert case["primary_error"]["reason"] == (
        "container stopped before observed controller work death")


def test_source_bound_entry_ignores_same_size_same_mtime_bytecode(tmp_path):
    import py_compile

    for name in (ENTRY.name, "public_deadline_guardian.py"):
        (tmp_path / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    driver = tmp_path / "public_containment_driver.py"
    source = '''import json,os
MARKER='OLD'
def new_json(path,value):
 value['loader_marker']=MARKER
 with open(path,'xb') as stream:
  stream.write((json.dumps(value)+'\\n').encode());stream.flush();os.fsync(stream.fileno())
'''
    driver.write_text(source)
    initial = driver.stat()
    py_compile.compile(str(driver), doraise=True)
    driver.write_text(source.replace("'OLD'", "'NEW'"))
    os.utime(driver, ns=(initial.st_atime_ns, initial.st_mtime_ns))
    output = tmp_path / "actual.json"
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(tmp_path / ENTRY.name), "--preflight", str(output),
         "--requested-ms", str(time.time_ns() // 1_000_000)],
        start_new_session=True, capture_output=True, timeout=3,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_bytes())["loader_marker"] == "NEW"


def test_cleanup_kill_denial_keeps_guardian_until_owned_work_stops(tmp_path):
    import fcntl
    import hashlib

    for name in (ENTRY.name, "public_deadline_guardian.py"):
        (tmp_path / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    driver = tmp_path / "public_containment_driver.py"
    driver.write_text(r'''
import fcntl,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OriginalPopen=subprocess.Popen
class DeniedKill(OriginalPopen):
 def kill(self): raise PermissionError('PUBLIC_INJECTED_KILL_DENIAL')
subprocess.Popen=DeniedKill
def pinned_json(path,expected): return json.loads(Path(path).read_bytes())
def validate_plan(plan): pass
def need(condition,reason):
 if not condition: raise ValueError(reason)
def error_record(error): return dict(type=type(error).__name__,reason=str(error))
def new_json(path,value):
 with Path(path).open('xb') as stream:
  stream.write((json.dumps(value)+'\n').encode());stream.flush();os.fsync(stream.fileno())
class Cli:
 def __init__(self,plan): pass
 def remaining(self):
  if (ROOT/'work-ready').exists(): raise RuntimeError('PUBLIC_INJECTED_WORK_FAILURE')
  return 1
if __name__=='__main__':
 stream=(ROOT/'work.lock').open('w');fcntl.flock(stream,fcntl.LOCK_EX)
 (ROOT/'work-ready').write_text('ready')
 while True: time.sleep(.01)
''')
    end_unix, end_mono = time.time_ns() + 2 * 10**9, time.monotonic_ns() + 2 * 10**9
    pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (driver, tmp_path / "public_deadline_guardian.py")}
    ticket = dict(plan=dict(start_unix_ns=end_unix - 45 * 10**9,
                            start_monotonic_ns=end_mono - 45 * 10**9, source_sha256=pins),
                  case=dict(mode="host-controller-death"), output=str(tmp_path), cid="a" * 64)
    path = tmp_path / "ticket.json"
    path.write_text(json.dumps(ticket))
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(tmp_path / ENTRY.name), "--controller", str(path),
         "--sha256", "0" * 64, "--deadline-unix-ns", str(end_unix),
         "--deadline-monotonic-ns", str(end_mono)],
        start_new_session=True, capture_output=True, timeout=3,
    )
    assert result.returncode == 1, result.stderr
    receipt = json.loads((tmp_path / "controller-work-actual.json").read_bytes())
    assert receipt["work_reaped"] is False
    assert receipt["primary_error"]["reason"] == "PUBLIC_INJECTED_WORK_FAILURE"
    assert receipt["secondary_errors"][0]["reason"] == "PUBLIC_INJECTED_KILL_DENIAL"
    with (tmp_path / "work.lock").open() as stream:
        deadline = time.monotonic() + 1
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                assert time.monotonic() < deadline, "guardian was cancelled with live owned work"
                time.sleep(.01)


def test_audit_cli_files_library_result_before_actual_entry_exit(tmp_path):
    for name in (ENTRY.name, "public_deadline_guardian.py"):
        (tmp_path / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    (tmp_path / "public_containment_driver.py").write_text('''import json,os,time
GLOBAL_END=time.time_ns()+8*3600*10**9
def need(condition,reason):
 if not condition: raise ValueError(reason)
def error_record(error): return dict(type=type(error).__name__,reason=str(error))
def new_json(path,value):
 with open(path,'xb') as stream:
  stream.write((json.dumps(value)+'\\n').encode());stream.flush();os.fsync(stream.fileno())
''')
    (tmp_path / "public_containment_audit.py").write_text('''import hashlib
from pathlib import Path
def audit_file(path,package_sha,public_static_sha):
 assert package_sha=='0'*64 and public_static_sha=='1'*64
 root=Path(__file__).parent
 names=['public_containment_driver.py','public_containment_audit.py','public_deadline_guardian.py']
 return dict(status='DECLARED_PUBLIC_LIBRARY_BOUNDARY_ONLY',
  expected_source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                         for name in names},
  audit_output=str(root/'audit-result'),input_accepted=False)
''')
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(tmp_path / ENTRY.name), "--audit",
         str(tmp_path / "declared-package-label-only"), "--sha256", "0" * 64,
         "--public-static-sha256", "1" * 64, "--requested-ms", str(time.time_ns() // 1_000_000)],
        start_new_session=True, capture_output=True, timeout=3,
    )
    assert result.returncode == 0, result.stderr
    path = tmp_path / "audit-result/independent-audit-before-return.json"
    value = json.loads(path.read_bytes())
    assert value["verdict"]["status"] == "DECLARED_PUBLIC_LIBRARY_BOUNDARY_ONLY"
    assert value["guardian_future_cancel_reap"] == "PENDING_ACTUAL_ENTRY_EXIT0"
    assert value["work_return"] == 0 and value["primary_error"] is None
    assert value["verdict"]["input_accepted"] is False
    assert result.stdout == b""


def test_post_reap_failure_exits_without_unprotected_traceback(tmp_path):
    for name in (ENTRY.name, "public_deadline_guardian.py", "public_containment_driver.py"):
        (tmp_path / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    guardian = tmp_path / "public_deadline_guardian.py"
    with guardian.open("a") as stream:
        stream.write('''
_original_cancel=cancel_and_reap
def cancel_and_reap(guard):
 _original_cancel(guard)
 raise RuntimeError('PUBLIC_INJECTED_FAILURE_AFTER_ACTUAL_REAP')
''')
    result = subprocess.run(
        [sys.executable, "-I", "-u", str(tmp_path / ENTRY.name), "--preflight",
         str(tmp_path / "filed-before-reap.json"),
         "--requested-ms", str(time.time_ns() // 1_000_000)],
        start_new_session=True, capture_output=True, timeout=3,
    )
    assert result.returncode == 1
    assert result.stderr == b"" and result.stdout == b""
    assert (tmp_path / "filed-before-reap.json").is_file()
