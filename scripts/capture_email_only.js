const path = require('path');
const fs = require('fs');
const puppeteer = require('../frontend/node_modules/puppeteer');

const IMAGES_DIR = path.join(__dirname, '..', 'docs', 'images');
const emailHtmlPath = path.join(__dirname, 'email_temp.html');

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
        <div><strong>Thời gian:</strong> 28/10/2026, 22:50 (Vừa xong) &bull; Bảo mật: TLS 1.3</div>
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

fs.writeFileSync(emailHtmlPath, emailHtmlContent, 'utf-8');

async function captureEmail() {
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
  await page.goto('file:///' + emailHtmlPath.replace(/\\/g, '/'), { waitUntil: 'load' });
  const hinh55Path = path.join(IMAGES_DIR, 'hinh_5_5_email_otp.png');
  await page.screenshot({ path: hinh55Path });
  console.log(`✓ Saved ${hinh55Path}`);

  await browser.close();
  try { fs.unlinkSync(emailHtmlPath); } catch {}
}

captureEmail();
