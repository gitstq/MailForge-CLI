"""IMAP接收引擎模块 - 收件箱读取、搜索、解析、退信检测.

支持IMAP/IMAPS连接、邮件搜索（按日期、发件人、主题、未读等）、
邮件解析（提取正文、附件、headers）、退信检测、自动标记/移动邮件。
"""

import email
import email.header
import imaplib
import logging
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mailforge.core.config import IMAPAccount

logger = logging.getLogger(__name__)


class ReceiverError(Exception):
    """接收引擎相关错误."""


class IMAPConnectionError(ReceiverError):
    """IMAP连接错误."""


class MailMessage:
    """解析后的邮件消息.

    Attributes:
        uid: 邮件UID.
        message_id: Message-ID头.
        from_addr: 发件人地址.
        from_name: 发件人名称.
        to_addr: 收件人地址.
        cc_addr: 抄送地址.
        subject: 邮件主题.
        date: 邮件日期.
        text_body: 纯文本正文.
        html_body: HTML正文.
        attachments: 附件列表.
        headers: 所有邮件头.
        is_read: 是否已读.
        is_bounce: 是否为退信.
        folder: 所在文件夹.
    """

    def __init__(self, uid: str = "", folder: str = "INBOX") -> None:
        """初始化邮件消息.

        Args:
            uid: 邮件UID.
            folder: 所在文件夹.
        """
        self.uid = uid
        self.folder = folder
        self.message_id: str = ""
        self.from_addr: str = ""
        self.from_name: str = ""
        self.to_addr: str = ""
        self.cc_addr: str = ""
        self.subject: str = ""
        self.date: Optional[datetime] = None
        self.text_body: str = ""
        self.html_body: str = ""
        self.attachments: List[Dict[str, Any]] = []
        self.headers: Dict[str, str] = {}
        self.is_read: bool = False
        self.is_bounce: bool = False
        self.size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "uid": self.uid,
            "folder": self.folder,
            "message_id": self.message_id,
            "from_addr": self.from_addr,
            "from_name": self.from_name,
            "to_addr": self.to_addr,
            "cc_addr": self.cc_addr,
            "subject": self.subject,
            "date": self.date.isoformat() if self.date else None,
            "text_body": self.text_body[:500] + "..." if len(self.text_body) > 500 else self.text_body,
            "html_body": self.html_body[:500] + "..." if len(self.html_body) > 500 else self.html_body,
            "has_attachments": len(self.attachments) > 0,
            "attachment_count": len(self.attachments),
            "is_read": self.is_read,
            "is_bounce": self.is_bounce,
            "size": self.size,
        }


# 退信检测模式
BOUNCE_PATTERNS = [
    re.compile(r"delivery\s+(?:status|failure|report)", re.IGNORECASE),
    re.compile(r"undeliverable", re.IGNORECASE),
    re.compile(r"returned\s+mail", re.IGNORECASE),
    re.compile(r"mail\s+delivery\s+failed", re.IGNORECASE),
    re.compile(r"permanent\s+failure", re.IGNORECASE),
    re.compile(r"temporary\s+failure", re.IGNORECASE),
    re.compile(r"user\s+(?:unknown|not\s+found|does\s+not\s+exist)", re.IGNORECASE),
    re.compile(r"mailbox\s+(?:full|unavailable|not\s+found)", re.IGNORECASE),
    re.compile(r"host\s+not\s+found", re.IGNORECASE),
    re.compile(r"connection\s+timed?\s*out", re.IGNORECASE),
    re.compile(r"550\s+\d", re.IGNORECASE),
    re.compile(r"552\s+\d", re.IGNORECASE),
    re.compile(r"553\s+\d", re.IGNORECASE),
    re.compile(r"554\s+\d", re.IGNORECASE),
]

# 退信邮件常见发件人
BOUNCE_SENDERS = [
    "mailer-daemon",
    "postmaster",
    "noreply",
    "mail-daemon",
    "bounce",
    "delivery-status",
]


class IMAPConnection:
    """IMAP连接封装.

    管理单个IMAP连接的建立、认证和关闭。
    """

    def __init__(self, account: IMAPAccount, timeout: int = 30) -> None:
        """初始化IMAP连接.

        Args:
            account: IMAP账户配置.
            timeout: 连接超时（秒）.
        """
        self.account = account
        self.timeout = timeout
        self._connection: Optional[imaplib.IMAP4] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """是否已连接."""
        return self._connected and self._connection is not None

    def connect(self) -> None:
        """建立IMAP连接.

        Raises:
            IMAPConnectionError: 连接失败时抛出.
        """
        try:
            if self.account.use_ssl:
                self._connection = imaplib.IMAP4_SSL(
                    self.account.host,
                    self.account.port,
                    timeout=self.timeout,
                )
            else:
                self._connection = imaplib.IMAP4(
                    self.account.host,
                    self.account.port,
                    timeout=self.timeout,
                )

            if self.account.username and self.account.password:
                self._connection.login(
                    self.account.username,
                    self.account.password,
                )

            self._connected = True
            logger.info("IMAP连接已建立: %s:%d", self.account.host, self.account.port)

        except imaplib.IMAP4.error as e:
            self._connected = False
            raise IMAPConnectionError(f"IMAP连接失败: {e}") from e
        except OSError as e:
            self._connected = False
            raise IMAPConnectionError(f"网络错误: {e}") from e

    def disconnect(self) -> None:
        """关闭IMAP连接."""
        if self._connection:
            try:
                self._connection.logout()
            except Exception:
                pass
            self._connection = None
            self._connected = False
            logger.debug("IMAP连接已关闭")

    def select_folder(self, folder: str = "INBOX") -> int:
        """选择文件夹.

        Args:
            folder: 文件夹名称.

        Returns:
            文件夹中的邮件数量.

        Raises:
            IMAPConnectionError: 操作失败时抛出.
        """
        if not self.is_connected:
            raise IMAPConnectionError("IMAP未连接")

        status, data = self._connection.select(folder, readonly=True)
        if status != "OK":
            raise IMAPConnectionError(f"选择文件夹失败: {folder}")

        return int(data[0])

    def search(
        self,
        criteria: str = "ALL",
        folder: str = "INBOX",
    ) -> List[str]:
        """搜索邮件.

        Args:
            criteria: IMAP搜索条件.
            folder: 搜索的文件夹.

        Returns:
            匹配的邮件UID列表.

        Raises:
            IMAPConnectionError: 搜索失败时抛出.
        """
        if not self.is_connected:
            raise IMAPConnectionError("IMAP未连接")

        self.select_folder(folder)

        status, data = self._connection.uid("search", None, criteria)
        if status != "OK":
            return []

        if data and data[0]:
            return data[0].split()
        return []

    def fetch_message(self, uid: str, folder: str = "INBOX") -> MailMessage:
        """获取单封邮件.

        Args:
            uid: 邮件UID.
            folder: 文件夹名称.

        Returns:
            解析后的MailMessage.

        Raises:
            IMAPConnectionError: 获取失败时抛出.
        """
        if not self.is_connected:
            raise IMAPConnectionError("IMAP未连接")

        self.select_folder(folder)

        status, data = self._connection.uid("fetch", uid, "(RFC822)")
        if status != "OK" or not data or not data[0]:
            raise IMAPConnectionError(f"获取邮件失败: UID={uid}")

        raw_email = data[0][1]  # type: ignore[index-type]
        msg = email.message_from_bytes(raw_email)
        return self._parse_message(msg, uid, folder)

    def fetch_headers(self, uid: str, folder: str = "INBOX") -> Dict[str, str]:
        """获取邮件头.

        Args:
            uid: 邮件UID.
            folder: 文件夹名称.

        Returns:
            邮件头字典.
        """
        if not self.is_connected:
            raise IMAPConnectionError("IMAP未连接")

        self.select_folder(folder)

        status, data = self._connection.uid("fetch", uid, "(BODY[HEADER])")
        if status != "OK" or not data or not data[0]:
            return {}

        raw_header = data[0][1]  # type: ignore[index-type]
        msg = email.message_from_bytes(raw_header)
        return dict(msg.items())

    def mark_as_read(self, uid: str, folder: str = "INBOX") -> bool:
        """标记邮件为已读.

        Args:
            uid: 邮件UID.
            folder: 文件夹名称.

        Returns:
            是否成功.
        """
        if not self.is_connected:
            return False

        try:
            self._connection.select(folder)
            status, _ = self._connection.uid("store", uid, "+FLAGS", "\\Seen")
            return status == "OK"
        except Exception as e:
            logger.error("标记已读失败: %s", e)
            return False

    def move_message(self, uid: str, target_folder: str, source_folder: str = "INBOX") -> bool:
        """移动邮件到目标文件夹.

        Args:
            uid: 邮件UID.
            target_folder: 目标文件夹.
            source_folder: 源文件夹.

        Returns:
            是否成功.
        """
        if not self.is_connected:
            return False

        try:
            self._connection.select(source_folder)
            status, _ = self._connection.uid("copy", uid, target_folder)
            if status == "OK":
                status, _ = self._connection.uid("store", uid, "+FLAGS", "\\Deleted")
                if status == "OK":
                    self._connection.expunge()
                    return True
        except Exception as e:
            logger.error("移动邮件失败: %s", e)
        return False

    def list_folders(self) -> List[str]:
        """列出所有文件夹.

        Returns:
            文件夹名称列表.
        """
        if not self.is_connected:
            return []

        try:
            status, data = self._connection.list()
            if status != "OK":
                return []

            folders: List[str] = []
            for item in data:
                if isinstance(item, (list, tuple)):
                    item = item[-1]
                if isinstance(item, bytes):
                    decoded = item.decode("utf-8", errors="replace")
                    # 提取文件夹名
                    parts = decoded.rsplit('"', 2)
                    if len(parts) >= 2:
                        folders.append(parts[-1].strip())
            return folders
        except Exception as e:
            logger.error("列出文件夹失败: %s", e)
            return []

    def _parse_message(self, msg: email.message.Message, uid: str, folder: str) -> MailMessage:
        """解析原始邮件消息.

        Args:
            msg: email.message.Message对象.
            uid: 邮件UID.
            folder: 文件夹名称.

        Returns:
            解析后的MailMessage.
        """
        mail_msg = MailMessage(uid=uid, folder=folder)

        # 解析头
        mail_msg.message_id = msg.get("Message-ID", "")
        mail_msg.subject = self._decode_header(msg.get("Subject", ""))
        mail_msg.date = self._parse_date(msg.get("Date", ""))

        # 发件人
        from_header = msg.get("From", "")
        mail_msg.from_name, mail_msg.from_addr = self._parse_address(from_header)

        # 收件人
        to_header = msg.get("To", "")
        _, mail_msg.to_addr = self._parse_address(to_header)

        # 抄送
        cc_header = msg.get("Cc", "")
        _, mail_msg.cc_addr = self._parse_address(cc_header)

        # 所有头
        for key, value in msg.items():
            mail_msg.headers[key] = self._decode_header(value)

        # 已读状态
        flags = msg.get("Flags", "")
        mail_msg.is_read = "\\Seen" in flags

        # 解析正文和附件
        if msg.is_multipart():
            self._parse_multipart(msg, mail_msg)
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode("utf-8", errors="replace")
                if content_type == "text/plain":
                    mail_msg.text_body = text
                elif content_type == "text/html":
                    mail_msg.html_body = text

        # 退信检测
        mail_msg.is_bounce = self._detect_bounce(mail_msg)

        return mail_msg

    def _parse_multipart(self, msg: email.message.Message, mail_msg: MailMessage) -> None:
        """解析multipart邮件.

        Args:
            msg: 邮件消息.
            mail_msg: MailMessage对象.
        """
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # 附件
            if "attachment" in content_disposition:
                attachment_info = self._parse_attachment(part)
                if attachment_info:
                    mail_msg.attachments.append(attachment_info)
                continue

            if "inline" in content_disposition and part.get_filename():
                attachment_info = self._parse_attachment(part)
                if attachment_info:
                    mail_msg.attachments.append(attachment_info)
                continue

            # 正文
            payload = part.get_payload(decode=True)
            if not payload:
                continue

            text = payload.decode("utf-8", errors="replace")
            if content_type == "text/plain":
                mail_msg.text_body = text
            elif content_type == "text/html":
                mail_msg.html_body = text

    def _parse_attachment(self, part: email.message.Message) -> Optional[Dict[str, Any]]:
        """解析附件.

        Args:
            part: 邮件部分.

        Returns:
            附件信息字典或None.
        """
        filename = part.get_filename()
        if not filename:
            return None

        filename = self._decode_header(filename)
        payload = part.get_payload(decode=True)
        if not payload:
            return None

        return {
            "filename": filename,
            "content_type": part.get_content_type(),
            "size": len(payload),
            "data": payload,
        }

    @staticmethod
    def _decode_header(value: str) -> str:
        """解码邮件头.

        Args:
            value: 原始头值.

        Returns:
            解码后的字符串.
        """
        if not value:
            return ""

        try:
            decoded_parts = email.header.decode_header(value)
            parts: List[str] = []
            for data, charset in decoded_parts:
                if isinstance(data, bytes):
                    parts.append(data.decode(charset or "utf-8", errors="replace"))
                else:
                    parts.append(data)
            return "".join(parts)
        except Exception:
            return value

    @staticmethod
    def _parse_address(addr_str: str) -> Tuple[str, str]:
        """解析邮件地址.

        Args:
            addr_str: 地址字符串.

        Returns:
            (名称, 地址) 元组.
        """
        if not addr_str:
            return "", ""

        from email.utils import parseaddr
        name, addr = parseaddr(addr_str)
        return name, addr

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """解析邮件日期.

        Args:
            date_str: 日期字符串.

        Returns:
            datetime对象或None.
        """
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return None

    @staticmethod
    def _detect_bounce(mail_msg: MailMessage) -> bool:
        """检测是否为退信邮件.

        Args:
            mail_msg: 邮件消息.

        Returns:
            是否为退信.
        """
        # 检查发件人
        from_lower = mail_msg.from_addr.lower()
        for bounce_sender in BOUNCE_SENDERS:
            if bounce_sender in from_lower:
                return True

        # 检查主题
        subject_lower = mail_msg.subject.lower()
        for pattern in BOUNCE_PATTERNS:
            if pattern.search(subject_lower):
                return True

        # 检查正文
        text_lower = mail_msg.text_body.lower()
        for pattern in BOUNCE_PATTERNS:
            if pattern.search(text_lower):
                return True

        return False


class Receiver:
    """IMAP邮件接收引擎.

    提供邮件搜索、读取、解析、退信检测等功能。

    Usage:
        account = IMAPAccount(host="imap.example.com", port=993, ...)
        receiver = Receiver(account)
        messages = receiver.search_unread()
    """

    def __init__(self, account: IMAPAccount, timeout: int = 30) -> None:
        """初始化接收引擎.

        Args:
            account: IMAP账户配置.
            timeout: 连接超时.
        """
        self.account = account
        self.timeout = timeout
        self._connection: Optional[IMAPConnection] = None

    def connect(self) -> None:
        """建立IMAP连接.

        Raises:
            IMAPConnectionError: 连接失败时抛出.
        """
        self._connection = IMAPConnection(self.account, self.timeout)
        self._connection.connect()

    def disconnect(self) -> None:
        """关闭IMAP连接."""
        if self._connection:
            self._connection.disconnect()
            self._connection = None

    @property
    def is_connected(self) -> bool:
        """是否已连接."""
        return self._connection is not None and self._connection.is_connected

    def _ensure_connected(self) -> None:
        """确保已连接."""
        if not self.is_connected:
            self.connect()

    def search(
        self,
        criteria: str = "ALL",
        folder: str = "INBOX",
        limit: int = 50,
    ) -> List[MailMessage]:
        """搜索邮件.

        Args:
            criteria: IMAP搜索条件.
            folder: 搜索文件夹.
            limit: 最大返回数量.

        Returns:
            MailMessage列表.
        """
        self._ensure_connected()
        assert self._connection is not None

        uids = self._connection.search(criteria, folder)
        uids = uids[-limit:]  # 取最新的

        messages: List[MailMessage] = []
        for uid in uids:
            try:
                msg = self._connection.fetch_message(uid.decode(), folder)
                messages.append(msg)
            except Exception as e:
                logger.error("获取邮件失败 UID=%s: %s", uid, e)

        return messages

    def search_unread(self, folder: str = "INBOX", limit: int = 50) -> List[MailMessage]:
        """搜索未读邮件.

        Args:
            folder: 文件夹名称.
            limit: 最大返回数量.

        Returns:
            未读邮件列表.
        """
        return self.search("UNSEEN", folder, limit)

    def search_by_sender(self, sender: str, folder: str = "INBOX", limit: int = 50) -> List[MailMessage]:
        """按发件人搜索.

        Args:
            sender: 发件人地址.
            folder: 文件夹名称.
            limit: 最大返回数量.

        Returns:
            匹配的邮件列表.
        """
        return self.search(f'FROM "{sender}"', folder, limit)

    def search_by_subject(self, subject: str, folder: str = "INBOX", limit: int = 50) -> List[MailMessage]:
        """按主题搜索.

        Args:
            subject: 主题关键词.
            folder: 文件夹名称.
            limit: 最大返回数量.

        Returns:
            匹配的邮件列表.
        """
        return self.search(f'SUBJECT "{subject}"', folder, limit)

    def search_by_date(
        self,
        since: Optional[datetime] = None,
        before: Optional[datetime] = None,
        folder: str = "INBOX",
        limit: int = 50,
    ) -> List[MailMessage]:
        """按日期范围搜索.

        Args:
            since: 起始日期.
            before: 结束日期.
            folder: 文件夹名称.
            limit: 最大返回数量.

        Returns:
            匹配的邮件列表.
        """
        criteria_parts: List[str] = []
        if since:
            criteria_parts.append(f'SINCE {since.strftime("%d-%b-%Y")}')
        if before:
            criteria_parts.append(f'BEFORE {before.strftime("%d-%b-%Y")}')

        criteria = " ".join(criteria_parts) if criteria_parts else "ALL"
        return self.search(criteria, folder, limit)

    def search_bounces(self, folder: str = "INBOX", limit: int = 50) -> List[MailMessage]:
        """搜索退信邮件.

        Args:
            folder: 文件夹名称.
            limit: 最大返回数量.

        Returns:
            退信邮件列表.
        """
        all_messages = self.search("ALL", folder, limit)
        return [msg for msg in all_messages if msg.is_bounce]

    def get_message(self, uid: str, folder: str = "INBOX") -> Optional[MailMessage]:
        """获取单封邮件.

        Args:
            uid: 邮件UID.
            folder: 文件夹名称.

        Returns:
            MailMessage或None.
        """
        self._ensure_connected()
        assert self._connection is not None

        try:
            return self._connection.fetch_message(uid, folder)
        except Exception as e:
            logger.error("获取邮件失败: %s", e)
            return None

    def list_folders(self) -> List[str]:
        """列出所有文件夹.

        Returns:
            文件夹列表.
        """
        self._ensure_connected()
        assert self._connection is not None
        return self._connection.list_folders()

    def get_inbox_count(self) -> int:
        """获取收件箱邮件数量.

        Returns:
            邮件数量.
        """
        self._ensure_connected()
        assert self._connection is not None
        return self._connection.select_folder("INBOX")

    def mark_as_read(self, uid: str, folder: str = "INBOX") -> bool:
        """标记邮件为已读.

        Args:
            uid: 邮件UID.
            folder: 文件夹名称.

        Returns:
            是否成功.
        """
        self._ensure_connected()
        assert self._connection is not None
        return self._connection.mark_as_read(uid, folder)

    def move_message(self, uid: str, target_folder: str, source_folder: str = "INBOX") -> bool:
        """移动邮件.

        Args:
            uid: 邮件UID.
            target_folder: 目标文件夹.
            source_folder: 源文件夹.

        Returns:
            是否成功.
        """
        self._ensure_connected()
        assert self._connection is not None
        return self._connection.move_message(uid, target_folder, source_folder)

    def close(self) -> None:
        """关闭接收引擎."""
        self.disconnect()
        logger.info("邮件接收引擎已关闭")
