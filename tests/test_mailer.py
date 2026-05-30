"""SMTP发送引擎测试."""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from email.mime.multipart import MIMEMultipart

from mailforge.core.config import SMTPAccount
from mailforge.core.mailer import Mailer, SendResult, SMTPConnection


class TestSMTPAccount(unittest.TestCase):
    """SMTPAccount测试."""

    def test_create_default_account(self) -> None:
        """测试创建默认账户."""
        account = SMTPAccount(name="test")
        self.assertEqual(account.name, "test")
        self.assertEqual(account.port, 587)
        self.assertTrue(account.use_tls)
        self.assertFalse(account.use_ssl)

    def test_account_to_dict(self) -> None:
        """测试账户序列化."""
        account = SMTPAccount(name="test", host="smtp.test.com", port=465)
        data = account.to_dict()
        self.assertEqual(data["name"], "test")
        self.assertEqual(data["host"], "smtp.test.com")
        self.assertEqual(data["port"], 465)

    def test_account_from_dict(self) -> None:
        """测试账户反序列化."""
        data = {"name": "test", "host": "smtp.test.com", "port": 465}
        account = SMTPAccount.from_dict(data)
        self.assertEqual(account.name, "test")
        self.assertEqual(account.host, "smtp.test.com")
        self.assertEqual(account.port, 465)


class TestSendResult(unittest.TestCase):
    """SendResult测试."""

    def test_success_result(self) -> None:
        """测试成功结果."""
        result = SendResult(success=True, email="test@example.com", message_id="<abc>")
        self.assertTrue(result.success)
        self.assertEqual(result.email, "test@example.com")
        self.assertEqual(result.message_id, "<abc>")
        self.assertEqual(result.retries, 0)

    def test_failure_result(self) -> None:
        """测试失败结果."""
        result = SendResult(success=False, email="test@example.com", error="Connection refused", retries=2)
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Connection refused")
        self.assertEqual(result.retries, 2)

    def test_result_to_dict(self) -> None:
        """测试结果序列化."""
        result = SendResult(success=True, email="test@example.com")
        data = result.to_dict()
        self.assertIn("success", data)
        self.assertIn("email", data)
        self.assertIn("timestamp", data)


class TestSMTPConnection(unittest.TestCase):
    """SMTPConnection测试."""

    def test_initial_state(self) -> None:
        """测试初始状态."""
        account = SMTPAccount(name="test", host="smtp.test.com")
        conn = SMTPConnection(account)
        self.assertFalse(conn.is_connected)

    @patch("mailforge.core.mailer.smtplib.SMTP_SSL")
    def test_ssl_connection(self, mock_smtp_ssl: MagicMock) -> None:
        """测试SSL连接."""
        mock_instance = MagicMock()
        mock_smtp_ssl.return_value = mock_instance

        account = SMTPAccount(name="test", host="smtp.test.com", port=465, use_ssl=True)
        conn = SMTPConnection(account)
        conn.connect()

        self.assertTrue(conn.is_connected)
        mock_smtp_ssl.assert_called_once()

    @patch("mailforge.core.mailer.smtplib.SMTP")
    def test_tls_connection(self, mock_smtp: MagicMock) -> None:
        """测试STARTTLS连接."""
        mock_instance = MagicMock()
        mock_smtp.return_value = mock_instance

        account = SMTPAccount(name="test", host="smtp.test.com", port=587, use_tls=True)
        conn = SMTPConnection(account)
        conn.connect()

        self.assertTrue(conn.is_connected)
        mock_instance.starttls.assert_called_once()

    def test_disconnect(self) -> None:
        """测试断开连接."""
        account = SMTPAccount(name="test", host="smtp.test.com")
        conn = SMTPConnection(account)
        conn._connection = MagicMock()
        conn._connected = True
        conn.disconnect()
        self.assertFalse(conn.is_connected)


class TestMailer(unittest.TestCase):
    """Mailer测试."""

    def setUp(self) -> None:
        """测试前准备."""
        self.account = SMTPAccount(
            name="test",
            host="smtp.test.com",
            port=587,
            username="user@test.com",
            password="pass",
        )

    def test_build_message_text(self) -> None:
        """测试构建纯文本邮件."""
        mailer = Mailer(self.account)
        msg = mailer.build_message(
            to="recipient@example.com",
            subject="Test Subject",
            text_body="Hello, World!",
        )
        self.assertIsInstance(msg, MIMEMultipart)
        self.assertEqual(msg["To"], "recipient@example.com")
        self.assertEqual(msg["Subject"], "Test Subject")

    def test_build_message_html(self) -> None:
        """测试构建HTML邮件."""
        mailer = Mailer(self.account)
        msg = mailer.build_message(
            to="recipient@example.com",
            subject="Test Subject",
            html_body="<h1>Hello</h1>",
        )
        self.assertIsInstance(msg, MIMEMultipart)

    def test_build_message_with_cc_bcc(self) -> None:
        """测试构建带抄送/密送的邮件."""
        mailer = Mailer(self.account)
        msg = mailer.build_message(
            to="recipient@example.com",
            subject="Test",
            text_body="Body",
            cc=["cc1@example.com", "cc2@example.com"],
            bcc=["bcc@example.com"],
        )
        self.assertIn("cc1@example.com", msg["Cc"])
        self.assertIn("bcc@example.com", msg["Bcc"])

    def test_html_to_text(self) -> None:
        """测试HTML转纯文本."""
        html = "<h1>Title</h1><p>Hello<br>World</p>"
        text = Mailer._html_to_text(html)
        self.assertIn("Title", text)
        self.assertIn("Hello", text)
        self.assertIn("World", text)

    def test_personalize(self) -> None:
        """测试变量替换."""
        mailer = Mailer(self.account)
        template = "Hello, {{name}}! Your email is {{email}}."
        result = mailer._personalize(template, {"name": "Alice", "email": "alice@test.com"})
        self.assertEqual(result, "Hello, Alice! Your email is alice@test.com.")

    def test_close(self) -> None:
        """测试关闭发送引擎."""
        mailer = Mailer(self.account)
        mailer.close()  # 不应抛出异常


if __name__ == "__main__":
    unittest.main()
