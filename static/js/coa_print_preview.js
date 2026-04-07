// Chromium COA Print Preview Viewer
// Integrated from Chromium PDF print preview components

class COAPrintPreview {
  constructor(containerId, pdfUrl) {
    this.container = document.getElementById(containerId);
    this.pdfUrl = pdfUrl;
    this.currentPage = 1;
    this.totalPages = 1;
    this.zoomLevel = 1.0;
    this.plugin = null;
    this.init();
  }

  init() {
    this.setupContainer();
    this.createPlugin();
    this.bindToolbarEvents();
    this.setupMessaging();
  }

  setupContainer() {
    this.container.innerHTML = `
      <div class="print-toolbar">
        <div class="toolbar-left">
          <button id="fit-page" class="toolbar-btn">📄 Fit Page</button>
          <button id="fit-width" class="toolbar-btn">↔️ Fit Width</button>
          <span id="page-info" class="page-info">Loading...</span>
        </div>
        <div class="toolbar-right">
          <button id="zoom-in" class="toolbar-btn">🔍 +</button>
          <button id="zoom-out" class="toolbar-btn">🔍 -</button>
          <button id="print-btn" class="print-btn">🖨️ Print</button>
        </div>
      </div>
      <div id="pdf-viewport" class="pdf-viewport"></div>
    `;
  }

  createPlugin() {
    this.plugin = document.createElement('embed');
    this.plugin.id = 'coa-pdf-plugin';
    this.plugin.type = 'application/x-google-chrome-pdf';
    this.plugin.src = this.pdfUrl;
    this.plugin.style.width = '100%';
    this.plugin.style.height = '100%';
    this.plugin.setAttribute('enable-print-preview', 'true');
    
    document.getElementById('pdf-viewport').appendChild(this.plugin);
  }

  bindToolbarEvents() {
    // Toolbar buttons
    document.getElementById('fit-page').onclick = () => this.setFitMode('fit-to-page');
    document.getElementById('fit-width').onclick = () => this.setFitMode('fit-to-width');
    document.getElementById('zoom-in').onclick = () => this.zoom(1.2);
    document.getElementById('zoom-out').onclick = () => this.zoom(0.8);
    document.getElementById('print-btn').onclick = () => window.print();
  }

  setupMessaging() {
    window.addEventListener('message', (e) => {
      if (e.source !== this.plugin.contentWindow) return;
      
      const data = e.data;
      switch(data.type) {
        case 'documentDimensions':
          this.updatePageInfo(data);
          break;
        case 'printPreviewReady':
          this.onPreviewReady();
          break;
        case 'pageChanged':
          this.currentPage = data.page;
          this.updatePageDisplay();
          break;
      }
    });
  }

  setFitMode(mode) {
    if (this.plugin.contentWindow) {
      this.plugin.contentWindow.postMessage({
        type: 'setPrintPreviewFitMode',
        mode: mode
      }, '*');
    }
  }

  zoom(factor) {
    this.zoomLevel *= factor;
    if (this.plugin.contentWindow) {
      this.plugin.contentWindow.postMessage({
        type: 'setZoom',
        zoom: this.zoomLevel
      }, '*');
    }
  }

  updatePageInfo(data) {
    this.totalPages = data.numPages || 1;
    this.updatePageDisplay();
  }

  updatePageDisplay() {
    document.getElementById('page-info').textContent = 
      `Page ${this.currentPage} of ${this.totalPages}`;
  }

  onPreviewReady() {
    console.log('✅ COA Print Preview Ready');
    document.body.classList.add('preview-ready');
  }
}

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('coa-print-preview');
  if (container && window.coaPdfUrl) {
    new COAPrintPreview('coa-print-preview', window.coaPdfUrl);
  }
});

