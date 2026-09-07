from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from simulator.app_factory import create_app
from simulator.cstore import _identifier_mismatches
from simulator.simlib import storage


def test_welcome_accessible_without_student_code():
    app = create_app()
    app.testing = True

    client = app.test_client()
    res = client.get('/welcome')
    assert res.status_code == 200


def test_gate_redirects_to_welcome_without_student_code():
    app = create_app()
    app.testing = True

    client = app.test_client()
    res = client.get('/', follow_redirects=False)
    assert res.status_code in {301, 302, 303, 307, 308}
    assert res.headers['Location'].endswith('/welcome')


def test_index_accessible_with_student_code():
    app = create_app()
    app.testing = True

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['student_code'] = 'SUS-TEST'

    res = client.get('/')
    assert res.status_code == 200
    assert b'Radiologie Workflow Simulator' in res.data


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [sys.executable, '-c', code],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )


def test_import_app_package_mode():
    res = _run_python(
        "import simulator.app as a; print(len(list(a.app.url_map.iter_rules())));",
    )
    assert res.returncode == 0, res.stderr
    assert int(res.stdout.strip().splitlines()[-1]) > 0


def test_import_app_script_mode():
    res = _run_python(
        "import sys; sys.path.insert(0, 'simulator'); import app as a; print(len(list(a.app.url_map.iter_rules())));",
    )
    assert res.returncode == 0, res.stderr
    assert int(res.stdout.strip().splitlines()[-1]) > 0


def test_uploaded_dicom_identifiers_match_selected_worklist_item():
    class Dataset:
        PatientID = 'SUS-TEST-007'
        AccessionNumber = 'SUS-TEST-ACC001'

    assert _identifier_mismatches(Dataset(), 'SUS-TEST-007', 'SUS-TEST-ACC001') == []
    assert _identifier_mismatches(Dataset(), 'SUS-TEST-008', 'SUS-TEST-ACC001') == ['PatientID']


def test_admin_dashboard_requires_login_and_shows_session_progress(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, 'DATA_DIR', str(tmp_path))
    monkeypatch.setattr(storage, 'SESSIONS_FILE', str(tmp_path / 'sessions.json'))
    monkeypatch.setattr('simulator.simlib.admin_auth.admin_enabled', lambda: True)
    storage.save_session_codes(['SUS-TEST'])
    storage.upsert_patient('SUS-TEST', 'BOND^JAMES', 'SUS-TEST-007')
    storage.append_activity('SUS-TEST', 'HL7 ADT: Patient aufgenommen', 'PID=SUS-TEST-007')

    app = create_app()
    app.testing = True
    client = app.test_client()

    anonymous = client.get('/admin')
    assert b'Lernfortschritt nach SuS-Session' not in anonymous.data

    with client.session_transaction() as sess:
        sess['is_admin'] = True
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'Lernfortschritt nach SuS-Session' in response.data
    assert b'SUS-TEST' in response.data
    assert b'HL7 ADT: Patient aufgenommen' in response.data
