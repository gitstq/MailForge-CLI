"""SMTP发送引擎模块 - SSL/TLS、认证、HTML/纯文本、附件.

支持SMTP/SMTPS/STARTTLS连接、连接池管理、HTML+纯文本multipart邮件、
附件支持、发送速率限制、自动重试（指数退避）、发送回调/钩子、
队列化异步批量发送。
"""

import logging
import mimetypes
import os
import queue
import smtplib
import threading
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from mailforge.core.config import SMTPAccount
from mailforge.utils.validators import RateLimiter

logger = logging.getLogger(__name__)


class MailerError(Exception):
    """发送引擎相关错误."""


class SMTPConnectionError(MailerError):
    """SMTP连接错误."""


class SendError(MailerError):
    """邮件发送错误."""


class SendResult:
    """单封邮件发送结果.

    Attributes:
        success: 是否成功.
        email: 收件人邮箱.
        message_id: 邮件Message-ID.
        error: 错误信息.
        timestamp: 发送时间戳.
        retries: 重试次数.
    """

    def __init__(
        self,
        success: bool,
        email: str,
        message_id: str = "",
        error: str = "",
        timestamp: Optional[float] = None,
        retries: int = 0,
    ) -> None:
        """初始化发送结果.

        Args:
            success: 是否成功.
            email: 收件人邮箱.
            message_id: 邮件Message-ID.
            error: 错误信息.
            timestamp: 发送时间戳.
            retries: 重试次数.
        """
        self.success = success
        self.email = email
        self.message_id = message_id
        self.error = error
        self.timestamp = timestamp or time.time()
        self.retries = retries

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "success": self.success,
            "email": self.email,
            "message_id": self.message_id,
            "error": self.error,
            "timestamp": self.timestamp,
            "retries": self.retries,
        }


# 发送回调类型
SendCallback = Callable[[SendResult], None]


class SMTPConnection:
    """SMTP连接封装.

    管理单个SMTP连接的建立、认证和关闭。

    Attributes:
        account: SMTP账户配置.
    """

    def __init__(self, account: SMTPAccount, timeout: int = 30) -> None:
        """初始化SMTP连接.

        Args:
            account: SMTP账户配置.
            timeout: 连接超时（秒）.
        """
        self.account = account
        self.timeout = timeout
        self._connection: Optional[smtplib.SMTP] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """是否已连接."""
        return self._connected and self._connection is not None

    def connect(self) -> None:
        """建立SMTP连接.

        Raises:
            SMTPConnectionError: 连接失败时抛出.
        """
        try:
            if self.account.use_ssl:
                self._connection = smtplib.SMTP_SSL(
                    self.account.host,
                    self.account.port,
                    timeout=self.timeout,
                )
            else:
                self._connection = smtplib.SMTP(
                    self.account.host,
                    self.account.port,
                    timeout=self.timeout,
                )
                if self.account.use_tls:
                    self._connection.starttls()

            # 认证
            if self.account.username and self.account.password:
                self._connection.login(
                    self.account.username,
                    self.account.password,
                )

            self._connected = True
            logger.info(
                "SMTP连接已建立: %s:%d (SSL=%s, TLS=%s)",
                self.account.host, self.account.port,
                self.account.use_ssl, self.account.use_tls,
            )

        except smtplib.SMTPException as e:
            self._connected = False
            raise SMTPConnectionError(f"SMTP连接失败: {e}") from e
        except OSError as e:
            self._connected = False
            raise SMTPConnectionError(f"网络错误: {e}") from e

    def disconnect(self) -> None:
        """关闭SMTP连接."""
        if self._connection:
            try:
                self._connection.quit()
            except Exception:
                pass
            self._connection = None
            self._connected = False
            logger.debug("SMTP连接已关闭")

    def send_message(self, msg: MIMEMultipart) -> Dict[str, Any]:
        """发送邮件消息.

        Args:
            msg: 邮件消息对象.

        Returns:
            SMTP服务器响应.

        Raises:
            SendError: 发送失败时抛出.
        """
        if not self.is_connected:
            raise SendError("SMTP未连接")

        try:
            return self._connection.send_message(msg)  # type: ignore[arg-type]
        except smtplib.SMTPRecipientsRefused as e:
            raise SendError(f"收件人被拒绝: {e.recipients}") from e
        except smtplib.SMTPDataError as e:
            raise SendError(f"邮件数据错误: {e}") from e
        except smtplib.SMTPException as e:
            raise SendError(f"SMTP错误: {e}") from e
        except OSError as e:
            self._connected = False
            raise SendError(f"网络错误: {e}") from e


class ConnectionPool:
    """SMTP连接池.

    管理多个SMTP连接，支持复用和自动重连。

    Attributes:
        account: SMTP账户配置.
        pool_size: 连接池大小.
    """

    def __init__(self, account: SMTPAccount, pool_size: int = 3, timeout: int = 30) -> None:
        """初始化连接池.

        Args:
            account: SMTP账户配置.
            pool_size: 连接池大小.
            timeout: 连接超时.
        """
        self.account = account
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool: queue.Queue = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self) -> None:
        """初始化连接池."""
        with self._lock:
            if self._initialized:
                return
            for _ in range(self.pool_size):
                conn = SMTPConnection(self.account, self.timeout)
                conn.connect()
                self._pool.put(conn)
            self._initialized = True
            logger.info("SMTP连接池已初始化，大小=%d", self.pool_size)

    def acquire(self) -> SMTPConnection:
        """获取一个连接.

        Returns:
            SMTPConnection实例.

        Raises:
            SMTPConnectionError: 获取失败时抛出.
        """
        if not self._initialized:
            self.initialize()

        try:
            conn = self._pool.get(timeout=5)
            if not conn.is_connected:
                conn.connect()
            return conn
        except queue.Empty:
            raise SMTPConnectionError("连接池已耗尽，无法获取连接")

    def release(self, conn: SMTPConnection) -> None:
        """释放连接回连接池.

        Args:
            conn: SMTPConnection实例.
        """
        if conn.is_connected:
            try:
                self._pool.put_nowait(conn)
            except queue.Full:
                conn.disconnect()
        else:
            conn.disconnect()

    def close_all(self) -> None:
        """关闭所有连接."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.disconnect()
            except queue.Empty:
                break
        self._initialized = False
        logger.info("SMTP连接池已关闭")


class Mailer:
    """SMTP邮件发送引擎.

    提供邮件构建、发送、批量发送、重试等功能。

    Usage:
        account = SMTPAccount(host="smtp.example.com", port=587, ...)
        mailer = Mailer(account)
        result = mailer.send(
            to="user@example.com",
            subject="Hello",
            body="World",
        )
    """

    def __init__(
        self,
        account: SMTPAccount,
        rate_limiter: Optional[RateLimiter] = None,
        retry_max: int = 3,
        retry_delay: float = 5.0,
        pool_size: int = 1,
        timeout: int = 30,
    ) -> None:
        """初始化邮件发送引擎.

        Args:
            account: SMTP账户配置.
            rate_limiter: 频率限制器.
            retry_max: 最大重试次数.
            retry_delay: 初始重试延迟（秒）.
            pool_size: 连接池大小.
            timeout: 连接超时.
        """
        self.account = account
        self.rate_limiter = rate_limiter or RateLimiter()
        self.retry_max = retry_max
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.pool = ConnectionPool(account, pool_size=pool_size, timeout=timeout)
        self._callbacks: List[SendCallback] = []
        self._results: List[SendResult] = []
        self._lock = threading.Lock()

    def add_callback(self, callback: SendCallback) -> None:
        """添加发送回调.

        Args:
            callback: 回调函数.
        """
        self._callbacks.append(callback)

    def _notify_callbacks(self, result: SendResult) -> None:
        """通知所有回调."""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error("回调执行失败: %s", e)

    def build_message(
        self,
        to: str,
        subject: str,
        html_body: str = "",
        text_body: str = "",
        from_name: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> MIMEMultipart:
        """构建邮件消息.

        Args:
            to: 收件人邮箱.
            subject: 邮件主题.
            html_body: HTML正文.
            text_body: 纯文本正文.
            from_name: 发件人显示名.
            from_email: 发件人邮箱.
            reply_to: 回复地址.
            cc: 抄送列表.
            bcc: 密送列表.
            attachments: 附件文件路径列表.
            headers: 自定义邮件头.

        Returns:
            MIMEMultipart消息对象.
        """
        msg = MIMEMultipart("alternative")

        # 发件人
        sender_email = from_email or self.account.from_email or self.account.username
        sender_name = from_name or self.account.from_name
        if sender_name:
            msg["From"] = formataddr((sender_name, sender_email))
        else:
            msg["From"] = sender_email

        # 收件人
        msg["To"] = to

        # 抄送/密送
        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)

        # 回复地址
        if reply_to:
            msg["Reply-To"] = reply_to

        # 主题
        msg["Subject"] = subject

        # 标准头
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=sender_email.split("@")[-1] if "@" in sender_email else "localhost")

        # 自定义头
        if headers:
            for key, value in headers.items():
                msg[key] = value

        # 正文
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))

        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        # 如果没有纯文本正文但有HTML，自动生成纯文本版本
        if not text_body and html_body:
            plain = self._html_to_text(html_body)
            msg.attach(MIMEText(plain, "plain", "utf-8"))

        # 附件
        if attachments:
            for file_path in attachments:
                self._attach_file(msg, file_path)

        return msg

    def send(
        self,
        to: str,
        subject: str,
        html_body: str = "",
        text_body: str = "",
        from_name: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> SendResult:
        """发送单封邮件.

        Args:
            to: 收件人邮箱.
            subject: 邮件主题.
            html_body: HTML正文.
            text_body: 纯文本正文.
            from_name: 发件人显示名.
            from_email: 发件人邮箱.
            reply_to: 回复地址.
            cc: 抄送列表.
            bcc: 密送列表.
            attachments: 附件文件路径列表.
            headers: 自定义邮件头.

        Returns:
            SendResult发送结果.
        """
        msg = self.build_message(
            to=to, subject=subject, html_body=html_body, text_body=text_body,
            from_name=from_name, from_email=from_email, reply_to=reply_to,
            cc=cc, bcc=bcc, attachments=attachments, headers=headers,
        )

        message_id = msg.get("Message-ID", "")

        # 频率限制
        self.rate_limiter.acquire()

        # 带重试的发送
        last_error = ""
        retries = 0

        for attempt in range(self.retry_max + 1):
            try:
                conn = self.pool.acquire()
                try:
                    conn.send_message(msg)
                    result = SendResult(
                        success=True,
                        email=to,
                        message_id=message_id,
                        retries=retries,
                    )
                    self._record_result(result)
                    return result
                finally:
                    self.pool.release(conn)

            except (SendError, SMTPConnectionError) as e:
                last_error = str(e)
                retries += 1
                if attempt < self.retry_max:
                    delay = self.retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        "发送失败（第%d次），%0.1f秒后重试: %s",
                        attempt + 1, delay, last_error,
                    )
                    time.sleep(delay)

        result = SendResult(
            success=False,
            email=to,
            message_id=message_id,
            error=last_error,
            retries=retries - 1,
        )
        self._record_result(result)
        return result

    def send_batch(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        html_body: str = "",
        text_body: str = "",
        attachments: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[int, int, SendResult], None]] = None,
    ) -> List[SendResult]:
        """批量发送邮件.

        Args:
            recipients: 收件人列表，每项包含 email, name 等字段.
            subject: 邮件主题（支持模板变量）.
            html_body: HTML正文（支持模板变量）.
            text_body: 纯文本正文（支持模板变量）.
            attachments: 附件列表.
            headers: 自定义头.
            progress_callback: 进度回调 (当前索引, 总数, 结果).

        Returns:
            SendResult列表.
        """
        results: List[SendResult] = []
        total = len(recipients)

        logger.info("开始批量发送: %d 封邮件", total)

        for idx, recipient in enumerate(recipients):
            email = recipient.get("email", "")
            name = recipient.get("name", "")

            if not email:
                logger.warning("跳过无效收件人: %s", recipient)
                continue

            # 个性化替换
            personalized_subject = self._personalize(subject, recipient)
            personalized_html = self._personalize(html_body, recipient)
            personalized_text = self._personalize(text_body, recipient)

            result = self.send(
                to=formataddr((name, email)) if name else email,
                subject=personalized_subject,
                html_body=personalized_html,
                text_body=personalized_text,
                attachments=attachments,
                headers=headers,
            )

            results.append(result)

            if progress_callback:
                progress_callback(idx + 1, total, result)

        logger.info(
            "批量发送完成: 成功=%d, 失败=%d",
            sum(1 for r in results if r.success),
            sum(1 for r in results if not r.success),
        )
        return results

    def send_async(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        html_body: str = "",
        text_body: str = "",
        attachments: Optional[List[str]] = None,
        max_workers: int = 3,
    ) -> List[SendResult]:
        """异步批量发送（使用线程池）.

        Args:
            recipients: 收件人列表.
            subject: 邮件主题.
            html_body: HTML正文.
            text_body: 纯文本正文.
            attachments: 附件列表.
            max_workers: 最大工作线程数.

        Returns:
            SendResult列表.
        """
        results: List[SendResult] = []
        result_lock = threading.Lock()
        task_queue: queue.Queue = queue.Queue()

        # 填充任务队列
        for recipient in recipients:
            task_queue.put(recipient)

        def worker() -> None:
            while True:
                try:
                    recipient = task_queue.get_nowait()
                except queue.Empty:
                    break

                email = recipient.get("email", "")
                name = recipient.get("name", "")
                if not email:
                    continue

                personalized_subject = self._personalize(subject, recipient)
                personalized_html = self._personalize(html_body, recipient)
                personalized_text = self._personalize(text_body, recipient)

                result = self.send(
                    to=formataddr((name, email)) if name else email,
                    subject=personalized_subject,
                    html_body=personalized_html,
                    text_body=personalized_text,
                    attachments=attachments,
                )

                with result_lock:
                    results.append(result)

                task_queue.task_done()

        threads = [
            threading.Thread(target=worker, daemon=True)
            for _ in range(max_workers)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        return results

    def get_results(self) -> List[SendResult]:
        """获取所有发送结果.

        Returns:
            SendResult列表.
        """
        with self._lock:
            return list(self._results)

    def clear_results(self) -> None:
        """清除发送结果."""
        with self._lock:
            self._results.clear()

    def _record_result(self, result: SendResult) -> None:
        """记录发送结果."""
        with self._lock:
            self._results.append(result)
        self._notify_callbacks(result)

    def _personalize(self, template: str, context: Dict[str, Any]) -> str:
        """简单的变量替换（不使用完整模板引擎）.

        支持 {{name}}, {{email}} 等简单变量。

        Args:
            template: 模板字符串.
            context: 变量上下文.

        Returns:
            替换后的字符串.
        """
        import re
        def replacer(match: re.Match) -> str:
            key = match.group(1).strip()
            value = context.get(key, match.group(0))
            return str(value)
        return re.sub(r"\{\{(\w+)\}\}", replacer, template)

    def _attach_file(self, msg: MIMEMultipart, file_path: str) -> None:
        """添加附件到邮件.

        Args:
            msg: 邮件消息对象.
            file_path: 附件文件路径.
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning("附件文件不存在: %s", file_path)
            return

        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        main_type, sub_type = mime_type.split("/", 1)

        try:
            with open(path, "rb") as f:
                file_data = f.read()
        except OSError as e:
            logger.warning("读取附件失败: %s", e)
            return

        attachment = MIMEBase(main_type, sub_type)
        attachment.set_payload(file_data)
        encoders.encode_base64(attachment)

        # 处理中文文件名
        filename = path.name
        try:
            filename.encode("ascii")
            attachment.add_header("Content-Disposition", "attachment", filename=filename)
        except UnicodeEncodeError:
            from email.header import Header
            attachment.add_header(
                "Content-Disposition", "attachment",
                filename=("utf-8", "", filename),
            )

        msg.attach(attachment)

    @staticmethod
    def _html_to_text(html: str) -> str:
        """简单的HTML转纯文本.

        Args:
            html: HTML字符串.

        Returns:
            纯文本字符串.
        """
        import re
        # 移除script和style
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # 移除标签
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</h[1-6]>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        # 解码HTML实体
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")
        # 清理空白
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        return text

    def close(self) -> None:
        """关闭发送引擎，释放所有资源."""
        self.pool.close_all()
        logger.info("邮件发送引擎已关闭")
