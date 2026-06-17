"""
邮件发送服务（aiosmtplib）
"""
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """
    发送密码重置邮件。

    :param to_email: 收件人邮箱
    :param reset_token: 明文重置令牌（用户收到后用于重置密码）
    """
    settings = get_settings()

    subject = "密码重置请求 / Password Reset Request"
    body_text = (
        f"您好，\n\n"
        f"您的密码重置令牌如下（30分钟内有效）：\n\n"
        f"{reset_token}\n\n"
        f"请将此令牌填入密码重置确认页面。\n\n"
        f"如果您没有请求密码重置，请忽略此邮件。\n\n"
        f"---\n"
        f"Thumb Ledger"
    )
    body_html = (
        f"<p>您好，</p>"
        f"<p>您的密码重置令牌如下（<strong>30分钟内有效</strong>）：</p>"
        f"<pre>{reset_token}</pre>"
        f"<p>请将此令牌填入密码重置确认页面。</p>"
        f"<p>如果您没有请求密码重置，请忽略此邮件。</p>"
        f"<hr><p>Thumb Ledger</p>"
    )

    message = MIMEMultipart("alternative")
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body_text, "plain", "utf-8"))
    message.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user if settings.smtp_user else None,
            password=settings.smtp_password if settings.smtp_password else None,
            start_tls=False,
        )
        logger.info("Password reset email sent to %s", to_email)
    except Exception as exc:
        # 邮件发送失败不应阻断主流程，仅记录错误
        logger.error("Failed to send password reset email to %s: %s", to_email, exc)
        raise
