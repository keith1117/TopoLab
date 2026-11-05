"""Explicit prospective V35 entry; historical entrypoints keep old defaults."""
import importlib.util
import os
import sys
from pathlib import Path

path = Path(__file__).with_name('p17_m2_input_continuation.py')
spec = importlib.util.spec_from_file_location('p17_m2_input_continuation', path)
if spec is None or spec.loader is None:
    raise ValueError('published V35 profile unavailable')
profiles = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = profiles
spec.loader.exec_module(profiles)
subject = profiles.profile('registered', profiles.V35_INPUT)

if __name__ == '__main__':
    os.umask(0o077)
    try:
        raise SystemExit(subject.main())
    except Exception as error:
        print(subject.producer.canonical({'status': 'STOP_NO_RETRY',
            'primary_error': {'type': type(error).__name__,
                              'reason': str(error)}}).decode(), end='')
        raise SystemExit(1) from error
