(() => {
  'use strict';

  // Capture server-rendered pending order values before the existing
  // DOMContentLoaded handler can clear them when the patient select is empty.
  const initialOrderPid = (document.getElementById('orderPid')?.value || '').trim();
  const initialOrderName = (document.getElementById('orderName')?.value || '').trim();

  // Wrap the existing explanation function so every "... erklärt" button
  // opens the workflow sidebar where the explanation panel lives.
  if (typeof window.showSystemDetail === 'function') {
    const originalShowSystemDetail = window.showSystemDetail;
    window.showSystemDetail = function(system) {
      originalShowSystemDetail(system);
      const drawer = document.getElementById('workflowDrawer');
      if (drawer) drawer.checked = true;
      try { localStorage.setItem('workflowDrawerOpen', '1'); } catch (e) {}
    };
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (!initialOrderPid) return;

    const select = document.getElementById('risPatientSelect');
    const pidInput = document.getElementById('orderPid');
    const nameInput = document.getElementById('orderName');
    if (!select || !pidInput || !nameInput) return;

    const matchingOption = Array.from(select.options).find(
      (option) => (option.value || '').trim() === initialOrderPid
    );

    if (matchingOption) {
      select.value = initialOrderPid;
      pidInput.value = initialOrderPid;
      nameInput.value = (matchingOption.getAttribute('data-name') || initialOrderName).trim();
    }
  });
})();
