from __future__ import annotations

import datetime
import shutil

from flask import render_template, request, session

try:
    from blueprint import bp
except ImportError:
    from .blueprint import bp

try:
    from simlib.students import get_student_code, prefix_for_student
except ModuleNotFoundError:
    from .simlib.students import get_student_code, prefix_for_student

try:
    from cstore import _collect_dicom_file_paths_from_uploads, send_c_store, send_c_store_uploaded_files
except ImportError:
    from .cstore import _collect_dicom_file_paths_from_uploads, send_c_store, send_c_store_uploaded_files

try:
    from deps import (
        _dicom_log_append,
        _get_patient,
        _load_patients,
        _load_reports,
        _patient_exists,
        _reports_index_by_pid,
        _set_active_pid,
        _update_patient_last_exam,
    )
except ImportError:
    from .deps import (
    _dicom_log_append,
    _get_patient,
    _load_patients,
    _load_reports,
    _patient_exists,
    _reports_index_by_pid,
    _set_active_pid,
    _update_patient_last_exam,
    )

try:
    from mwl import create_dicom_worklist_file, perform_c_find_mwl
except ImportError:
    from .mwl import create_dicom_worklist_file, perform_c_find_mwl

try:
    from simlib.hl7 import build_hl7_orm_o01
except ModuleNotFoundError:
    from .simlib.hl7 import build_hl7_orm_o01


@bp.route('/create_order', methods=['POST'])
def create_order():
    name = request.form.get('name')
    pid = prefix_for_student(request.form.get('pid'))
    acc = prefix_for_student(request.form.get('acc'))
    desc = request.form.get('desc')

    code = get_student_code()
    if not _patient_exists(code, pid):
        return render_template(
            'index.html',
            msg=f"❌ Unbekannte PID: {pid}. Bitte Patient zuerst im KIS erfassen.",
            patients=_load_patients(code),
            ris_reports_by_pid=_reports_index_by_pid(code),
            ris_reports=_load_reports(code) if code else [],
            last_adt_hl7=session.get('last_adt_hl7', ''),
            last_lis_request_hl7=session.get('last_lis_request_hl7', ''),
            last_oru_hl7=session.get('last_oru_hl7', ''),
            last_lis_summary=session.get('last_lis_summary', None),
            workflow_current="1. HL7 ADT: KIS → RIS (Patient aufnehmen)",
            workflow_next="2. HL7 ORU: RIS ↔ LIS (Kreatinin)",
        )

    needs_contrast = 'km' in (desc or '').lower() or 'kontrastmittel' in (desc or '').lower()
    lab = (_get_patient(code, pid) or {}).get('last_lab') or {}
    lab_critical = str(lab.get('status') or '').upper().startswith('CRITICAL')
    if needs_contrast and lab_critical and request.form.get('confirm_km') != 'on':
        return render_template(
            'index.html',
            msg=(
                f"⚠️ Achtung: Kreatinin von {pid} ist erhöht ({lab.get('value')} {lab.get('unit')}, {lab.get('status')}). "
                "Kontrastmittel-Gabe ist riskant (Kontrastmittel-induzierte Nephropathie). "
                "Bitte unten explizit bestätigen, falls die Untersuchung trotzdem freigegeben werden soll."
            ),
            confirm_km_pending={'name': name, 'pid': pid, 'acc': acc, 'desc': desc},
            patients=_load_patients(code),
            ris_reports_by_pid=_reports_index_by_pid(code),
            ris_reports=_load_reports(code) if code else [],
            last_adt_hl7=session.get('last_adt_hl7', ''),
            last_lis_request_hl7=session.get('last_lis_request_hl7', ''),
            last_oru_hl7=session.get('last_oru_hl7', ''),
            last_lis_summary=session.get('last_lis_summary', None),
            workflow_current="2. HL7 ORU: RIS ↔ LIS (Kreatinin)",
            workflow_next="3. HL7 ORM: Auftrag freigeben (RIS)",
        )

    create_dicom_worklist_file(name, pid, acc, desc)
    _update_patient_last_exam(
        code,
        pid,
        accession_number=acc,
        description=desc,
        status='Auftrag freigegeben',
    )
    raw_orm_hl7 = build_hl7_orm_o01(pid=pid, patient_name=name, accession_number=acc, study_desc=desc)
    session['last_orm_hl7'] = raw_orm_hl7
    session.modified = True
    _set_active_pid(pid)
    ns = f" (SuS-Code: {code})" if code else ""
    msg = f"✅ Auftrag erfolgreich! HL7 ORM wurde simuliert und ein Worklist-Eintrag für '{name}' erstellt.{ns}"
    return render_template(
        'index.html',
        msg=msg,
        patients=_load_patients(code),
        ris_reports_by_pid=_reports_index_by_pid(code),
        ris_reports=_load_reports(code) if code else [],
        last_adt_hl7=session.get('last_adt_hl7', ''),
        last_lis_request_hl7=session.get('last_lis_request_hl7', ''),
        last_oru_hl7=session.get('last_oru_hl7', ''),
        last_lis_summary=session.get('last_lis_summary', None),
        last_orm_hl7=raw_orm_hl7,
        workflow_current="3. HL7 ORM: RIS (Auftrag freigeben)",
        workflow_next="4. DICOM C-FIND (MWL): Worklist abrufen",
    )


@bp.route('/modality')
def modality():
    items = perform_c_find_mwl()
    _dicom_log_append('C-FIND (MWL)', True, f'{len(items)} Worklist-Eintrag(e)')
    return render_template(
        'modality.html',
        items=items,
        worklist_refreshed_at=datetime.datetime.now().strftime('%H:%M:%S'),
        workflow_current="4. DICOM C-FIND (MWL): Worklist abrufen",
        workflow_next="5. DICOM C-STORE: Bilder senden → PACS",
    )


@bp.route('/scan', methods=['POST'])
def scan():
    name = request.form.get('name')
    pid = prefix_for_student(request.form.get('pid'))
    acc = prefix_for_student(request.form.get('acc'))

    uploads = request.files.getlist('dicom_files') if request.files else []
    retag = request.form.get('retag') == 'on'

    code = get_student_code()
    _set_active_pid(pid)

    _update_patient_last_exam(code, pid, accession_number=acc, status='Untersuchung begonnen')

    if uploads and any(u and u.filename for u in uploads):
        dicom_paths, temp_dir = _collect_dicom_file_paths_from_uploads(uploads)
        try:
            summary = send_c_store_uploaded_files(
                dicom_paths,
                patient_name=name,
                patient_id=pid,
                accession_number=acc,
                retag=retag,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        if summary["sent"] == 0 and summary["skipped"] > 0:
            msg = "⚠️ Es wurden Dateien hochgeladen, aber keine gültigen DICOM-Instanzen gefunden (SOPClassUID/SOPInstanceUID fehlen)."
        else:
            msg = (
                f"☢️ Upload-Scan für {name}: gesendet={summary['sent']}, ok={summary['ok']}, "
                f"fehlgeschlagen={summary['failed']}, übersprungen={summary['skipped']}."
            )
            if summary["errors"]:
                msg += " Details: " + " | ".join(summary["errors"][:3])
                if len(summary["errors"]) > 3:
                    msg += f" (+{len(summary['errors']) - 3} weitere)"

        if summary.get('ok', 0) > 0:
            _update_patient_last_exam(code, pid, accession_number=acc, status='Untersuchung abgeschlossen')
        _dicom_log_append('C-STORE', summary.get('ok', 0) > 0, f"gesendet={summary['sent']}, ok={summary['ok']}, fehlgeschlagen={summary['failed']}")
        scan_was_real = True
    else:
        status = send_c_store(name, pid, acc)
        msg = f"☢️ Dummy-Scan für {name}. (Hinweis: Für echte Daten bitte DICOM-Dateien hochladen.) Status: {status}."

        ok = bool(status and getattr(status, 'Status', None) == 0x0000)
        if ok:
            _update_patient_last_exam(code, pid, accession_number=acc, status='Untersuchung abgeschlossen')
        _dicom_log_append('C-STORE', ok, f'Dummy-Scan, Status={status}')
        scan_was_real = False

    items = perform_c_find_mwl()
    return render_template(
        'modality.html',
        items=items,
        scan_was_real=scan_was_real,
        msg=msg,
        worklist_refreshed_at=datetime.datetime.now().strftime('%H:%M:%S'),
        workflow_current="5. DICOM C-STORE: Bilder senden → PACS",
        workflow_next="6. DICOM C-FIND (Study): Workstation ↔ PACS (Studien suchen)",
    )
