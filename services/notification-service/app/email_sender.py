import logging
from decimal import Decimal
from email.message import EmailMessage
from typing import Any, Union
import aiosmtplib

from app.config import settings
from app.logging_config import get_correlation_id

logger = logging.getLogger("notification-service.email_sender")


def is_smtp_configured() -> bool:
    """Check if SMTP credentials are provided and not default dummy placeholders."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return False
    if "your-email" in settings.SMTP_USER or "your-app-password" in settings.SMTP_PASSWORD:
        return False
    return True


def format_currency_vnd(amount: Union[int, float, Decimal, str]) -> str:
    """Format numeric or string amount into standard Vietnamese Dong format."""
    try:
        if isinstance(amount, str):
            cleaned = amount.replace(",", "").replace(".", "").replace(" ", "").replace("VNĐ", "").replace("VND", "")
            val = float(cleaned)
        else:
            val = float(amount)
        formatted = f"{val:,.0f}".replace(",", ".")
        return f"{formatted} VNĐ"
    except Exception:
        return f"{amount} VNĐ"


def generate_otp_html(code: str, transaction_id: str) -> str:
    """Return inline HTML template for OTP verification email."""
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mã OTP xác thực giao dịch</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b; line-height: 1.6;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 36px 12px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08); overflow: hidden; border: 1px solid #e2e8f0;" cellspacing="0" cellpadding="0" border="0">
                    <!-- Brand Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 32px 24px; text-align: center;">
                            <div style="font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: 1.5px; text-transform: uppercase;">iBanking TDTU</div>
                            <div style="font-size: 13px; color: #bfdbfe; margin-top: 6px; font-weight: 400; letter-spacing: 0.5px;">Cổng Thanh Toán Học Phí Trực Tuyến - Đại Học Tôn Đức Thắng</div>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 36px 32px;">
                            <h2 style="margin: 0 0 16px 0; font-size: 20px; color: #1e3a8a; font-weight: 700;">Mã OTP Xác Thực Giao Dịch</h2>
                            <p style="margin: 0 0 20px 0; font-size: 15px; color: #334155; line-height: 1.6;">
                                Kính chào Quý khách,<br>
                                Bạn đang thực hiện giao dịch thanh toán học phí trên cổng trực tuyến iBanking TDTU. Vui lòng nhập mã OTP dưới đây để xác thực và hoàn tất giao dịch:
                            </p>

                            <!-- OTP Box -->
                            <div style="background-color: #eff6ff; border: 2px dashed #2563eb; border-radius: 10px; padding: 22px; text-align: center; margin: 28px 0;">
                                <div style="font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 6px;">MÃ XÁC THỰC GIAO DỊCH</div>
                                <div style="font-size: 40px; font-weight: 800; letter-spacing: 12px; color: #1e40af; font-family: 'Courier New', Courier, monospace;">{code}</div>
                            </div>

                            <!-- Transaction Info Table -->
                            <table width="100%" cellspacing="0" cellpadding="10" border="0" style="background-color: #f8fafc; border-radius: 8px; margin-bottom: 24px; font-size: 14px; border: 1px solid #f1f5f9;">
                                <tr>
                                    <td style="color: #64748b; width: 40%; padding: 12px 16px; border-bottom: 1px solid #e2e8f0;">Mã giao dịch:</td>
                                    <td style="color: #0f172a; font-weight: 600; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-family: monospace;">{transaction_id}</td>
                                </tr>
                                <tr>
                                    <td style="color: #64748b; padding: 12px 16px;">Thời gian hiệu lực:</td>
                                    <td style="color: #dc2626; font-weight: 700; padding: 12px 16px;">5 phút</td>
                                </tr>
                            </table>

                            <!-- Security Warning -->
                            <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px 16px; border-radius: 4px; margin-bottom: 24px;">
                                <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #92400e;">
                                    <strong>Cảnh báo bảo mật:</strong> Mã xác thực có hiệu lực trong vòng <strong>5 phút</strong>. Tuyệt đối <strong>KHÔNG</strong> chia sẻ mã OTP này cho bất kỳ ai, kể cả nhân viên hỗ trợ hay cán bộ nhà trường, để tránh rủi ro bảo mật.
                                </p>
                            </div>

                            <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #64748b;">
                                Nếu bạn không thực hiện giao dịch này, vui lòng bỏ qua thư này hoặc thông báo ngay cho bộ phận Hỗ trợ Học vụ TDTU.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 22px 32px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #94a3b8; line-height: 1.6;">
                            <p style="margin: 0 0 6px 0; font-weight: 600; color: #64748b;">© 2026 Cổng Thanh Toán iBanking - Trường Đại học Tôn Đức Thắng (TDTU)</p>
                            <p style="margin: 0;">19 Nguyễn Hữu Thọ, Phường Tân Phong, Quận 7, TP. Hồ Chí Minh<br>Hotline: 1900 2026 | Email: hotro@tdtu.edu.vn</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def generate_payment_confirmation_html(
    transaction_id: str,
    student_name: str,
    mssv: str,
    formatted_amount: str,
    completed_at: str
) -> str:
    """Return inline HTML template for payment receipt confirmation email."""
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xác nhận thanh toán học phí thành công</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b; line-height: 1.6;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f1f5f9; padding: 36px 12px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08); overflow: hidden; border: 1px solid #e2e8f0;" cellspacing="0" cellpadding="0" border="0">
                    <!-- Brand Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #065f46 0%, #059669 100%); padding: 32px 24px; text-align: center;">
                            <div style="font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: 1.5px; text-transform: uppercase;">iBanking TDTU</div>
                            <div style="font-size: 13px; color: #d1fae5; margin-top: 6px; font-weight: 400; letter-spacing: 0.5px;">Cổng Thanh Toán Học Phí Trực Tuyến - Đại Học Tôn Đức Thắng</div>
                        </td>
                    </tr>

                    <!-- Success Banner -->
                    <tr>
                        <td style="background-color: #ecfdf5; padding: 18px 24px; text-align: center; border-bottom: 1px solid #a7f3d0;">
                            <div style="font-size: 18px; font-weight: 700; color: #047857;">
                                &#10004; THANH TOÁN HỌC PHÍ THÀNH CÔNG
                            </div>
                            <div style="font-size: 13px; color: #065f46; margin-top: 4px;">
                                Giao dịch đã được hệ thống hạch toán thành công
                            </div>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td style="padding: 36px 32px;">
                            <p style="margin: 0 0 20px 0; font-size: 15px; color: #334155; line-height: 1.6;">
                                Kính chào <strong>{student_name}</strong>,<br>
                                Cổng thanh toán iBanking TDTU xác nhận giao dịch thanh toán học phí của bạn đã được thực hiện thành công. Dưới đây là thông tin chi tiết biên lai điện tử:
                            </p>

                            <!-- Receipt Card -->
                            <div style="border: 1px solid #cbd5e1; border-radius: 10px; overflow: hidden; margin: 24px 0;">
                                <div style="background-color: #f8fafc; padding: 12px 20px; font-size: 13px; font-weight: 700; color: #0f172a; border-bottom: 1px solid #cbd5e1; text-transform: uppercase; letter-spacing: 0.5px;">
                                    BIÊN LAI ĐIỆN TỬ
                                </div>
                                <table width="100%" cellspacing="0" cellpadding="10" border="0" style="font-size: 14px; background-color: #ffffff;">
                                    <tr>
                                        <td style="color: #64748b; width: 42%; border-bottom: 1px solid #f1f5f9; padding-left: 20px;">Mã giao dịch:</td>
                                        <td style="color: #0f172a; font-weight: 600; border-bottom: 1px solid #f1f5f9; font-family: monospace;">{transaction_id}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; border-bottom: 1px solid #f1f5f9; padding-left: 20px;">Họ tên sinh viên:</td>
                                        <td style="color: #0f172a; font-weight: 600; border-bottom: 1px solid #f1f5f9;">{student_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; border-bottom: 1px solid #f1f5f9; padding-left: 20px;">Mã số sinh viên (MSSV):</td>
                                        <td style="color: #0f172a; font-weight: 600; border-bottom: 1px solid #f1f5f9;">{mssv}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; border-bottom: 1px solid #f1f5f9; padding-left: 20px;">Số tiền thanh toán:</td>
                                        <td style="color: #047857; font-size: 18px; font-weight: 800; border-bottom: 1px solid #f1f5f9;">{formatted_amount}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; border-bottom: 1px solid #f1f5f9; padding-left: 20px;">Thời gian hoàn tất:</td>
                                        <td style="color: #0f172a; font-weight: 500; border-bottom: 1px solid #f1f5f9;">{completed_at}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; padding-left: 20px;">Trạng thái:</td>
                                        <td style="color: #047857; font-weight: 700;">Đã thanh toán (Thành công)</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Note Alert -->
                            <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px 16px; border-radius: 4px; margin-bottom: 24px;">
                                <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #1e40af;">
                                    <strong>Ghi chú:</strong> Biên lai điện tử này có giá trị xác nhận bạn đã hoàn thành nghĩa vụ học phí. Dữ liệu công nợ trên cổng thông tin sinh viên sẽ được đồng bộ tự động. Vui lòng lưu lại email này để đối chiếu khi cần thiết.
                                </p>
                            </div>

                            <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #64748b;">
                                Chân thành cảm ơn bạn đã sử dụng dịch vụ thanh toán trực tuyến iBanking TDTU. Chúc bạn có một kỳ học tập thuận lợi và đạt kết quả xuất sắc!
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 22px 32px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #94a3b8; line-height: 1.6;">
                            <p style="margin: 0 0 6px 0; font-weight: 600; color: #64748b;">© 2026 Cổng Thanh Toán iBanking - Trường Đại học Tôn Đức Thắng (TDTU)</p>
                            <p style="margin: 0;">19 Nguyễn Hữu Thọ, Phường Tân Phong, Quận 7, TP. Hồ Chí Minh<br>Hotline: 1900 2026 | Email: hotro@tdtu.edu.vn</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


async def send_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
    """Send email via aiosmtplib or log to stdout if SMTP is not configured."""
    correlation_id = get_correlation_id()

    # If SMTP is not configured or in development mode, log email content
    if not is_smtp_configured():
        logger.info(
            f"[DEV_MODE] Email dispatched to {to_email} with subject: '{subject}' (SMTP credentials not configured)",
            extra={
                "action": "EMAIL_LOGGED_DEV_MODE",
                "correlation_id": correlation_id,
                "recipient": to_email,
                "subject": subject,
                "text_preview": text_content[:300] if text_content else "",
            }
        )
        return True

    msg = EmailMessage()
    from_name = settings.SMTP_FROM_NAME
    from_email = settings.SMTP_USER
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    if text_content:
        msg.set_content(text_content)
    else:
        msg.set_content("Vui lòng mở thư trên trình duyệt hoặc ứng dụng hỗ trợ định dạng HTML.")
    msg.add_alternative(html_content, subtype="html")

    logger.info(
        f"Sending email via SMTP to {to_email}...",
        extra={
            "action": "EMAIL_SENDING",
            "correlation_id": correlation_id,
            "recipient": to_email,
            "subject": subject,
            "smtp_host": settings.SMTP_HOST,
            "smtp_port": settings.SMTP_PORT
        }
    )

    use_starttls = (settings.SMTP_PORT == 587)
    use_tls = (settings.SMTP_PORT == 465)

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=use_starttls,
        use_tls=use_tls,
        timeout=15.0
    )

    logger.info(
        f"Email successfully sent via SMTP to {to_email}",
        extra={
            "action": "EMAIL_SENT",
            "correlation_id": correlation_id,
            "recipient": to_email,
            "subject": subject
        }
    )
    return True


async def send_otp_email(email: str, code: str, transaction_id: str) -> bool:
    """Send OTP email to user."""
    subject = "[iBanking] Mã OTP xác thực giao dịch"
    html_content = generate_otp_html(code=code, transaction_id=transaction_id)
    text_content = (
        f"[iBanking TDTU] Mã OTP xác thực giao dịch\n\n"
        f"Kính chào Quý khách,\n"
        f"Mã OTP xác thực giao dịch iBanking TDTU của bạn là: {code}\n"
        f"Mã giao dịch: {transaction_id}\n"
        f"Thời hạn hiệu lực: 5 phút\n\n"
        f"Lưu ý bảo mật: Tuyệt đối KHÔNG chia sẻ mã OTP này cho bất kỳ ai."
    )
    return await send_email(to_email=email, subject=subject, html_content=html_content, text_content=text_content)


async def send_payment_confirmation_email(
    email: str,
    transaction_id: str,
    student_name: str,
    mssv: str,
    amount: Any,
    completed_at: str
) -> bool:
    """Send payment confirmation receipt email."""
    subject = "[iBanking] Xác nhận thanh toán học phí thành công"
    formatted_amount = format_currency_vnd(amount)
    html_content = generate_payment_confirmation_html(
        transaction_id=transaction_id,
        student_name=student_name,
        mssv=mssv,
        formatted_amount=formatted_amount,
        completed_at=completed_at
    )
    text_content = (
        f"[iBanking TDTU] Xác nhận thanh toán học phí thành công\n\n"
        f"Kính chào {student_name},\n"
        f"Giao dịch thanh toán học phí của bạn đã hoàn tất thành công.\n\n"
        f"THÔNG TIN BIÊN LAI:\n"
        f"- Mã giao dịch: {transaction_id}\n"
        f"- Họ và tên sinh viên: {student_name}\n"
        f"- MSSV: {mssv}\n"
        f"- Số tiền thanh toán: {formatted_amount}\n"
        f"- Thời gian hoàn tất: {completed_at}\n"
        f"- Trạng thái: Thành công\n\n"
        f"Cảm ơn bạn đã sử dụng dịch vụ iBanking TDTU."
    )
    return await send_email(to_email=email, subject=subject, html_content=html_content, text_content=text_content)
