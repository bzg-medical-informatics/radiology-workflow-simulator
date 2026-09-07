from __future__ import annotations

import datetime

from flask import session
from typing import Optional

try:
    from simlib import admin_auth, dicom_receiver, storage
    from simlib.students import get_student_code
except ModuleNotFoundError:  # package mode
    from .simlib import admin_auth, dicom_receiver, storage
    from .simlib.students import get_student_code


def _admin_user() -> str:
    return admin_auth.admin_user()


def _admin_enabled() -> bool:
    return admin_auth.admin_enabled()


def _is_admin() -> bool:
    return admin_auth.is_admin()


def _require_admin():
    return admin_auth.require_admin()


def _load_patients(code: str) -> list:
    return storage.load_patients(code)


def _save_patients(code: str, patients: list) -> None:
    storage.save_patients(code, patients)


def _patient_exists(code: str, pid: str) -> bool:
    return storage.patient_exists(code, pid)


def _get_patient(code: str, pid: str) -> Optional[dict]:
    return storage.get_patient(code, pid)


def _upsert_patient(code: str, name: str, pid: str) -> None:
    storage.upsert_patient(code, name, pid)


def _update_patient_last_exam(
    code: str,
    pid: str,
    *,
    accession_number: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
) -> None:
    storage.update_patient_last_exam(
        code,
        pid,
        accession_number=accession_number,
        description=description,
        status=status,
    )


def _update_patient_last_lab(
    code: str,
    pid: str,
    *,
    value: float,
    unit: str,
    status: str,
    color: str,
) -> None:
    storage.update_patient_last_lab(code, pid, value=value, unit=unit, status=status, color=color)


def _set_active_pid(pid: str) -> None:
    """Remember the patient currently being worked on (for the cross-page ID-tracking widget)."""
    pid = (pid or '').strip()
    if not pid:
        return
    session['active_pid'] = pid
    session.modified = True


def _load_reports(code: str) -> list:
    return storage.load_reports(code)


def _save_reports(code: str, reports: list) -> None:
    storage.save_reports(code, reports)


def _reports_index_by_pid(code: str) -> dict:
    return storage.reports_index_by_pid(code)


def _viewer_moved_studies() -> set[str]:
    """Return StudyInstanceUIDs for which this session has triggered a C-MOVE."""
    raw = session.get('viewer_moved_studies')
    if not isinstance(raw, list):
        return set()
    out: set[str] = set()
    for x in raw:
        if isinstance(x, str) and x.strip():
            out.add(x.strip())
    return out


def _viewer_mark_study_moved(study_uid: str) -> None:
    uid = (study_uid or '').strip()
    if not uid:
        return
    moved = _viewer_moved_studies()
    moved.add(uid)
    # Keep the list bounded.
    session['viewer_moved_studies'] = list(sorted(moved))[-50:]
    session.modified = True


def _received_images_for_code(code: str) -> list[dict]:
    return dicom_receiver.received_images_for_code(code)


def _received_study_groups(received: list[dict]) -> list[dict]:
    return dicom_receiver.received_study_groups(received)


def _dicom_log_append(action: str, ok: bool, detail: str = '') -> None:
    """Append an entry to the session-scoped DICOM protocol log (visible on the dashboard)."""
    log = session.get('dicom_log')
    if not isinstance(log, list):
        log = []
    log.append({
        'ts': datetime.datetime.now().strftime('%H:%M:%S'),
        'action': action,
        'ok': bool(ok),
        'detail': detail,
    })
    session['dicom_log'] = log[-20:]
    session.modified = True
    storage.append_activity(get_student_code(), action, detail, ok)


def _activity_append(action: str, detail: str = '', ok: bool = True) -> None:
    storage.append_activity(get_student_code(), action, detail, ok)


def _dicom_log() -> list:
    log = session.get('dicom_log')
    return log if isinstance(log, list) else []
