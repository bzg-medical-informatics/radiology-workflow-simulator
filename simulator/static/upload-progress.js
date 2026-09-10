(() => {
  'use strict';

  function ensureStyles() {
    if (document.getElementById('dicomUploadProgressStyles')) return;
    const style = document.createElement('style');
    style.id = 'dicomUploadProgressStyles';
    style.textContent = `
      .dicom-upload-status {
        display: none;
        margin-top: 12px;
        padding: 12px;
        border: 1px solid #b0bec5;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,.08);
      }
      .dicom-upload-status.is-visible { display: block; }
      .dicom-upload-status__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 8px;
        font-size: .92em;
      }
      .dicom-upload-status__label { font-weight: 700; }
      .dicom-upload-status__percent {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-weight: 700;
      }
      .dicom-upload-status__track {
        position: relative;
        height: 12px;
        overflow: hidden;
        border-radius: 999px;
        background: #eceff1;
      }
      .dicom-upload-status__bar {
        width: 0%;
        height: 100%;
        background: #ff9800;
        border-radius: inherit;
        transition: width .15s ease-out;
      }
      .dicom-upload-status.is-processing .dicom-upload-status__bar {
        width: 100% !important;
        animation: dicomUploadPulse 1s ease-in-out infinite alternate;
      }
      .dicom-upload-status.is-error {
        border-color: #c62828;
        background: #ffebee;
      }
      .dicom-upload-status.is-error .dicom-upload-status__bar { background: #c62828; }
      .dicom-upload-status__detail {
        margin-top: 8px;
        color: #546e7a;
        font-size: .85em;
        line-height: 1.35;
      }
      @keyframes dicomUploadPulse {
        from { opacity: .45; }
        to { opacity: 1; }
      }
    `;
    document.head.appendChild(style);
  }

  function makeStatusPanel(form) {
    let panel = form.querySelector('.dicom-upload-status');
    if (panel) return panel;

    panel = document.createElement('div');
    panel.className = 'dicom-upload-status';
    panel.setAttribute('role', 'status');
    panel.setAttribute('aria-live', 'polite');
    panel.innerHTML = `
      <div class="dicom-upload-status__header">
        <span class="dicom-upload-status__label">DICOM-Dateien werden hochgeladen …</span>
        <span class="dicom-upload-status__percent">0%</span>
      </div>
      <div class="dicom-upload-status__track" aria-hidden="true">
        <div class="dicom-upload-status__bar"></div>
      </div>
      <div class="dicom-upload-status__detail">Bitte diese Seite während des Uploads geöffnet lassen.</div>
    `;
    form.appendChild(panel);
    return panel;
  }

  function setProgress(panel, percent) {
    const value = Math.max(0, Math.min(100, Math.round(percent)));
    const bar = panel.querySelector('.dicom-upload-status__bar');
    const percentLabel = panel.querySelector('.dicom-upload-status__percent');
    if (bar) bar.style.width = `${value}%`;
    if (percentLabel) percentLabel.textContent = `${value}%`;
  }

  function setProcessing(panel) {
    panel.classList.add('is-processing');
    const label = panel.querySelector('.dicom-upload-status__label');
    const percentLabel = panel.querySelector('.dicom-upload-status__percent');
    const detail = panel.querySelector('.dicom-upload-status__detail');
    if (label) label.textContent = 'Upload abgeschlossen – Verarbeitung läuft …';
    if (percentLabel) percentLabel.textContent = '100%';
    if (detail) detail.textContent = 'Die DICOM-Dateien werden jetzt verarbeitet und per C-STORE an das PACS gesendet.';
  }

  function setError(panel, message) {
    panel.classList.remove('is-processing');
    panel.classList.add('is-error');
    const label = panel.querySelector('.dicom-upload-status__label');
    const percentLabel = panel.querySelector('.dicom-upload-status__percent');
    const detail = panel.querySelector('.dicom-upload-status__detail');
    if (label) label.textContent = 'Upload fehlgeschlagen';
    if (percentLabel) percentLabel.textContent = 'Fehler';
    if (detail) detail.textContent = message || 'Bitte erneut versuchen.';
  }

  function bindUploadForm(form) {
    if (form.dataset.uploadProgressBound === '1') return;
    form.dataset.uploadProgressBound = '1';

    form.addEventListener('submit', (event) => {
      const fileInput = form.querySelector('input[type="file"][name="dicom_files"]');
      if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;

      event.preventDefault();
      ensureStyles();

      const panel = makeStatusPanel(form);
      panel.classList.remove('is-error', 'is-processing');
      panel.classList.add('is-visible');
      setProgress(panel, 0);

      const label = panel.querySelector('.dicom-upload-status__label');
      const detail = panel.querySelector('.dicom-upload-status__detail');
      if (label) label.textContent = 'DICOM-Dateien werden hochgeladen …';
      if (detail) {
        const count = fileInput.files.length;
        detail.textContent = `${count} Datei${count === 1 ? '' : 'en'} ausgewählt. Bitte diese Seite während des Uploads geöffnet lassen.`;
      }

      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.dataset.originalText = submitButton.textContent || '';
        submitButton.textContent = 'Upload läuft …';
        submitButton.style.opacity = '0.65';
        submitButton.style.cursor = 'wait';
      }

      const xhr = new XMLHttpRequest();
      xhr.open((form.method || 'POST').toUpperCase(), form.action, true);

      xhr.upload.addEventListener('progress', (progressEvent) => {
        if (!progressEvent.lengthComputable || progressEvent.total <= 0) return;
        const percent = (progressEvent.loaded / progressEvent.total) * 100;
        setProgress(panel, percent);
        if (percent >= 100) setProcessing(panel);
      });

      xhr.upload.addEventListener('load', () => {
        setProgress(panel, 100);
        setProcessing(panel);
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 400) {
          const target = xhr.responseURL || '/modality';
          window.location.assign(target);
          return;
        }
        setError(panel, `Serverfehler beim Upload (HTTP ${xhr.status}).`);
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = submitButton.dataset.originalText || 'DICOM UPLOAD & C-STORE senden';
          submitButton.style.opacity = '';
          submitButton.style.cursor = '';
        }
      });

      xhr.addEventListener('error', () => {
        setError(panel, 'Netzwerkfehler beim Upload. Bitte Verbindung prüfen und erneut versuchen.');
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = submitButton.dataset.originalText || 'DICOM UPLOAD & C-STORE senden';
          submitButton.style.opacity = '';
          submitButton.style.cursor = '';
        }
      });

      xhr.addEventListener('timeout', () => {
        setError(panel, 'Der Upload hat zu lange gedauert. Bitte erneut versuchen.');
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = submitButton.dataset.originalText || 'DICOM UPLOAD & C-STORE senden';
          submitButton.style.opacity = '';
          submitButton.style.cursor = '';
        }
      });

      xhr.send(new FormData(form));
    });
  }

  function init() {
    ensureStyles();
    document
      .querySelectorAll('form[action="/scan"][enctype="multipart/form-data"]')
      .forEach(bindUploadForm);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
