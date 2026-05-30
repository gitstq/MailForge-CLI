"""发送分析模块 - 成功率、退信统计、时间段分析、联系人组对比.

支持发送成功率统计、退信率统计、按时间段分析、联系人组对比、
导出报告（JSON/CSV/Markdown）等功能。
"""

import csv
import io
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalyticsError(Exception):
    """分析相关错误."""


class SendRecord:
    """单条发送记录.

    Attributes:
        email: 收件人邮箱.
        group: 联系人分组.
        campaign_id: 活动ID.
        success: 是否成功.
        error: 错误信息.
        timestamp: 发送时间戳.
        is_bounce: 是否为退信.
    """

    def __init__(
        self,
        email: str,
        success: bool,
        timestamp: Optional[float] = None,
        group: str = "",
        campaign_id: str = "",
        error: str = "",
        is_bounce: bool = False,
    ) -> None:
        """初始化发送记录.

        Args:
            email: 收件人邮箱.
            success: 是否成功.
            timestamp: 发送时间戳.
            group: 联系人分组.
            campaign_id: 活动ID.
            error: 错误信息.
            is_bounce: 是否为退信.
        """
        self.email = email
        self.success = success
        self.timestamp = timestamp or datetime.now().timestamp()
        self.group = group
        self.campaign_id = campaign_id
        self.error = error
        self.is_bounce = is_bounce

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "email": self.email,
            "success": self.success,
            "timestamp": self.timestamp,
            "group": self.group,
            "campaign_id": self.campaign_id,
            "error": self.error,
            "is_bounce": self.is_bounce,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SendRecord":
        """从字典创建."""
        return cls(
            email=data.get("email", ""),
            success=data.get("success", False),
            timestamp=data.get("timestamp"),
            group=data.get("group", ""),
            campaign_id=data.get("campaign_id", ""),
            error=data.get("error", ""),
            is_bounce=data.get("is_bounce", False),
        )


class Analytics:
    """发送分析引擎.

    分析发送记录，生成统计数据和报告。

    Usage:
        analytics = Analytics()
        analytics.add_record(SendRecord("user@example.com", True))
        stats = analytics.get_summary()
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        """初始化分析引擎.

        Args:
            storage_dir: 数据存储目录.
        """
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.records: List[SendRecord] = []

    def add_record(self, record: SendRecord) -> None:
        """添加发送记录.

        Args:
            record: SendRecord实例.
        """
        self.records.append(record)

    def add_records(self, records: List[SendRecord]) -> None:
        """批量添加发送记录.

        Args:
            records: SendRecord列表.
        """
        self.records.extend(records)

    def clear(self) -> None:
        """清除所有记录."""
        self.records.clear()

    @property
    def total_count(self) -> int:
        """总发送数."""
        return len(self.records)

    @property
    def success_count(self) -> int:
        """成功发送数."""
        return sum(1 for r in self.records if r.success)

    @property
    def fail_count(self) -> int:
        """失败发送数."""
        return sum(1 for r in self.records if not r.success)

    @property
    def bounce_count(self) -> int:
        """退信数."""
        return sum(1 for r in self.records if r.is_bounce)

    @property
    def success_rate(self) -> float:
        """发送成功率."""
        if not self.records:
            return 0.0
        return (self.success_count / self.total_count) * 100

    @property
    def bounce_rate(self) -> float:
        """退信率."""
        if not self.records:
            return 0.0
        return (self.bounce_count / self.total_count) * 100

    def get_summary(self) -> Dict[str, Any]:
        """获取发送统计概览.

        Returns:
            统计摘要字典.
        """
        return {
            "total": self.total_count,
            "success": self.success_count,
            "failed": self.fail_count,
            "bounces": self.bounce_count,
            "success_rate": round(self.success_rate, 2),
            "bounce_rate": round(self.bounce_rate, 2),
        }

    def get_error_summary(self) -> Dict[str, int]:
        """获取错误类型统计.

        Returns:
            {错误类型: 数量} 字典.
        """
        errors: Dict[str, int] = {}
        for record in self.records:
            if not record.success and record.error:
                errors[record.error] = errors.get(record.error, 0) + 1
        return dict(sorted(errors.items(), key=lambda x: x[1], reverse=True))

    def get_group_stats(self) -> Dict[str, Dict[str, Any]]:
        """按联系人分组统计.

        Returns:
            {分组名: 统计数据} 字典.
        """
        groups: Dict[str, List[SendRecord]] = {}
        for record in self.records:
            group = record.group or "default"
            if group not in groups:
                groups[group] = []
            groups[group].append(record)

        stats: Dict[str, Dict[str, Any]] = {}
        for group_name, group_records in groups.items():
            total = len(group_records)
            success = sum(1 for r in group_records if r.success)
            failed = sum(1 for r in group_records if not r.success)
            bounces = sum(1 for r in group_records if r.is_bounce)
            stats[group_name] = {
                "total": total,
                "success": success,
                "failed": failed,
                "bounces": bounces,
                "success_rate": round((success / total * 100) if total > 0 else 0, 2),
                "bounce_rate": round((bounces / total * 100) if total > 0 else 0, 2),
            }

        return stats

    def get_campaign_stats(self) -> Dict[str, Dict[str, Any]]:
        """按活动统计.

        Returns:
            {活动ID: 统计数据} 字典.
        """
        campaigns: Dict[str, List[SendRecord]] = {}
        for record in self.records:
            cid = record.campaign_id or "unknown"
            if cid not in campaigns:
                campaigns[cid] = []
            campaigns[cid].append(record)

        stats: Dict[str, Dict[str, Any]] = {}
        for cid, campaign_records in campaigns.items():
            total = len(campaign_records)
            success = sum(1 for r in campaign_records if r.success)
            failed = sum(1 for r in campaign_records if not r.success)
            bounces = sum(1 for r in campaign_records if r.is_bounce)
            stats[cid] = {
                "total": total,
                "success": success,
                "failed": failed,
                "bounces": bounces,
                "success_rate": round((success / total * 100) if total > 0 else 0, 2),
                "bounce_rate": round((bounces / total * 100) if total > 0 else 0, 2),
            }

        return stats

    def get_time_series(self, interval: str = "hour") -> List[Dict[str, Any]]:
        """按时间段分析.

        Args:
            interval: 时间间隔（hour/day/week）.

        Returns:
            时间序列数据列表.
        """
        if not self.records:
            return []

        # 按时间段分组
        time_buckets: Dict[str, List[SendRecord]] = {}

        for record in self.records:
            dt = datetime.fromtimestamp(record.timestamp)
            if interval == "hour":
                key = dt.strftime("%Y-%m-%d %H:00")
            elif interval == "day":
                key = dt.strftime("%Y-%m-%d")
            elif interval == "week":
                week_start = dt - timedelta(days=dt.weekday())
                key = week_start.strftime("%Y-%m-%d")
            else:
                key = dt.strftime("%Y-%m-%d %H:00")

            if key not in time_buckets:
                time_buckets[key] = []
            time_buckets[key].append(record)

        # 生成时间序列
        series: List[Dict[str, Any]] = []
        for key in sorted(time_buckets.keys()):
            bucket_records = time_buckets[key]
            total = len(bucket_records)
            success = sum(1 for r in bucket_records if r.success)
            failed = sum(1 for r in bucket_records if not r.success)
            series.append({
                "period": key,
                "total": total,
                "success": success,
                "failed": failed,
                "success_rate": round((success / total * 100) if total > 0 else 0, 2),
            })

        return series

    def get_top_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取失败最多的邮箱.

        Args:
            limit: 返回数量.

        Returns:
            失败邮箱列表.
        """
        failures: Dict[str, Dict[str, Any]] = {}
        for record in self.records:
            if not record.success:
                if record.email not in failures:
                    failures[record.email] = {
                        "email": record.email,
                        "count": 0,
                        "last_error": record.error,
                    }
                failures[record.email]["count"] += 1
                failures[record.email]["last_error"] = record.error

        sorted_failures = sorted(
            failures.values(),
            key=lambda x: x["count"],
            reverse=True,
        )
        return sorted_failures[:limit]

    def export_json(self, file_path: str) -> None:
        """导出分析报告为JSON.

        Args:
            file_path: 输出文件路径.

        Raises:
            AnalyticsError: 导出失败时抛出.
        """
        report = {
            "summary": self.get_summary(),
            "error_summary": self.get_error_summary(),
            "group_stats": self.get_group_stats(),
            "campaign_stats": self.get_campaign_stats(),
            "time_series": self.get_time_series(),
            "top_failures": self.get_top_failures(),
            "generated_at": datetime.now().isoformat(),
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info("分析报告已导出为JSON: %s", file_path)
        except OSError as e:
            raise AnalyticsError(f"导出JSON失败: {e}") from e

    def export_csv(self, file_path: str) -> None:
        """导出发送记录为CSV.

        Args:
            file_path: 输出文件路径.

        Raises:
            AnalyticsError: 导出失败时抛出.
        """
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "email", "success", "timestamp", "group",
                    "campaign_id", "error", "is_bounce",
                ])
                writer.writeheader()
                for record in self.records:
                    writer.writerow({
                        "email": record.email,
                        "success": record.success,
                        "timestamp": datetime.fromtimestamp(record.timestamp).isoformat(),
                        "group": record.group,
                        "campaign_id": record.campaign_id,
                        "error": record.error,
                        "is_bounce": record.is_bounce,
                    })
            logger.info("发送记录已导出为CSV: %s", file_path)
        except OSError as e:
            raise AnalyticsError(f"导出CSV失败: {e}") from e

    def export_markdown(self, file_path: str) -> None:
        """导出分析报告为Markdown.

        Args:
            file_path: 输出文件路径.

        Raises:
            AnalyticsError: 导出失败时抛出.
        """
        summary = self.get_summary()
        error_summary = self.get_error_summary()
        group_stats = self.get_group_stats()

        lines: List[str] = [
            "# MailForge 发送分析报告",
            "",
            f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 概览",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总发送数 | {summary['total']} |",
            f"| 成功数 | {summary['success']} |",
            f"| 失败数 | {summary['failed']} |",
            f"| 退信数 | {summary['bounces']} |",
            f"| 成功率 | {summary['success_rate']}% |",
            f"| 退信率 | {summary['bounce_rate']}% |",
            "",
        ]

        if error_summary:
            lines.extend([
                "## 错误统计",
                "",
                "| 错误类型 | 数量 |",
                "|----------|------|",
            ])
            for error, count in error_summary.items():
                lines.append(f"| {error} | {count} |")
            lines.append("")

        if group_stats:
            lines.extend([
                "## 分组统计",
                "",
                "| 分组 | 总数 | 成功 | 失败 | 退信 | 成功率 |",
                "|------|------|------|------|------|--------|",
            ])
            for group_name, stats in group_stats.items():
                lines.append(
                    f"| {group_name} | {stats['total']} | {stats['success']} | "
                    f"{stats['failed']} | {stats['bounces']} | {stats['success_rate']}% |"
                )
            lines.append("")

        report = "\n".join(lines)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info("分析报告已导出为Markdown: %s", file_path)
        except OSError as e:
            raise AnalyticsError(f"导出Markdown失败: {e}") from e

    def save(self, file_path: Optional[str] = None) -> None:
        """保存发送记录到文件.

        Args:
            file_path: 文件路径.
        """
        if file_path is None:
            if not self.storage_dir:
                return
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(self.storage_dir / "analytics.json")

        data = [r.to_dict() for r in self.records]
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("发送记录已保存到 %s", file_path)
        except OSError as e:
            raise AnalyticsError(f"保存发送记录失败: {e}") from e

    def load(self, file_path: Optional[str] = None) -> None:
        """从文件加载发送记录.

        Args:
            file_path: 文件路径.
        """
        if file_path is None:
            if not self.storage_dir:
                return
            file_path = str(self.storage_dir / "analytics.json")

        path = Path(file_path)
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        self.records.append(SendRecord.from_dict(item))

            logger.info("已从 %s 加载 %d 条发送记录", file_path, len(self.records))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("加载发送记录失败: %s", e)
