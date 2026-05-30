"""配置管理模块 - 多账户配置、环境变量覆盖、配置文件管理.

支持多SMTP账户配置、默认发送参数、环境变量覆盖（MAILFORGE_SMTP_HOST等），
配置文件存储在 ~/.mailforge/config.json。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CONFIG_DIR_NAME = ".mailforge"
CONFIG_FILE_NAME = "config.json"
DEFAULT_SMTP_PORT = 587
DEFAULT_IMAP_PORT = 993
DEFAULT_SEND_RATE_LIMIT = 60  # 每分钟
DEFAULT_HOURLY_LIMIT = 500
DEFAULT_RETRY_MAX = 3
DEFAULT_RETRY_DELAY = 5.0
DEFAULT_CONNECTION_TIMEOUT = 30


class ConfigError(Exception):
    """配置相关错误."""


class SMTPAccount:
    """SMTP账户配置.

    Attributes:
        name: 账户名称.
        host: SMTP服务器地址.
        port: SMTP端口.
        username: 用户名/邮箱.
        password: 密码（加密存储）.
        use_tls: 是否使用STARTTLS.
        use_ssl: 是否使用SSL/TLS直接连接.
        from_name: 发件人显示名.
        from_email: 发件人邮箱（可覆盖username）.
    """

    def __init__(
        self,
        name: str,
        host: str = "",
        port: int = DEFAULT_SMTP_PORT,
        username: str = "",
        password: str = "",
        use_tls: bool = True,
        use_ssl: bool = False,
        from_name: str = "",
        from_email: str = "",
    ) -> None:
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.from_name = from_name
        self.from_email = from_email or username

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "from_name": self.from_name,
            "from_email": self.from_email,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SMTPAccount":
        """从字典反序列化."""
        return cls(
            name=data.get("name", ""),
            host=data.get("host", ""),
            port=data.get("port", DEFAULT_SMTP_PORT),
            username=data.get("username", ""),
            password=data.get("password", ""),
            use_tls=data.get("use_tls", True),
            use_ssl=data.get("use_ssl", False),
            from_name=data.get("from_name", ""),
            from_email=data.get("from_email", ""),
        )


class IMAPAccount:
    """IMAP账户配置.

    Attributes:
        host: IMAP服务器地址.
        port: IMAP端口.
        username: 用户名.
        password: 密码（加密存储）.
        use_ssl: 是否使用SSL.
    """

    def __init__(
        self,
        host: str = "",
        port: int = DEFAULT_IMAP_PORT,
        username: str = "",
        password: str = "",
        use_ssl: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "use_ssl": self.use_ssl,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IMAPAccount":
        """从字典反序列化."""
        return cls(
            host=data.get("host", ""),
            port=data.get("port", DEFAULT_IMAP_PORT),
            username=data.get("username", ""),
            password=data.get("password", ""),
            use_ssl=data.get("use_ssl", True),
        )


class Config:
    """MailForge 全局配置管理器.

    管理SMTP/IMAP账户配置、默认发送参数、模板目录等。
    支持从配置文件和环境变量加载，环境变量优先级最高。

    Usage:
        config = Config()
        config.load()
        account = config.get_smtp_account("default")
    """

    ENV_PREFIX = "MAILFORGE_"

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """初始化配置管理器.

        Args:
            config_dir: 自定义配置目录路径，默认为 ~/.mailforge.
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / CONFIG_DIR_NAME
        self.config_file = self.config_dir / CONFIG_FILE_NAME
        self.smtp_accounts: Dict[str, SMTPAccount] = {}
        self.imap_account: Optional[IMAPAccount] = None
        self.default_account: str = "default"
        self.send_rate_limit: int = DEFAULT_SEND_RATE_LIMIT
        self.hourly_limit: int = DEFAULT_HOURLY_LIMIT
        self.retry_max: int = DEFAULT_RETRY_MAX
        self.retry_delay: float = DEFAULT_RETRY_DELAY
        self.connection_timeout: int = DEFAULT_CONNECTION_TIMEOUT
        self.template_dir: str = ""
        self.contact_dir: str = ""
        self.log_level: str = "INFO"

    @property
    def env_overrides(self) -> Dict[str, str]:
        """获取所有MAILFORGE_前缀的环境变量."""
        overrides: Dict[str, str] = {}
        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                config_key = key[len(self.ENV_PREFIX):].lower()
                overrides[config_key] = value
        return overrides

    def load(self) -> None:
        """从配置文件加载配置，并应用环境变量覆盖."""
        if not self.config_file.exists():
            logger.debug("配置文件不存在: %s", self.config_file)
            self._apply_env_overrides()
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("加载配置文件失败: %s", e)
            self._apply_env_overrides()
            return

        self._parse_config(data)
        self._apply_env_overrides()
        logger.info("配置已从 %s 加载", self.config_file)

    def save(self) -> None:
        """保存当前配置到文件."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = self._to_dict()
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("配置已保存到 %s", self.config_file)
        except OSError as e:
            raise ConfigError(f"保存配置文件失败: {e}") from e

    def init_default(self) -> None:
        """初始化默认配置目录和文件."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir = str(self.config_dir / "templates")
        self.contact_dir = str(self.config_dir / "contacts")
        Path(self.template_dir).mkdir(parents=True, exist_ok=True)
        Path(self.contact_dir).mkdir(parents=True, exist_ok=True)
        self.save()
        logger.info("默认配置已初始化到 %s", self.config_dir)

    def _parse_config(self, data: Dict[str, Any]) -> None:
        """解析配置字典."""
        # SMTP账户
        smtp_data = data.get("smtp_accounts", {})
        for name, account_data in smtp_data.items():
            self.smtp_accounts[name] = SMTPAccount.from_dict(account_data)

        # IMAP账户
        imap_data = data.get("imap", {})
        if imap_data:
            self.imap_account = IMAPAccount.from_dict(imap_data)

        # 默认账户
        self.default_account = data.get("default_account", "default")

        # 发送参数
        self.send_rate_limit = data.get("send_rate_limit", DEFAULT_SEND_RATE_LIMIT)
        self.hourly_limit = data.get("hourly_limit", DEFAULT_HOURLY_LIMIT)
        self.retry_max = data.get("retry_max", DEFAULT_RETRY_MAX)
        self.retry_delay = data.get("retry_delay", DEFAULT_RETRY_DELAY)
        self.connection_timeout = data.get("connection_timeout", DEFAULT_CONNECTION_TIMEOUT)

        # 路径
        self.template_dir = data.get("template_dir", "")
        self.contact_dir = data.get("contact_dir", "")
        self.log_level = data.get("log_level", "INFO")

    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖."""
        env = self.env_overrides

        if "smtp_host" in env:
            self._ensure_smtp_account().host = env["smtp_host"]
        if "smtp_port" in env:
            self._ensure_smtp_account().port = int(env["smtp_port"])
        if "smtp_username" in env:
            self._ensure_smtp_account().username = env["smtp_username"]
        if "smtp_password" in env:
            self._ensure_smtp_account().password = env["smtp_password"]
        if "smtp_use_ssl" in env:
            self._ensure_smtp_account().use_ssl = env["smtp_use_ssl"].lower() in ("true", "1", "yes")
        if "smtp_use_tls" in env:
            self._ensure_smtp_account().use_tls = env["smtp_use_tls"].lower() in ("true", "1", "yes")
        if "smtp_from_name" in env:
            self._ensure_smtp_account().from_name = env["smtp_from_name"]
        if "smtp_from_email" in env:
            self._ensure_smtp_account().from_email = env["smtp_from_email"]

        if "imap_host" in env:
            if not self.imap_account:
                self.imap_account = IMAPAccount()
            self.imap_account.host = env["imap_host"]
        if "imap_port" in env:
            if not self.imap_account:
                self.imap_account = IMAPAccount()
            self.imap_account.port = int(env["imap_port"])
        if "imap_username" in env:
            if not self.imap_account:
                self.imap_account = IMAPAccount()
            self.imap_account.username = env["imap_username"]
        if "imap_password" in env:
            if not self.imap_account:
                self.imap_account = IMAPAccount()
            self.imap_account.password = env["imap_password"]

        if "send_rate_limit" in env:
            self.send_rate_limit = int(env["send_rate_limit"])
        if "hourly_limit" in env:
            self.hourly_limit = int(env["hourly_limit"])
        if "log_level" in env:
            self.log_level = env["log_level"]

    def _ensure_smtp_account(self) -> SMTPAccount:
        """确保默认SMTP账户存在."""
        if self.default_account not in self.smtp_accounts:
            self.smtp_accounts[self.default_account] = SMTPAccount(name=self.default_account)
        return self.smtp_accounts[self.default_account]

    def get_smtp_account(self, name: Optional[str] = None) -> Optional[SMTPAccount]:
        """获取指定SMTP账户配置.

        Args:
            name: 账户名称，默认使用default_account.

        Returns:
            SMTPAccount实例，不存在则返回None.
        """
        account_name = name or self.default_account
        return self.smtp_accounts.get(account_name)

    def add_smtp_account(self, account: SMTPAccount) -> None:
        """添加或更新SMTP账户.

        Args:
            account: SMTPAccount实例.
        """
        self.smtp_accounts[account.name] = account
        logger.info("SMTP账户 '%s' 已添加", account.name)

    def remove_smtp_account(self, name: str) -> None:
        """删除SMTP账户.

        Args:
            name: 账户名称.

        Raises:
            ConfigError: 账户不存在时抛出.
        """
        if name not in self.smtp_accounts:
            raise ConfigError(f"SMTP账户 '{name}' 不存在")
        del self.smtp_accounts[name]
        logger.info("SMTP账户 '%s' 已删除", name)

    def set(self, key: str, value: Any) -> None:
        """设置配置项.

        Args:
            key: 配置键（支持点号分隔，如 smtp.host）.
            value: 配置值.
        """
        parts = key.split(".")
        if len(parts) == 1:
            if hasattr(self, parts[0]):
                setattr(self, parts[0], value)
            else:
                raise ConfigError(f"未知配置项: {key}")
        elif len(parts) == 2 and parts[0] == "smtp":
            account = self._ensure_smtp_account()
            if hasattr(account, parts[1]):
                setattr(account, parts[1], value)
            else:
                raise ConfigError(f"未知SMTP配置项: {parts[1]}")
        elif len(parts) == 3 and parts[0] == "smtp":
            account_name = parts[1]
            if account_name not in self.smtp_accounts:
                self.smtp_accounts[account_name] = SMTPAccount(name=account_name)
            if hasattr(self.smtp_accounts[account_name], parts[2]):
                setattr(self.smtp_accounts[account_name], parts[2], value)
            else:
                raise ConfigError(f"未知SMTP配置项: {parts[2]}")
        else:
            raise ConfigError(f"不支持的配置键格式: {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项.

        Args:
            key: 配置键.
            default: 默认值.

        Returns:
            配置值.
        """
        parts = key.split(".")
        if len(parts) == 1:
            return getattr(self, parts[0], default)
        elif len(parts) == 2 and parts[0] == "smtp":
            account = self._ensure_smtp_account()
            return getattr(account, parts[1], default)
        return default

    def list_all(self) -> Dict[str, Any]:
        """列出所有配置项.

        Returns:
            包含所有配置的字典.
        """
        result: Dict[str, Any] = {
            "default_account": self.default_account,
            "send_rate_limit": self.send_rate_limit,
            "hourly_limit": self.hourly_limit,
            "retry_max": self.retry_max,
            "retry_delay": self.retry_delay,
            "connection_timeout": self.connection_timeout,
            "template_dir": self.template_dir,
            "contact_dir": self.contact_dir,
            "log_level": self.log_level,
            "smtp_accounts": {
                name: account.to_dict()
                for name, account in self.smtp_accounts.items()
            },
        }
        if self.imap_account:
            result["imap"] = self.imap_account.to_dict()
        return result

    def _to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于保存）."""
        return self.list_all()
