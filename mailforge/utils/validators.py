"""验证器模块 - 邮箱验证、内容检查、频率限制.

提供RFC 5322邮箱验证、内容安全检查、发送频率限制检查等功能。
"""

import logging
import re
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证相关错误."""


# RFC 5322 简化版邮箱正则
EMAIL_REGEX = re.compile(
    r"^(?=.{1,254}$)(?=.{1,64}@)[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}$"
)

# 常见域名后缀
COMMON_TLDS = {
    "com", "org", "net", "edu", "gov", "mil", "int",
    "cn", "jp", "uk", "de", "fr", "au", "ca", "ru", "br", "in",
    "io", "co", "me", "info", "biz", "xyz", "top", "vip", "club",
    "online", "site", "app", "dev", "cloud", "tech", "ai",
}

# 垃圾邮件关键词
SPAM_KEYWORDS = {
    "free money", "click here", "act now", "limited time",
    "congratulations you won", "no obligation", "winner",
    "100% free", "you have been selected", "earn money",
    "risk free", "guaranteed", "no credit check",
}

# 敏感内容模式
SENSITIVE_PATTERNS = [
    re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
]


def validate_email(email: str) -> Tuple[bool, str]:
    """验证邮箱地址格式.

    根据RFC 5322标准验证邮箱地址格式。

    Args:
        email: 待验证的邮箱地址.

    Returns:
        (是否有效, 错误信息) 元组.
    """
    if not email or not email.strip():
        return False, "邮箱地址不能为空"

    email = email.strip().lower()

    if len(email) > 254:
        return False, "邮箱地址过长（最大254字符）"

    if email.count("@") != 1:
        return False, "邮箱地址必须包含且仅包含一个@符号"

    local_part, domain = email.rsplit("@", 1)

    if not local_part:
        return False, "本地部分不能为空"

    if not domain:
        return False, "域名部分不能为空"

    if len(local_part) > 64:
        return False, "本地部分过长（最大64字符）"

    if ".." in local_part:
        return False, "本地部分不能包含连续的点号"

    if domain.startswith(".") or domain.endswith("."):
        return False, "域名不能以点号开头或结尾"

    if not EMAIL_REGEX.match(email):
        return False, "邮箱地址格式不正确"

    return True, ""


def validate_email_batch(emails: List[str]) -> Dict[str, Tuple[bool, str]]:
    """批量验证邮箱地址.

    Args:
        emails: 邮箱地址列表.

    Returns:
        {邮箱: (是否有效, 错误信息)} 字典.
    """
    results: Dict[str, Tuple[bool, str]] = {}
    for email in emails:
        results[email] = validate_email(email)
    return results


def check_content_safety(
    subject: str,
    body: str,
    strict: bool = False,
) -> Tuple[bool, List[str]]:
    """检查邮件内容安全性.

    检测潜在的垃圾邮件特征和危险内容。

    Args:
        subject: 邮件主题.
        body: 邮件正文.
        strict: 是否启用严格模式.

    Returns:
        (是否安全, 警告列表) 元组.
    """
    warnings: List[str] = []
    combined = f"{subject} {body}".lower()

    # 检查垃圾邮件关键词
    for keyword in SPAM_KEYWORDS:
        if keyword in combined:
            warnings.append(f"包含垃圾邮件关键词: '{keyword}'")

    # 检查敏感HTML模式
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(body):
            warnings.append("邮件内容包含潜在危险的HTML/JavaScript代码")

    # 检查主题长度
    if len(subject) > 200:
        warnings.append("邮件主题过长，可能被标记为垃圾邮件")

    # 检查正文中的URL数量
    url_count = len(re.findall(r"https?://", body))
    if url_count > 10:
        warnings.append(f"邮件包含过多链接（{url_count}个），可能被标记为垃圾邮件")

    # 检查大写字母比例
    if strict and body:
        upper_ratio = sum(1 for c in body if c.isupper()) / max(len(body), 1)
        if upper_ratio > 0.5 and len(body) > 50:
            warnings.append("大写字母比例过高，可能被标记为垃圾邮件")

    # 检查重复字符
    if strict:
        repeat_pattern = re.compile(r"(.)\1{5,}")
        if repeat_pattern.search(body):
            warnings.append("正文中包含过多重复字符")

    is_safe = len(warnings) == 0
    return is_safe, warnings


class RateLimiter:
    """发送频率限制器.

    支持每分钟和每小时的发送速率限制，使用滑动窗口算法。

    Attributes:
        per_minute: 每分钟最大发送数.
        per_hour: 每小时最大发送数.
    """

    def __init__(self, per_minute: int = 60, per_hour: int = 500) -> None:
        """初始化频率限制器.

        Args:
            per_minute: 每分钟最大发送数.
            per_hour: 每小时最大发送数.
        """
        self.per_minute = per_minute
        self.per_hour = per_hour
        self._minute_timestamps: List[float] = []
        self._hour_timestamps: List[float] = []

    def check(self) -> Tuple[bool, Optional[float]]:
        """检查是否可以发送.

        Returns:
            (是否可以发送, 需要等待的秒数) 元组.
        """
        now = time.time()

        # 清理过期的时间戳
        self._minute_timestamps = [
            t for t in self._minute_timestamps if now - t < 60
        ]
        self._hour_timestamps = [
            t for t in self._hour_timestamps if now - t < 3600
        ]

        # 检查每分钟限制
        if len(self._minute_timestamps) >= self.per_minute:
            oldest = min(self._minute_timestamps)
            wait_time = 60 - (now - oldest)
            return False, max(wait_time, 0.1)

        # 检查每小时限制
        if len(self._hour_timestamps) >= self.per_hour:
            oldest = min(self._hour_timestamps)
            wait_time = 3600 - (now - oldest)
            return False, max(wait_time, 0.1)

        return True, None

    def record(self) -> None:
        """记录一次发送."""
        now = time.time()
        self._minute_timestamps.append(now)
        self._hour_timestamps.append(now)

    def acquire(self) -> float:
        """获取发送许可，必要时等待.

        Returns:
            实际等待的秒数.
        """
        can_send, wait_time = self.check()
        if not can_send and wait_time is not None:
            time.sleep(wait_time)
        self.record()
        return wait_time or 0.0

    def reset(self) -> None:
        """重置所有计数器."""
        self._minute_timestamps.clear()
        self._hour_timestamps.clear()

    @property
    def minute_count(self) -> int:
        """当前分钟窗口内的发送计数."""
        now = time.time()
        return len([t for t in self._minute_timestamps if now - t < 60])

    @property
    def hour_count(self) -> int:
        """当前小时窗口内的发送计数."""
        now = time.time()
        return len([t for t in self._hour_timestamps if now - t < 3600])
