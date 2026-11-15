const path = require('path');
const puppeteer = require('../frontend/node_modules/puppeteer');

(async () => {
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none', '--allow-file-access-from-files']
  });

  // 1. Render SOA Distributed ERD
  const erdPage = await browser.newPage();
  await erdPage.setViewport({ width: 1100, height: 820, deviceScaleFactor: 2 });
  const erdUrl = 'file:///' + path.resolve(__dirname, '../docs/diagrams/soa_distributed_erd.html').replace(/\\/g, '/');
  await erdPage.goto(erdUrl, { waitUntil: 'networkidle0' });
  await erdPage.evaluateHandle('document.fonts.ready');
  await new Promise(r => setTimeout(r, 600));

  const erdPng = path.resolve(__dirname, '../docs/images/hinh_3_3b_soa_erd.png');
  const erdJpg = path.resolve(__dirname, '../docs/images/so_do_erd_soa.jpg');
  await erdPage.screenshot({ path: erdPng, type: 'png' });
  await erdPage.screenshot({ path: erdJpg, type: 'jpeg', quality: 95 });
  console.log('Rendered SOA Distributed ERD ->', erdPng);

  // 2. Render Archify Workflow Diagram (Publication-ready capture for report)
  const wfPage = await browser.newPage();
  await wfPage.setViewport({ width: 1400, height: 950, deviceScaleFactor: 2 });
  const wfUrl = 'file:///' + path.resolve(__dirname, '../.archify/workflow-ibanking-tuition-payment-20261111-112200/ibanking-tuition-payment.html').replace(/\\/g, '/');
  await wfPage.goto(wfUrl, { waitUntil: 'networkidle0' });
  await wfPage.evaluateHandle('document.fonts.ready');

  // Hide interactive viewer controls in memory only for clean print image export
  await wfPage.evaluate(() => {
    const style = document.createElement('style');
    style.textContent = `
      /* Hide top-right toolbar buttons, floating zoom bar, and bottom node index for print figure */
      header button, header select, [class*="toolbar"], [class*="controls"], [aria-label*="Zoom"], [class*="index"], section:last-of-type {
        display: none !important;
      }
      body {
        padding-bottom: 16px !important;
      }
    `;
    document.head.appendChild(style);
    // Also hide specific interactive elements by text content if present
    document.querySelectorAll('button').forEach(b => {
      b.style.display = 'none';
    });
    // Find Node index container and hide it for print compactness
    document.querySelectorAll('div, section, aside').forEach(el => {
      if (el.textContent && el.textContent.trim().startsWith('Node index') && el.children.length > 1 && el.offsetHeight < 350) {
        el.style.display = 'none';
      }
    });
  });
  await new Promise(r => setTimeout(r, 500));

  const wfPng = path.resolve(__dirname, '../docs/images/hinh_3_4_workflow_archify.png');
  const wfJpg = path.resolve(__dirname, '../docs/images/so_do_workflow_new.jpg');
  const clipRect = { x: 0, y: 0, width: 1400, height: 1095 };
  await wfPage.screenshot({ path: wfPng, type: 'png', clip: clipRect });
  await wfPage.screenshot({ path: wfJpg, type: 'jpeg', quality: 95, clip: clipRect });
  console.log('Rendered Archify Workflow ->', wfPng);

  await browser.close();
})();
