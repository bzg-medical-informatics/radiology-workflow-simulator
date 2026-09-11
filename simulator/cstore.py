from __future__ import annotations

import os
import tempfile
import zipfile

import pydicom
import requests
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import generate_uid
from pynetdicom import AE, sop_class

try:
    from simlib.config import ORTHANC_HOST, ORTHANC_HTTP_URL, ORTHANC_PORT
except ModuleNotFoundError:
    from .simlib.config import ORTHANC_HOST, ORTHANC_HTTP_URL, ORTHANC_PORT

try:
    from mwl import derive_study_uid
except ImportError:
    from .mwl import derive_study_uid


def send_c_store(patient_name, patient_id, accession_number, study_uid=None):
    ae = AE(ae_title=b'SIMULATOR')
    ae.add_requested_context(sop_class.CTImageStorage)

    if not study_uid:
        study_uid = derive_study_uid(accession_number)

    assoc = ae.associate(ORTHANC_HOST, ORTHANC_PORT)
    if assoc.is_established:
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = sop_class.CTImageStorage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

        ds = FileDataset('dummy.dcm', {}, file_meta=file_meta, preamble=b"\0" * 128)
        ds.PatientName = patient_name
        ds.PatientID = patient_id
        ds.AccessionNumber = accession_number
        ds.Modality = 'CT'
        ds.StudyInstanceUID = study_uid if study_uid else generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = sop_class.CTImageStorage
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.Rows = 512
        ds.Columns = 512
        ds.BitsAllocated = 16
        ds.BitsStored = 12
        ds.HighBit = 11
        ds.PixelRepresentation = 0
        ds.PixelData = (b'\x00\x00' * 512 * 512)

        status = assoc.send_c_store(ds)
        assoc.release()
        return status
    return None


def _save_upload_to_tempdir(upload, temp_dir: str) -> str:
    filename = upload.filename or "upload"
    safe_name = os.path.basename(filename)
    if not safe_name:
        safe_name = "upload"
    target_path = os.path.join(temp_dir, safe_name)
    upload.save(target_path)
    return target_path


def _collect_dicom_file_paths_from_uploads(uploads):
    """Return (dicom_file_paths, temp_dir). Caller must delete temp_dir."""
    temp_dir = tempfile.mkdtemp(prefix="dicom_upload_")
    extracted_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extracted_dir, exist_ok=True)

    file_paths = []
    for upload in uploads:
        if not upload or not getattr(upload, "filename", None):
            continue

        saved_path = _save_upload_to_tempdir(upload, temp_dir)
        if saved_path.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(saved_path, 'r') as zf:
                    zf.extractall(extracted_dir)
            except zipfile.BadZipFile:
                file_paths.append(saved_path)
        else:
            file_paths.append(saved_path)

    for root, _, files in os.walk(extracted_dir):
        for name in files:
            file_paths.append(os.path.join(root, name))

    likely = [p for p in file_paths if p.lower().endswith((".dcm", ".dicom"))]
    if likely:
        return likely, temp_dir

    return file_paths, temp_dir


def _identifier_mismatches(ds, patient_id: str, accession_number: str) -> list[str]:
    mismatches = []
    if str(getattr(ds, "PatientID", "") or "") != patient_id:
        mismatches.append("PatientID")
    if str(getattr(ds, "AccessionNumber", "") or "") != accession_number:
        mismatches.append("AccessionNumber")
    return mismatches


def _orthanc_upload_raw(dicom_bytes: bytes) -> dict:
    """Store exact DICOM bytes in Orthanc without decoding/re-encoding PixelData."""
    response = requests.post(
        f"{ORTHANC_HTTP_URL}/instances",
        data=dicom_bytes,
        headers={"Content-Type": "application/dicom", "Expect": ""},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _orthanc_modify_instance(instance_id: str, replacements: dict) -> bytes:
    """Let Orthanc modify metadata while keeping pixel encoding under its control."""
    response = requests.post(
        f"{ORTHANC_HTTP_URL}/instances/{instance_id}/modify",
        json={
            "Replace": replacements,
            "RemovePrivateTags": False,
            "Force": True,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.content


def _orthanc_delete_instance(instance_id: str) -> None:
    response = requests.delete(f"{ORTHANC_HTTP_URL}/instances/{instance_id}", timeout=30)
    response.raise_for_status()


def send_c_store_uploaded_files(
    dicom_paths,
    *,
    patient_name,
    patient_id,
    accession_number,
    study_description='',
    referring_physician_name='Dr. House',
    retag,
):
    """Ingest uploaded DICOM files without re-encoding their pixel data.

    Browser uploads are sent as their original bytes to Orthanc's REST endpoint,
    matching Orthanc's official web uploader. If teaching metadata must be
    adapted, Orthanc performs the DICOM modification itself and the resulting
    bytes are stored again. PixelData is never decoded by the simulator.

    The generated dummy scan still uses real DICOM C-STORE via send_c_store().
    """
    summary = {
        "sent": 0,
        "ok": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
        "identifier_mismatches": [],
        "identifier_preview": [],
        "transport": "orthanc-rest",
    }

    if not dicom_paths:
        return summary

    study_uid = derive_study_uid(accession_number)
    series_uid_map: dict[str, str] = {}

    for path in dicom_paths:
        filename = os.path.basename(path)

        try:
            try:
                ds = pydicom.dcmread(path, stop_before_pixels=True)
            except Exception:
                ds = pydicom.dcmread(path, stop_before_pixels=True, force=True)
        except Exception as e:
            summary["skipped"] += 1
            summary["errors"].append(f"Nicht lesbar: {filename} ({e})")
            continue

        if not hasattr(ds, "SOPClassUID") or not hasattr(ds, "SOPInstanceUID"):
            summary["skipped"] += 1
            summary["errors"].append(f"Kein DICOM Storage-Objekt: {filename}")
            continue

        mismatches = _identifier_mismatches(ds, patient_id, accession_number)
        if len(summary["identifier_preview"]) < 3:
            summary["identifier_preview"].append({
                "filename": filename,
                "original_patient_id": str(getattr(ds, "PatientID", "") or "-"),
                "original_accession": str(getattr(ds, "AccessionNumber", "") or "-"),
                "worklist_patient_id": patient_id,
                "worklist_accession": accession_number,
                "retagged": retag,
            })
        if mismatches and not retag:
            summary["identifier_mismatches"].append(
                f"{filename}: {', '.join(mismatches)} stimmt nicht mit dem Worklist-Eintrag überein"
            )

        try:
            with open(path, "rb") as fh:
                original_bytes = fh.read()
        except Exception as e:
            summary["skipped"] += 1
            summary["errors"].append(f"Datei konnte nicht gelesen werden: {filename} ({e})")
            continue

        summary["sent"] += 1
        source_id = None
        source_was_new = False

        try:
            if not retag:
                _orthanc_upload_raw(original_bytes)
                summary["ok"] += 1
                continue

            source_result = _orthanc_upload_raw(original_bytes)
            source_id = str(source_result.get("ID") or "")
            source_was_new = str(source_result.get("Status") or "") == "Success"
            if not source_id:
                raise ValueError("Orthanc lieferte keine Instance-ID zurück")

            original_series_uid = str(getattr(ds, "SeriesInstanceUID", "") or "")
            series_key = original_series_uid or f"missing-series:{os.path.dirname(path)}"
            series_uid = series_uid_map.setdefault(series_key, generate_uid())

            replacements = {
                "PatientName": str(patient_name or ""),
                "PatientID": str(patient_id or ""),
                "AccessionNumber": str(accession_number or ""),
                "StudyID": str(accession_number or ""),
                "StudyInstanceUID": str(study_uid),
                "SeriesInstanceUID": str(series_uid),
                "SOPInstanceUID": str(generate_uid()),
                "Modality": str(getattr(ds, "Modality", "CT") or "CT"),
            }
            if study_description:
                replacements["StudyDescription"] = str(study_description)
            if referring_physician_name:
                replacements["ReferringPhysicianName"] = str(referring_physician_name)

            modified_bytes = _orthanc_modify_instance(source_id, replacements)
            final_result = _orthanc_upload_raw(modified_bytes)
            if not final_result.get("ID"):
                raise ValueError("Orthanc speicherte die angepasste DICOM-Datei nicht")

            if source_was_new:
                final_id = str(final_result.get("ID") or "")
                if final_id != source_id:
                    _orthanc_delete_instance(source_id)

            summary["ok"] += 1
        except Exception as e:
            summary["failed"] += 1
            summary["errors"].append(f"PACS-Upload fehlgeschlagen: {filename} ({e})")
            if retag and source_was_new and source_id:
                try:
                    _orthanc_delete_instance(source_id)
                except Exception:
                    pass

    return summary
