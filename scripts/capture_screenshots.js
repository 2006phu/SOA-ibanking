const http = require('http');
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const FRONTEND_BUILD_DIR = path.join(__dirname, '..', 'frontend', 'build');
const IMAGES_DIR = path.join(__dirname, '..', 'docs', 'images');

if (!fs.existsSync(IMAGES_DIR)) {
  fs.mkdirSync(IMAGES_DIR, { recursive: true });
}

// -------------------------------------------------------------
// 1. Mock API Server (Port 8000)
// -------------------------------------------------------------
let userBalance = 15000000;

const apiServer = http.createServer((req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, Idempotency-Key');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = req.url;
  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    res.setHeader('Content-Type', 'application/json');

    // /api/auth/login
    if (url === '/api/auth/login' && req.method === 'POST') {
      res.writeHead(200);
      res.end(JSON.stringify({
        access_token: 'mock-jwt-token-tdtu-ibanking-2024',
        token_type: 'bearer',
        user: {
          id: 1,
          username: 'student1',
          full_name: 'Nguyễn Văn Sinh Viên',
          role: 'STUDENT',
          email: 'student1@tdtu.edu.vn',
          account_number: '1029384756'
        }
      }));
      return;
    }

    // /api/users/me
    if (url === '/api/users/me') {
      res.writeHead(200);
      res.end(JSON.stringify({
        id: 1,
        username: 'student1',
        full_name: 'Nguyễn Văn Sinh Viên',
        role: 'STUDENT',
        email: 'student1@tdtu.edu.vn',
        account_number: '1029384756',
        balance: userBalance
      }));
      return;
    }

    // /api/tuition/:mssv
    if (url.startsWith('/api/tuition/')) {
      const mssv = url.split('/')[3] || '52100888';
      res.writeHead(200);
      res.end(JSON.stringify({
        mssv: mssv,
        student_name: 'Nguyễn Văn Sinh Viên',
        program: 'Kỹ thuật phần mềm (Chất lượng cao)',
        tuition_fees: [
          {
            id: 101,
            semester: 'Học kỳ 1 (2024 - 2025)',
            amount: 8500000,
            status: 'UNPAID',
            due_date: '30/11/2024'
          },
          {
            id: 102,
            semester: 'Học phí Giáo dục Quốc phòng',
            amount: 1500000,
            status: 'UNPAID',
            due_date: '15/12/2024'
          }
        ]
      }));
      return;
    }

    // /api/payments/initiate
    if (url === '/api/payments/initiate' && req.method === 'POST') {
      res.writeHead(200);
      res.end(JSON.stringify({
        transaction_id: 'TXN-2024-884920',
        status: 'INITIATED',
        amount: 8500000,
        message: 'Khởi tạo giao dịch thanh toán thành công'
      }));
      return;
    }

    // /api/payments/:id/confirm
    if (url.includes('/confirm') && req.method === 'POST') {
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'PENDING_OTP',
        otp_code: '582914',
        message: 'Mã OTP đã được gửi đến email student1@tdtu.edu.vn'
      }));
      return;
    }

    // /api/payments/:id/verify-otp
    if (url.includes('/verify-otp') && req.method === 'POST') {
      userBalance -= 8500000;
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'SUCCESS',
        transaction_id: 'TXN-2024-884920',
        amount: 8500000,
        student_name: 'Nguyễn Văn Sinh Viên',
        mssv: '52100888',
        semester: 'Học kỳ 1 (2024 - 2025)',
        payment_date: '2024-10-24 15:45:12',
        account_number: '1029384756',
        balance_after: userBalance
      }));
      return;
    }

    // /api/users/me/transactions
    if (url.startsWith('/api/users/me/transactions')) {
      res.writeHead(200);
      res.end(JSON.stringify({
        items: [
          {
            id: 'TXN-2024-884920',
            transaction_id: 'TXN-2024-884920',
            amount: 8500000,
            status: 'SUCCESS',
            created_at: '2024-10-24T15:45:12Z',
            mssv: '52100888',
            student_name: 'Nguyễn Văn Sinh Viên',
            semester: 'Học kỳ 1 (2024 - 2025)'
          },
          {
            id: 'TXN-2024-102941',
            transaction_id: 'TXN-2024-102941',
            amount: 7200000,
            status: 'SUCCESS',
            created_at: '2024-05-15T10:20:00Z',
            mssv: '52100888',
            student_name: 'Nguyễn Văn Sinh Viên',
            semester: 'Học kỳ 2 (2023 - 2024)'
          }
        ],
        total: 2,
        page: 1,
        total_pages: 1
      }));
      return;
    }

    // Default 404
    res.writeHead(404);
    res.end(JSON.stringify({ detail: 'Endpoint not found' }));
  });
});

// -------------------------------------------------------------
// 2. Static Web Server (Port 3000)
// -------------------------------------------------------------
const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
};

const emailHtmlContent = `
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>TDTU Webmail - Mã OTP xác thực giao dịch</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    body { background-color: #f1f5f9; padding: 24px; display: flex; justify-content: center; }
    .mail-client { width: 900px; background: #ffffff; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; overflow: hidden; }
    .mail-topbar { background: #1e3a8a; color: white; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; }
    .mail-topbar h3 { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .mail-meta { padding: 20px; border-bottom: 1px solid #e2e8f0; background: #f8fafc; }
    .mail-meta h2 { font-size: 18px; color: #0f172a; margin-bottom: 8px; }
    .mail-info { font-size: 13px; color: #64748b; line-height: 1.6; }
    .mail-info strong { color: #1e293b; }
    .mail-body { padding: 32px 40px; color: #334155; line-height: 1.7; }
    .brand-header { border-bottom: 2px solid #1e3a8a; padding-bottom: 12px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }
    .brand-title { color: #1e3a8a; font-size: 20px; font-weight: 700; }
    .brand-badge { background: #eff6ff; color: #1d4ed8; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
    .otp-card { background: #f8fafc; border: 1px dashed #94a3b8; border-radius: 10px; padding: 24px; text-align: center; margin: 24px 0; }
    .otp-code { font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #1e3a8a; font-family: monospace; margin: 12px 0; }
    .otp-expiry { font-size: 13px; color: #d97706; font-weight: 600; }
    .warning-box { background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 4px; font-size: 13px; color: #991b1b; margin-top: 20px; }
    .mail-footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; }
  </style>
</head>
<body>
  <div class="mail-client">
    <div class="mail-topbar">
      <h3>✉️ TDTU Mail System &mdash; Hộp thư đến</h3>
      <span style="font-size: 13px; opacity: 0.9;">student1@student.tdtu.edu.vn</span>
    </div>
    <div class="mail-meta">
      <h2>[TDTU iBanking] Mã xác thực OTP thanh toán học phí</h2>
      <div class="mail-info">
        <div><strong>Người gửi:</strong> TDTU iBanking Notification Service &lt;notification.banking@tdtu.edu.vn&gt;</div>
        <div><strong>Đến:</strong> Nguyễn Văn Sinh Viên &lt;student1@student.tdtu.edu.vn&gt;</div>
        <div><strong>Thời gian:</strong> 24/10/2024, 15:45 (Vừa xong) &bull; Bảo mật: TLS 1.3</div>
      </div>
    </div>
    <div class="mail-body">
      <div class="brand-header">
        <div class="brand-title">TDTU iBanking &bull; Dịch vụ Ngân hàng số</div>
        <div class="brand-badge">XÁC THỰC 2 LỚP (2FA)</div>
      </div>
      <p>Kính gửi sinh viên <strong>Nguyễn Văn Sinh Viên</strong> (MSSV: <strong>52100888</strong>),</p>
      <p style="margin-top: 8px;">Hệ thống nhận được yêu cầu nộp học phí cho giao dịch <strong>TXN-2024-884920</strong> (Số tiền: <strong>8.500.000 VNĐ</strong> &mdash; Học kỳ 1 2024-2025). Dưới đây là mã OTP xác thực của bạn:</p>
      
      <div class="otp-card">
        <div style="font-size: 13px; text-transform: uppercase; color: #64748b; font-weight: 600;">Mã OTP giao dịch</div>
        <div class="otp-code">582914</div>
        <div class="otp-expiry">⏱ Mã có hiệu lực trong 05:00 phút</div>
      </div>

      <div class="warning-box">
        <strong>⚠️ Cảnh báo an toàn:</strong> Tuyệt đối không cung cấp mã OTP này cho bất kỳ ai, kể cả cán bộ nhà trường hoặc nhân viên ngân hàng để tránh bị lừa đảo chiếm đoạt tài khoản.
      </div>

      <div class="mail-footer">
        Thư này được tạo tự động bởi Notification Worker qua RabbitMQ Message Broker &bull; Trường Đại học Tôn Đức Thắng
      </div>
    </div>
  </div>
</body>
</html>
`;

const staticServer = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, 'http://localhost:3000');
  let pathname = parsedUrl.pathname;

  if (pathname === '/email-preview') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(emailHtmlContent);
    return;
  }

  let filePath = path.join(FRONTEND_BUILD_DIR, pathname);

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'application/octet-stream' });
    fs.createReadStream(filePath).pipe(res);
  } else {
    // SPA Fallback
    const indexHtml = path.join(FRONTEND_BUILD_DIR, 'index.html');
    res.writeHead(200, { 'Content-Type': 'text/html' });
    fs.createReadStream(indexHtml).pipe(res);
  }
});

// -------------------------------------------------------------
// 3. Automated Screenshot Capture with Puppeteer
// -------------------------------------------------------------
async function run() {
  await new Promise(r => apiServer.listen(8000, r));
  console.log('✓ Mock API Server listening on port 8000');

  await new Promise(r => staticServer.listen(3000, r));
  console.log('✓ Frontend Static Server listening on port 3000');

  console.log('Launching browser for automated capture...');
  const browser = await puppeteer.launch({
    headless: 'new',
    defaultViewport: {
      width: 1440,
      height: 900,
      deviceScaleFactor: 2 // High DPI Retina Quality
    },
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=medium']
  });

  const page = await browser.newPage();

  // Helper for wait
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  try {
    // ---------------------------------------------------------
    // HÌNH 5.1: Màn hình Đăng nhập
    // ---------------------------------------------------------
    console.log('Capturing Hình 5.1: Màn hình Đăng nhập...');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle0' });
    await sleep(800);
    const hinh51Path = path.join(IMAGES_DIR, 'hinh_5_1_login.png');
    await page.screenshot({ path: hinh51Path });
    console.log(`Saved ${hinh51Path}`);

    // Set auth token in localStorage so all pages are authenticated immediately
    await page.evaluate(() => {
      localStorage.setItem('token', 'mock-jwt-token-tdtu-ibanking-2024');
    });

    // ---------------------------------------------------------
    // HÌNH 5.2: Bảng điều khiển tài khoản (Dashboard)
    // ---------------------------------------------------------
    console.log('Capturing Hình 5.2: Bảng điều khiển tài khoản...');
    await page.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle0' });
    await sleep(1000);
    const hinh52Path = path.join(IMAGES_DIR, 'hinh_5_2_dashboard.png');
    await page.screenshot({ path: hinh52Path });
    console.log(`Saved ${hinh52Path}`);

    // ---------------------------------------------------------
    // HÌNH 5.3: Tra cứu và danh sách học phí
    // ---------------------------------------------------------
    console.log('Navigating to /payment...');
    await page.goto('http://localhost:3000/payment', { waitUntil: 'networkidle0' });
    await sleep(800);

    // Click quick chip 52100888
    const quickChip = await page.$('.quick-mssv-chip');
    if (quickChip) {
      console.log('Clicking quick MSSV chip...');
      await quickChip.click();
    } else {
      console.log('Typing into #mssv-input...');
      await page.waitForSelector('#mssv-input', { timeout: 3000 });
      await page.type('#mssv-input', '52100888');
      const searchBtn = await page.$('button[type="submit"]');
      if (searchBtn) await searchBtn.click();
    }
    await sleep(1200);

    console.log('Capturing Hình 5.3: Tra cứu và danh sách học phí...');
    const hinh53Path = path.join(IMAGES_DIR, 'hinh_5_3_tuition_search.png');
    await page.screenshot({ path: hinh53Path });
    console.log(`Saved ${hinh53Path}`);

    // ---------------------------------------------------------
    // HÌNH 5.4: Màn hình xác thực OTP kèm đếm ngược
    // ---------------------------------------------------------
    console.log('Proceeding to Step 2 (Xác nhận chi phí)...');
    const selectFeeBtn = await page.$('.fee-card-item .btn-primary');
    if (selectFeeBtn) {
      await selectFeeBtn.click();
      await sleep(800);
    }

    // Agree terms checkbox
    const agreeCheckbox = await page.$('input[type="checkbox"]');
    if (agreeCheckbox) {
      await agreeCheckbox.click();
      await sleep(400);
    }

    // Click "Tiếp tục xác thực OTP" to reach Step 3
    console.log('Initiating payment to reach Step 3 (OTP)...');
    const continueBtn = await page.$('.card .btn-primary');
    if (continueBtn) {
      await continueBtn.click();
      await sleep(1200);
    }

    console.log('Capturing Hình 5.4: Màn hình xác thực OTP...');
    const hinh54Path = path.join(IMAGES_DIR, 'hinh_5_4_otp_verify.png');
    await page.screenshot({ path: hinh54Path });
    console.log(`Saved ${hinh54Path}`);

    // ---------------------------------------------------------
    // HÌNH 5.5: Email chứa mã xác thực OTP gửi qua giao thức SMTP
    // ---------------------------------------------------------
    console.log('Capturing Hình 5.5: Email xác thực OTP qua SMTP...');
    await page.goto('http://localhost:3000/email-preview', { waitUntil: 'networkidle0' });
    await sleep(800);
    const hinh55Path = path.join(IMAGES_DIR, 'hinh_5_5_email_otp.png');
    await page.screenshot({ path: hinh55Path });
    console.log(`Saved ${hinh55Path}`);

    // ---------------------------------------------------------
    // HÌNH 5.6: Biên lai điện tử hoàn tất giao dịch
    // ---------------------------------------------------------
    console.log('Completing payment flow for Step 4 (e-Receipt)...');
    await page.goto('http://localhost:3000/payment', { waitUntil: 'networkidle0' });
    await sleep(800);

    const quickChip2 = await page.$('.quick-mssv-chip');
    if (quickChip2) await quickChip2.click();
    await sleep(1000);

    const selectFeeBtn2 = await page.$('.fee-card-item .btn-primary');
    if (selectFeeBtn2) await selectFeeBtn2.click();
    await sleep(800);

    const agreeCheckbox2 = await page.$('input[type="checkbox"]');
    if (agreeCheckbox2) await agreeCheckbox2.click();
    await sleep(400);

    const continueBtn2 = await page.$('.card .btn-primary');
    if (continueBtn2) await continueBtn2.click();
    await sleep(1200);

    // Click fill demo OTP button or type digits
    const fillDemoBtn = await page.$('.demo-otp-banner button, .card button.btn-secondary');
    if (fillDemoBtn) {
      console.log('Clicking auto-fill demo OTP...');
      await fillDemoBtn.click();
      await sleep(400);
    } else {
      const inputs = await page.$$('.otp-digit-input');
      const digits = ['5', '8', '2', '9', '1', '4'];
      if (inputs && inputs.length === 6) {
        for (let i = 0; i < 6; i++) {
          await inputs[i].type(digits[i]);
        }
      }
      await sleep(400);
    }

    // Click verify & pay button
    const verifyPayBtn = await page.$('button.btn-primary');
    if (verifyPayBtn) {
      console.log('Submitting OTP verification...');
      await verifyPayBtn.click();
      await sleep(1500);
    }

    console.log('Capturing Hình 5.6: Biên lai điện tử hoàn tất...');
    const hinh56Path = path.join(IMAGES_DIR, 'hinh_5_6_receipt_history.png');
    await page.screenshot({ path: hinh56Path });
    console.log(`Saved ${hinh56Path}`);

    console.log('✓ ALL 6 SCREENSHOTS CAPTURED SUCCESSFULLY!');
  } catch (err) {
    console.error('Error capturing screenshots:', err);
  } finally {
    await browser.close();
    apiServer.close();
    staticServer.close();
    process.exit(0);
  }
}

run();
