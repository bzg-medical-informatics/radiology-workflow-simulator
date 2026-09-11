(() => {
  'use strict';

  const STEP_TARGETS = {
    '1': '/#workflow-kis',
    '2': '/#workflow-lis',
    '3': '/#workflow-ris',
    '4': '/modality',
    '5': '/modality',
    '6': '/viewer',
    '7': '/viewer',
  };

  const NODE_TARGETS = {
    KIS: '/#workflow-kis',
    ADT: '/#workflow-kis',
    LIS: '/#workflow-lis',
    ORU: '/#workflow-lis',
    RIS: '/#workflow-ris',
    ORM: '/#workflow-ris',
    MWLServer: '/modality',
    MWL: '/modality',
    Modality: '/modality',
    STORE: '/modality',
    PACS: '/pacs',
    Workstation: '/viewer',
    QFIND: '/viewer',
    CMOVE: '/viewer',
  };

  function addSharedStyles() {
    if (document.getElementById('workflowNavigationStyles')) return;
    const style = document.createElement('style');
    style.id = 'workflowNavigationStyles';
    style.textContent = `
      .global-home-button {
        position: fixed;
        left: 16px;
        bottom: 16px;
        z-index: 120;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 11px;
        border: 1px solid #9fb8b4;
        border-radius: 999px;
        background: #ffffff;
        color: #17454a;
        text-decoration: none;
        font: 600 .86rem/1.2 "DM Sans", "Segoe UI", sans-serif;
        box-shadow: 0 2px 8px rgba(24, 50, 58, .16);
      }
      .global-home-button:hover { background: #eef8f6; transform: translateY(-1px); }
      .workflow-nav-link { cursor: pointer !important; }
      .workflow-nav-link:hover { filter: brightness(.97); box-shadow: 0 2px 8px rgba(24, 50, 58, .14); }
      .workflow-nav-link:focus-visible { outline: 3px solid rgba(0, 124, 120, .34); outline-offset: 2px; }
      .workflow-diagram .node { cursor: pointer; }
      .workflow-target-flash { animation: workflowTargetFlash 1.3s ease-out; }
      @keyframes workflowTargetFlash {
        0% { box-shadow: 0 0 0 5px rgba(0,124,120,.28); }
        100% { box-shadow: 0 0 0 0 rgba(0,124,120,0); }
      }
    `;
    document.head.appendChild(style);
  }

  function closeWorkflowDrawer() {
    const drawer = document.getElementById('workflowDrawer');
    if (drawer) drawer.checked = false;
    try { localStorage.setItem('workflowDrawerOpen', '0'); } catch (e) {}
  }

  function navigateTo(href) {
    if (!href) return;
    closeWorkflowDrawer();

    const targetUrl = new URL(href, window.location.origin);
    const sameDocument = targetUrl.pathname === window.location.pathname &&
      targetUrl.search === window.location.search;

    if (sameDocument && targetUrl.hash) {
      const target = document.querySelector(targetUrl.hash);
      if (target) {
        history.replaceState(null, '', targetUrl.hash);
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        target.classList.remove('workflow-target-flash');
        void target.offsetWidth;
        target.classList.add('workflow-target-flash');
        return;
      }
    }

    window.location.assign(targetUrl.pathname + targetUrl.search + targetUrl.hash);
  }

  function makeNavigable(element, href, label) {
    if (!element || !href) return;
    element.dataset.workflowHref = href;
    element.classList.add('workflow-nav-link');
    if (!element.hasAttribute('tabindex')) element.tabIndex = 0;
    if (!element.hasAttribute('role')) element.setAttribute('role', 'link');
    if (label && !element.hasAttribute('aria-label')) element.setAttribute('aria-label', label);
  }

  function setHomeAnchors() {
    if (window.location.pathname !== '/' && !document.querySelector('form[action="/kis/register_patient"]')) return;

    document.querySelectorAll('.tile').forEach((tile) => {
      const heading = (tile.querySelector('h3')?.textContent || '').replace(/\s+/g, ' ').trim();
      if (/^1\).*HL7 ADT/i.test(heading)) tile.id = tile.id || 'workflow-kis';
      else if (/^2\).*HL7 ORU/i.test(heading)) tile.id = tile.id || 'workflow-lis';
      else if (/^3\).*HL7 ORM/i.test(heading)) tile.id = tile.id || 'workflow-ris';
    });

    const hash = window.location.hash;
    if (hash) {
      requestAnimationFrame(() => {
        const target = document.querySelector(hash);
        if (!target) return;
        target.scrollIntoView({ block: 'start' });
        target.classList.add('workflow-target-flash');
      });
    }
  }

  function setupHomeOverviewNavigation() {
    const phaseTargets = [
      '/#workflow-kis',
      '/modality',
      '/viewer',
    ];
    document.querySelectorAll('.workflow-phase').forEach((phase, index) => {
      makeNavigable(phase, phaseTargets[index], `Workflow-Phase ${index + 1} öffnen`);
    });

    const guidedTargets = [
      '/#workflow-kis',
      '/#workflow-lis',
      '/#workflow-ris',
      '/modality',
    ];
    document.querySelectorAll('.guided-step').forEach((step, index) => {
      makeNavigable(step, guidedTargets[index], `Lernschritt ${index + 1} öffnen`);
    });

    const statusTargets = [
      '/#workflow-ris',
      '/modality',
      '/pacs',
      '/viewer',
    ];
    document.querySelectorAll('.status-journey-step').forEach((step, index) => {
      makeNavigable(step, statusTargets[index], `Statusschritt ${index + 1} öffnen`);
    });

    document.querySelectorAll('[data-workflow-step]').forEach((stage) => {
      const firstStep = (stage.dataset.workflowStep || '').split(',')[0].trim();
      makeNavigable(stage, STEP_TARGETS[firstStep], `Workflow-Schritt ${firstStep} öffnen`);
    });

    document.querySelectorAll('.workflow-stage:not([data-workflow-step])').forEach((stage) => {
      const text = (stage.textContent || '').replace(/\s+/g, ' ').trim();
      if (/\bPACS\b/i.test(text)) makeNavigable(stage, '/pacs', 'PACS Bildarchiv öffnen');
      else if (/Workstation/i.test(text)) makeNavigable(stage, '/viewer', 'Workstation öffnen');
    });
  }

  function setupSidebarStepNavigation() {
    document.querySelectorAll('[data-wf-step]').forEach((button) => {
      const step = (button.getAttribute('data-wf-step') || '').trim();
      makeNavigable(button, STEP_TARGETS[step], `Workflow-Schritt ${step} öffnen`);
    });
  }

  function installClickRouting() {
    document.addEventListener('click', (event) => {
      const target = event.target.closest('[data-workflow-href], [data-wf-step], [data-workflow-step]');
      if (!target) return;

      let href = target.dataset.workflowHref || '';
      if (!href && target.hasAttribute('data-wf-step')) {
        href = STEP_TARGETS[(target.getAttribute('data-wf-step') || '').trim()] || '';
      }
      if (!href && target.hasAttribute('data-workflow-step')) {
        const step = (target.getAttribute('data-workflow-step') || '').split(',')[0].trim();
        href = STEP_TARGETS[step] || '';
      }
      if (!href) return;

      event.preventDefault();
      event.stopImmediatePropagation();
      navigateTo(href);
    }, true);

    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      const target = event.target.closest('[data-workflow-href]');
      if (!target) return;
      event.preventDefault();
      navigateTo(target.dataset.workflowHref || '');
    });
  }

  function makeMermaidNodesNavigate() {
    if (typeof window.workflowExplain !== 'function') return;
    window.workflowExplain = function(nodeId) {
      const key = String(nodeId || '').trim();
      const href = NODE_TARGETS[key];
      if (href) navigateTo(href);
    };
  }

  function keepPacsAsActiveNode() {
    if (!window.location.pathname.startsWith('/pacs')) return;
    if (typeof window.setWorkflowUi !== 'function') return;

    const originalSetWorkflowUi = window.setWorkflowUi;
    window.setWorkflowUi = function() {
      return originalSetWorkflowUi.call(
        this,
        'PACS: Bildarchiv',
        '6. DICOM C-FIND (Study): Workstation ↔ PACS',
        'PACS',
        'QFIND'
      );
    };
  }

  function addHomeButton() {
    if (window.location.pathname === '/') return;
    if (document.querySelector('.global-home-button')) return;

    const home = document.createElement('a');
    home.className = 'global-home-button';
    home.href = '/';
    home.setAttribute('aria-label', 'Zur Übersichtsseite');
    home.textContent = '⌂ Home';
    document.body.appendChild(home);
  }

  addSharedStyles();
  installClickRouting();
  makeMermaidNodesNavigate();
  keepPacsAsActiveNode();

  document.addEventListener('DOMContentLoaded', () => {
    setHomeAnchors();
    setupHomeOverviewNavigation();
    setupSidebarStepNavigation();
    addHomeButton();
  });
})();
