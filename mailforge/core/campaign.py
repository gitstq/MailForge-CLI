"""营销活动管理模块 - 创建、调度、状态跟踪、暂停/恢复/取消.

支持创建营销活动（名称、模板、联系人组、调度）、活动状态跟踪
（draft/sending/paused/completed/failed）、发送进度追踪、
暂停/恢复/取消、活动报告生成。
"""

import json
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CampaignError(Exception):
    """营销活动相关错误."""


class CampaignStatus(str, Enum):
    """营销活动状态枚举."""

    DRAFT = "draft"
    SENDING = "sending"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Campaign:
    """单个营销活动.

    Attributes:
        id: 活动唯一ID.
        name: 活动名称.
        template_name: 使用的模板名称.
        group_name: 目标联系人分组.
        subject: 邮件主题.
        status: 活动状态.
        created_at: 创建时间.
        started_at: 开始发送时间.
        completed_at: 完成时间.
        total_recipients: 总收件人数.
        sent_count: 已发送数.
        success_count: 成功数.
        fail_count: 失败数.
        results: 发送结果列表.
        schedule_time: 计划发送时间.
        attachments: 附件列表.
        extra_headers: 自定义邮件头.
    """

    def __init__(
        self,
        name: str,
        template_name: str = "",
        group_name: str = "default",
        subject: str = "",
        campaign_id: Optional[str] = None,
    ) -> None:
        """初始化营销活动.

        Args:
            name: 活动名称.
            template_name: 模板名称.
            group_name: 目标联系人分组.
            subject: 邮件主题.
            campaign_id: 活动ID（为空则自动生成）.
        """
        self.id: str = campaign_id or str(uuid.uuid4())[:8]
        self.name = name
        self.template_name = template_name
        self.group_name = group_name
        self.subject = subject
        self.status: CampaignStatus = CampaignStatus.DRAFT
        self.created_at: float = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.total_recipients: int = 0
        self.sent_count: int = 0
        self.success_count: int = 0
        self.fail_count: int = 0
        self.results: List[Dict[str, Any]] = []
        self.schedule_time: Optional[str] = None
        self.attachments: List[str] = []
        self.extra_headers: Dict[str, str] = {}

    @property
    def progress(self) -> float:
        """发送进度百分比."""
        if self.total_recipients <= 0:
            return 0.0
        return (self.sent_count / self.total_recipients) * 100

    @property
    def success_rate(self) -> float:
        """发送成功率."""
        if self.sent_count <= 0:
            return 0.0
        return (self.success_count / self.sent_count) * 100

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "id": self.id,
            "name": self.name,
            "template_name": self.template_name,
            "group_name": self.group_name,
            "subject": self.subject,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_recipients": self.total_recipients,
            "sent_count": self.sent_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "progress": round(self.progress, 1),
            "success_rate": round(self.success_rate, 1),
            "schedule_time": self.schedule_time,
            "attachments": self.attachments,
            "extra_headers": self.extra_headers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Campaign":
        """从字典反序列化."""
        campaign = cls(
            name=data.get("name", ""),
            template_name=data.get("template_name", ""),
            group_name=data.get("group_name", "default"),
            subject=data.get("subject", ""),
            campaign_id=data.get("id"),
        )
        campaign.status = CampaignStatus(data.get("status", "draft"))
        campaign.created_at = data.get("created_at", time.time())
        campaign.started_at = data.get("started_at")
        campaign.completed_at = data.get("completed_at")
        campaign.total_recipients = data.get("total_recipients", 0)
        campaign.sent_count = data.get("sent_count", 0)
        campaign.success_count = data.get("success_count", 0)
        campaign.fail_count = data.get("fail_count", 0)
        campaign.schedule_time = data.get("schedule_time")
        campaign.attachments = data.get("attachments", [])
        campaign.extra_headers = data.get("extra_headers", {})
        return campaign


class CampaignManager:
    """营销活动管理器.

    管理多个营销活动的创建、调度、状态跟踪。

    Usage:
        manager = CampaignManager()
        campaign = manager.create("春季促销", template="promo.html", group="vip")
        manager.start(campaign.id)
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        """初始化活动管理器.

        Args:
            storage_dir: 数据存储目录.
        """
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.campaigns: Dict[str, Campaign] = {}
        self._on_send_callbacks: Dict[str, Callable] = {}

    def create(
        self,
        name: str,
        template_name: str = "",
        group_name: str = "default",
        subject: str = "",
        schedule_time: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Campaign:
        """创建营销活动.

        Args:
            name: 活动名称.
            template_name: 模板名称.
            group_name: 目标联系人分组.
            subject: 邮件主题.
            schedule_time: 计划发送时间（ISO格式）.
            attachments: 附件列表.
            extra_headers: 自定义邮件头.

        Returns:
            创建的Campaign实例.
        """
        campaign = Campaign(
            name=name,
            template_name=template_name,
            group_name=group_name,
            subject=subject,
        )
        if schedule_time:
            campaign.schedule_time = schedule_time
        if attachments:
            campaign.attachments = attachments
        if extra_headers:
            campaign.extra_headers = extra_headers

        self.campaigns[campaign.id] = campaign
        logger.info("营销活动已创建: %s (ID=%s)", name, campaign.id)
        return campaign

    def get(self, campaign_id: str) -> Optional[Campaign]:
        """获取营销活动.

        Args:
            campaign_id: 活动ID.

        Returns:
            Campaign实例或None.
        """
        return self.campaigns.get(campaign_id)

    def list_campaigns(
        self,
        status: Optional[CampaignStatus] = None,
    ) -> List[Campaign]:
        """列出营销活动.

        Args:
            status: 按状态过滤.

        Returns:
            Campaign列表.
        """
        campaigns = list(self.campaigns.values())
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        return sorted(campaigns, key=lambda c: c.created_at, reverse=True)

    def start(self, campaign_id: str) -> bool:
        """启动营销活动.

        Args:
            campaign_id: 活动ID.

        Returns:
            是否成功启动.

        Raises:
            CampaignError: 活动不存在或状态不允许启动时抛出.
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise CampaignError(f"活动不存在: {campaign_id}")

        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.PAUSED):
            raise CampaignError(
                f"活动状态不允许启动: {campaign.status.value} "
                f"(需要 draft 或 paused)"
            )

        campaign.status = CampaignStatus.SENDING
        campaign.started_at = time.time()
        logger.info("营销活动已启动: %s (ID=%s)", campaign.name, campaign.id)
        return True

    def pause(self, campaign_id: str) -> bool:
        """暂停营销活动.

        Args:
            campaign_id: 活动ID.

        Returns:
            是否成功暂停.

        Raises:
            CampaignError: 活动不存在或状态不允许暂停时抛出.
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise CampaignError(f"活动不存在: {campaign_id}")

        if campaign.status != CampaignStatus.SENDING:
            raise CampaignError(
                f"活动状态不允许暂停: {campaign.status.value} "
                f"(需要 sending)"
            )

        campaign.status = CampaignStatus.PAUSED
        logger.info("营销活动已暂停: %s (ID=%s)", campaign.name, campaign.id)
        return True

    def resume(self, campaign_id: str) -> bool:
        """恢复营销活动.

        Args:
            campaign_id: 活动ID.

        Returns:
            是否成功恢复.
        """
        return self.start(campaign_id)

    def cancel(self, campaign_id: str) -> bool:
        """取消营销活动.

        Args:
            campaign_id: 活动ID.

        Returns:
            是否成功取消.

        Raises:
            CampaignError: 活动不存在或状态不允许取消时抛出.
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise CampaignError(f"活动不存在: {campaign_id}")

        if campaign.status == CampaignStatus.COMPLETED:
            raise CampaignError("已完成的活动无法取消")

        campaign.status = CampaignStatus.DRAFT
        campaign.started_at = None
        campaign.sent_count = 0
        campaign.success_count = 0
        campaign.fail_count = 0
        campaign.results.clear()
        logger.info("营销活动已取消: %s (ID=%s)", campaign.name, campaign.id)
        return True

    def complete(self, campaign_id: str) -> bool:
        """标记活动为已完成.

        Args:
            campaign_id: 活动ID.

        Returns:
            是否成功.
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return False

        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = time.time()
        logger.info("营销活动已完成: %s (ID=%s)", campaign.name, campaign.id)
        return True

    def fail(self, campaign_id: str, reason: str = "") -> bool:
        """标记活动为失败.

        Args:
            campaign_id: 活动ID.
            reason: 失败原因.

        Returns:
            是否成功.
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return False

        campaign.status = CampaignStatus.FAILED
        campaign.completed_at = time.time()
        logger.error("营销活动失败: %s (ID=%s), 原因: %s", campaign.name, campaign.id, reason)
        return True

    def record_send(self, campaign_id: str, result: Dict[str, Any]) -> None:
        """记录一次发送结果.

        Args:
            campaign_id: 活动ID.
            result: 发送结果字典.
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return

        campaign.sent_count += 1
        campaign.results.append(result)

        if result.get("success"):
            campaign.success_count += 1
        else:
            campaign.fail_count += 1

        # 检查是否全部发送完成
        if campaign.sent_count >= campaign.total_recipients and campaign.total_recipients > 0:
            self.complete(campaign_id)

    def delete(self, campaign_id: str) -> bool:
        """删除营销活动.

        Args:
            campaign_id: 活动ID.

        Returns:
            是否成功删除.
        """
        if campaign_id not in self.campaigns:
            return False

        del self.campaigns[campaign_id]
        logger.info("营销活动已删除: ID=%s", campaign_id)
        return True

    def generate_report(self, campaign_id: str) -> Dict[str, Any]:
        """生成活动报告.

        Args:
            campaign_id: 活动ID.

        Returns:
            报告字典.

        Raises:
            CampaignError: 活动不存在时抛出.
        """
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise CampaignError(f"活动不存在: {campaign_id}")

        # 统计失败原因
        error_summary: Dict[str, int] = {}
        for result in campaign.results:
            if not result.get("success"):
                error = result.get("error", "unknown")
                error_summary[error] = error_summary.get(error, 0) + 1

        # 时间统计
        duration = 0.0
        if campaign.started_at:
            end_time = campaign.completed_at or time.time()
            duration = end_time - campaign.started_at

        avg_rate = 0.0
        if duration > 0 and campaign.sent_count > 0:
            avg_rate = campaign.sent_count / duration

        return {
            "campaign": campaign.to_dict(),
            "error_summary": error_summary,
            "duration_seconds": round(duration, 1),
            "average_rate": round(avg_rate, 2),
            "generated_at": datetime.now().isoformat(),
        }

    def save(self, file_path: Optional[str] = None) -> None:
        """保存活动数据到文件.

        Args:
            file_path: 文件路径.
        """
        if file_path is None:
            if not self.storage_dir:
                raise CampaignError("未设置存储目录")
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(self.storage_dir / "campaigns.json")

        data = {
            cid: c.to_dict()
            for cid, c in self.campaigns.items()
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("活动数据已保存到 %s", file_path)
        except OSError as e:
            raise CampaignError(f"保存活动数据失败: {e}") from e

    def load(self, file_path: Optional[str] = None) -> None:
        """从文件加载活动数据.

        Args:
            file_path: 文件路径.
        """
        if file_path is None:
            if not self.storage_dir:
                return
            file_path = str(self.storage_dir / "campaigns.json")

        path = Path(file_path)
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                for cid, cdata in data.items():
                    campaign = Campaign.from_dict(cdata)
                    self.campaigns[campaign.id] = campaign

            logger.info("已从 %s 加载 %d 个活动", file_path, len(self.campaigns))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("加载活动数据失败: %s", e)
