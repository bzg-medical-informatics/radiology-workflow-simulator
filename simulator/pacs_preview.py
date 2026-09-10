from __future__ import annotations

from flask import make_response

try:
    from dicom_helpers import _render_dicom_png
    from orthanc_helpers import _orthanc_get_bytes
except ImportError:
    from .dicom_helpers import _render_dicom_png
    from .orthanc_helpers import _orthanc_get_bytes


def pacs_instance_preview_with_orthanc_fallback(instance_id: str):
    """Render a DICOM preview, preferring pydicom and falling back to Orthanc."""
    try:
        dicom_bytes = _orthanc_get_bytes(f'/instances/{instance_id}/file')
        png = _render_dicom_png(dicom_bytes)
        resp = make_response(png)
        resp.headers['Content-Type'] = 'image/png'
        resp.headers['Cache-Control'] = 'no-store'
        return resp
    except Exception as primary_error:
        try:
            png = _orthanc_get_bytes(f'/instances/{instance_id}/preview')
            resp = make_response(png)
            resp.headers['Content-Type'] = 'image/png'
            resp.headers['Cache-Control'] = 'no-store'
            resp.headers['X-DICOM-Preview-Renderer'] = 'orthanc'
            return resp
        except Exception as fallback_error:
            return make_response(
                'Cannot render this DICOM instance as PNG. '
                f'pydicom failed: {primary_error}; Orthanc preview failed: {fallback_error}',
                415,
            )
