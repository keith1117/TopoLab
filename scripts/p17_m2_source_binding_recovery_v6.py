"""Explicit prospective V31 entry; historical entrypoints keep old defaults."""
import importlib.util
import os
import sys
from pathlib import Path

path = Path(__file__).with_name('p17_m2_input_continuation.py')
spec = importlib.util.spec_from_file_location('p17_m2_input_continuation', path)
if spec is None or spec.loader is None:
    raise ValueError('published V31 profile unavailable')
profiles = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = profiles
spec.loader.exec_module(profiles)
subject = profiles.profile('recovery', profiles.V31_INPUT)

if __name__ == '__main__':
    os.umask(0o077)
    try:
        raise SystemExit(subject.main())
    except Exception as error:
        print(subject.canonical({'status': 'STOP_NO_RETRY', 'stage': 'recovery_control',
            'original_source_reads': 0,
            'publication_failure': getattr(error, 'recovery_publication_failure', None),
            **subject.load('p17_m2_source_binding').error_context(error)}).decode(), end='')
        raise SystemExit(1) from error
