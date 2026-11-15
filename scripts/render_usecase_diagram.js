const path = require('path');
const fs = require('fs');
const puppeteer = require('../frontend/node_modules/puppeteer');

(async () => {
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const htmlPath = path.resolve(__dirname, '../docs/diagrams/use_case_diagram.html');
  const fileUrl = 'file:///' + htmlPath.replace(/\\/g, '/');

  console.log('Launching Chrome to render diagram from:', fileUrl);

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none', '--allow-file-access-from-files']
  });

  const page = await browser.newPage();
  await page.setViewport({
    width: 1100,
    height: 800,
    deviceScaleFactor: 2
  });

  await page.goto(fileUrl, { waitUntil: 'networkidle0' });

  // Wait a moment for fonts to load
  await page.evaluateHandle('document.fonts.ready');
  await new Promise(r => setTimeout(r, 1000));

  const pngPath = path.resolve(__dirname, '../docs/images/hinh_3_1_use_case.png');
  const jpgPath = path.resolve(__dirname, '../docs/images/so_do_usecase_new.jpg');

  await page.screenshot({
    path: pngPath,
    type: 'png'
  });
  console.log('Saved 2x Retina PNG to:', pngPath);

  await page.screenshot({
    path: jpgPath,
    type: 'jpeg',
    quality: 95
  });
  console.log('Saved High Quality JPEG to:', jpgPath);

  await browser.close();
  console.log('Render completed successfully.');
})();
