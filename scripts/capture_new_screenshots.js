const path = require('path');
const fs = require('fs');
const puppeteer = require('../frontend/node_modules/puppeteer');

const IMAGES_DIR = path.join(__dirname, '..', 'docs', 'images');
if (!fs.existsSync(IMAGES_DIR)) {
  fs.mkdirSync(IMAGES_DIR, { recursive: true });
}

let userBalance = 15000000;

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
      <h3>TDTU Mail System &mdash; Hộp thư đến</h3>
      <span style="font-size: 13px; opacity: 0.9;">student1@student.tdtu.edu.vn</span>
    </div>
    <div class="mail-meta">
      <h2>[TDTU iBanking] Mã xác thực OTP thanh toán học phí</h2>
      <div class="mail-info">
        <div><strong>Người gửi:</strong> TDTU iBanking Notification Service &lt;notification.banking@tdtu.edu.vn&gt;</div>
        <div><strong>Đến:</strong> Nguyễn Văn Sinh Viên &lt;student1@student.tdtu.edu.vn&gt;</div>
        <div><strong>Thời gian:</strong> 24/10/2026, 15:45 (Vừa xong) &bull; Bảo mật: TLS 1.3</div>
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
        <div class="otp-expiry">Mã có hiệu lực trong 05:00 phút</div>
      </div>

      <div class="warning-box">
        <strong>Cảnh báo an toàn:</strong> Tuyệt đối không cung cấp mã OTP này cho bất kỳ ai, kể cả cán bộ nhà trường hoặc nhân viên ngân hàng để tránh bị lừa đảo chiếm đoạt tài khoản.
      </div>

      <div class="mail-footer">
        Thư này được tạo tự động bởi Notification Worker qua RabbitMQ Message Broker &bull; Trường Đại học Tôn Đức Thắng
      </div>
    </div>
  </div>
</body>
</html>
`;

async function main() {
  console.log('Launching browser for automated capture...');
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: 'new',
    defaultViewport: {
      width: 1440,
      height: 900,
      deviceScaleFactor: 2
    },
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=medium']
  });

  const page = await browser.newPage();
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  // Enable request interception for mock API responses matching report data
  await page.setRequestInterception(true);
  page.on('request', interceptedRequest => {
    const url = interceptedRequest.url();
    const method = interceptedRequest.method();

    if (url.includes('/api/')) {
      console.log('Intercepting API:', method, url);
    }

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, Idempotency-Key',
      'Content-Type': 'application/json',
    };

    if (method === 'OPTIONS') {
      return interceptedRequest.respond({
        status: 204,
        headers: corsHeaders,
      });
    }

    if (url.includes('/api/auth/login') && method === 'POST') {
      return interceptedRequest.respond({
        status: 200,
        headers: corsHeaders,
        body: JSON.stringify({
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
        })
      });
    }

    if (url.includes('/api/users/me') && method === 'GET') {
      return interceptedRequest.respond({
        status: 200,
        headers: corsHeaders,
        body: JSON.stringify({
          id: 1,
          username: 'student1',
          full_name: 'Nguyễn Văn Sinh Viên',
          role: 'STUDENT',
          email: 'student1@tdtu.edu.vn',
          account_number: '1029384756',
          balance: userBalance
        })
      });
    }

    if (url.includes('/api/tuition/')) {
      const mssv = url.split('/').pop() || '52100888';
      return interceptedRequest.respond({
        status: 200,
        headers: corsHeaders,
        body: JSON.stringify({
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
        })
      });
    }

    if (url.includes('/api/payments/initiate') && method === 'POST') {
      return interceptedRequest.respond({
        status: 200,
        headers: corsHeaders,
        body: JSON.stringify({
          transaction_id: 'TXN-2024-884920',
          status: 'INITIATED',
          amount: 8500000,
          message: 'Khởi tạo giao dịch thanh toán thành công'
        })
      });
    }

    if (url.includes('/confirm') && method === 'POST') {
      return interceptedRequest.respond({
        status: 200,
        headers: corsHeaders,
        body: JSON.stringify({
          status: 'PENDING_OTP',
          otp_code: '582914',
          message: 'Mã OTP đã được gửi đến email student1@tdtu.edu.vn'
        })
      });
    }

    if (url.includes('/verify-otp') && method === 'POST') {
      userBalance -= 8500000;
      return interceptedRequest.respond({
        status: 200,
        headers: corsHeaders,
        body: JSON.stringify({
          success: true,
          status: 'SUCCESS',
          message: 'Giao dịch thanh toán học phí thành công!',
          data: {
            transaction_id: 'TXN-2024-884920',
            amount: 8500000,
            student_name: 'Nguyễn Văn Sinh Viên',
            mssv: '52100888',
            semester: 'Học kỳ 1 (2024 - 2025)',
            balance_after: userBalance,
            completed_at: '2024-10-24T15:45:12Z'
          }
        })
      });
    }

    // Continue all other requests (static assets, fonts, etc.)
    interceptedRequest.continue();
  });

  try {
    // ---------------------------------------------------------
    // HÌNH 5.1: Màn hình Đăng nhập
    // ---------------------------------------------------------
    console.log('Capturing Hình 5.1: Màn hình Đăng nhập...');
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle0' });
    await sleep(1500);
    const hinh51Path = path.join(IMAGES_DIR, 'hinh_5_1_login.png');
    await page.screenshot({ path: hinh51Path });
    console.log(`✓ Saved ${hinh51Path}`);

    // Click demo account "student1" (second button in demo-grid)
    console.log('Logging in via demo student account...');
    await page.waitForSelector('.demo-grid button', { timeout: 5000 });
    const demoBtns = await page.$$('.demo-grid button');
    if (demoBtns && demoBtns.length >= 2) {
      await demoBtns[1].click();
      await sleep(400);
    }

    await page.evaluate(() => {
      const inputs = document.querySelectorAll('.login-input');
      if (inputs.length >= 2) {
        inputs[0].value = 'student1';
        inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
        inputs[1].value = 'password123';
        inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await sleep(400);

    // Click submit button
    const submitBtn = await page.$('button[type="submit"]');
    if (submitBtn) {
      await submitBtn.click();
    }

    // Wait for Dashboard to appear
    await page.waitForSelector('.account-card, .dashboard-container', { timeout: 10000 });
    await sleep(2000);

    // ---------------------------------------------------------
    // HÌNH 5.2: Bảng điều khiển tài khoản (Dashboard)
    // ---------------------------------------------------------
    console.log('Capturing Hình 5.2: Bảng điều khiển tài khoản...');
    const hinh52Path = path.join(IMAGES_DIR, 'hinh_5_2_dashboard.png');
    await page.screenshot({ path: hinh52Path });
    console.log(`✓ Saved ${hinh52Path}`);

    // ---------------------------------------------------------
    // HÌNH 5.3: Tra cứu và danh sách học phí
    // ---------------------------------------------------------
    console.log('Navigating to /payment via evaluate click...');
    await page.evaluate(() => {
      const link = document.querySelector('a[href="/payment"]');
      if (link) {
        link.click();
      } else {
        const card = document.querySelector('.action-card');
        if (card) card.click();
      }
    });
    await sleep(2000);
    console.log('URL after evaluate click:', page.url());

    await page.waitForSelector('#mssv-input', { timeout: 10000 });
    await sleep(1000);

    console.log('Clicking quick chip 52100888 via evaluate...');
    await page.waitForSelector('.quick-mssv-chip', { timeout: 10000 });
    await page.evaluate(() => {
      const chip = document.querySelector('.quick-mssv-chip');
      console.log('CHIP ELEMENT FOUND:', !!chip, chip ? chip.innerText : '');
      if (chip) chip.click();
    });
    await page.waitForSelector('.fee-card-item', { timeout: 10000 });
    await sleep(1500);

    console.log('Capturing Hình 5.3: Tra cứu và danh sách học phí...');
    const hinh53Path = path.join(IMAGES_DIR, 'hinh_5_3_tuition_search.png');
    await page.screenshot({ path: hinh53Path });
    console.log(`✓ Saved ${hinh53Path}`);

    // ---------------------------------------------------------
    // HÌNH 5.4: Màn hình xác thực OTP kèm đếm ngược
    // ---------------------------------------------------------
    console.log('Proceeding to Step 2 (Xác nhận chi phí)...');
    await page.waitForSelector('.fee-card-item .btn-primary', { timeout: 10000 });
    await page.evaluate(() => {
      const btn = document.querySelector('.fee-card-item .btn-primary');
      if (btn) btn.click();
    });
    await sleep(1000);

    console.log('Agreeing to terms...');
    await page.waitForSelector('#agree-checkbox', { timeout: 10000 });
    await page.evaluate(() => {
      const cb = document.querySelector('#agree-checkbox');
      if (cb) cb.click();
    });
    await sleep(500);

    console.log('Initiating payment to reach Step 3 (OTP)...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const otpBtn = btns.find(b => b.innerText.includes('Nhận mã OTP'));
      if (otpBtn) otpBtn.click();
    });

    await page.waitForSelector('.otp-digit-input', { timeout: 10000 });
    await sleep(1500);
    console.log('Capturing Hình 5.4: Màn hình xác thực OTP...');
    const hinh54Path = path.join(IMAGES_DIR, 'hinh_5_4_otp_verify.png');
    await page.screenshot({ path: hinh54Path });
    console.log(`✓ Saved ${hinh54Path}`);

    // ---------------------------------------------------------
    // HÌNH 5.6: Biên lai điện tử hoàn tất giao dịch
    // ---------------------------------------------------------
    console.log('Completing payment flow for Step 4 (e-Receipt)...');
    await page.evaluate(() => {
      const fillBtn = document.querySelector('.demo-otp-badge button');
      if (fillBtn) fillBtn.click();
    });
    await sleep(600);

    console.log('Submitting OTP verification...');
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const payBtn = btns.find(b => b.innerText.includes('Xác nhận thanh toán'));
      if (payBtn) payBtn.click();
    });

    await page.waitForSelector('.receipt-card', { timeout: 10000 });
    await sleep(1500);
    console.log('Capturing Hình 5.6: Biên lai điện tử hoàn tất...');
    const hinh56Path = path.join(IMAGES_DIR, 'hinh_5_6_receipt_history.png');
    await page.screenshot({ path: hinh56Path });
    console.log(`✓ Saved ${hinh56Path}`);

    // ---------------------------------------------------------
    // HÌNH 5.5: Email chứa mã xác thực OTP
    // ---------------------------------------------------------
    console.log('Capturing Hình 5.5: Email xác thực OTP qua SMTP...');
    await page.setContent(emailHtmlContent, { waitUntil: 'domcontentloaded' });
    await sleep(800);
    const hinh55Path = path.join(IMAGES_DIR, 'hinh_5_5_email_otp.png');
    await page.screenshot({ path: hinh55Path });
    console.log(`✓ Saved ${hinh55Path}`);

    console.log('🎉 ALL 6 SCREENSHOTS CAPTURED SUCCESSFULLY!');
  } catch (err) {
    console.error('Error during capture:', err);
  } finally {
    await browser.close();
  }
}

main();
