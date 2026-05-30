"""TUI仪表盘模块 - 发送统计、实时状态、联系人概览.

使用rich库（可选依赖）构建终端仪表盘，提供发送统计概览、
实时发送进度、联系人分组概览、活动列表与状态、键盘快捷键导航。
当rich不可用时自动降级到纯文本模式。
"""

import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 检查rich是否可用
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.columns import Columns
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class DashboardError(Exception):
    """仪表盘相关错误."""


class Dashboard:
    """TUI仪表盘.

    提供终端友好的交互式仪表盘，展示发送统计、活动状态、联系人概览等。
    当rich库可用时使用富文本渲染，否则降级到纯文本模式。

    Usage:
        dashboard = Dashboard()
        dashboard.show_stats(summary_data)
        dashboard.show_campaigns(campaign_list)
    """

    def __init__(self) -> None:
        """初始化仪表盘."""
        self._console = Console() if RICH_AVAILABLE else None

    @property
    def is_rich_available(self) -> bool:
        """rich库是否可用."""
        return RICH_AVAILABLE

    def clear(self) -> None:
        """清屏."""
        os.system("cls" if sys.platform == "win32" else "clear")

    def show_banner(self) -> None:
        """显示应用横幅."""
        if RICH_AVAILABLE and self._console:
            self._console.print(
                Panel(
                    Text(
                        "  MailForge-CLI  ",
                        style="bold cyan",
                        justify="center",
                    ),
                    subtitle="v1.0.0 | 轻量级终端邮件营销智能引擎",
                    box=box.DOUBLE,
                    border_style="cyan",
                )
            )
        else:
            print("=" * 50)
            print("  MailForge-CLI v1.0.0")
            print("  轻量级终端邮件营销智能引擎")
            print("=" * 50)
            print()

    def show_stats(self, summary: Dict[str, Any]) -> None:
        """显示发送统计概览.

        Args:
            summary: 统计摘要字典，包含 total, success, failed, bounces,
                     success_rate, bounce_rate 等字段.
        """
        if RICH_AVAILABLE and self._console:
            self._show_stats_rich(summary)
        else:
            self._show_stats_plain(summary)

    def _show_stats_rich(self, summary: Dict[str, Any]) -> None:
        """使用rich显示统计."""
        console = self._console
        assert console is not None

        table = Table(title="发送统计概览", box=box.ROUNDED, border_style="blue")
        table.add_column("指标", style="cyan", justify="left")
        table.add_column("数值", style="green", justify="right")

        table.add_row("总发送数", str(summary.get("total", 0)))
        table.add_row("成功数", str(summary.get("success", 0)))
        table.add_row("失败数", str(summary.get("failed", 0)))
        table.add_row("退信数", str(summary.get("bounces", 0)))
        table.add_row("成功率", f"{summary.get('success_rate', 0)}%")
        table.add_row("退信率", f"{summary.get('bounce_rate', 0)}%")

        console.print(table)

    def _show_stats_plain(self, summary: Dict[str, Any]) -> None:
        """纯文本显示统计."""
        print("发送统计概览")
        print("-" * 30)
        print(f"  总发送数: {summary.get('total', 0)}")
        print(f"  成功数:   {summary.get('success', 0)}")
        print(f"  失败数:   {summary.get('failed', 0)}")
        print(f"  退信数:   {summary.get('bounces', 0)}")
        print(f"  成功率:   {summary.get('success_rate', 0)}%")
        print(f"  退信率:   {summary.get('bounce_rate', 0)}%")
        print()

    def show_campaigns(self, campaigns: List[Dict[str, Any]]) -> None:
        """显示活动列表.

        Args:
            campaigns: 活动字典列表.
        """
        if not campaigns:
            print("  暂无营销活动")
            return

        if RICH_AVAILABLE and self._console:
            self._show_campaigns_rich(campaigns)
        else:
            self._show_campaigns_plain(campaigns)

    def _show_campaigns_rich(self, campaigns: List[Dict[str, Any]]) -> None:
        """使用rich显示活动列表."""
        console = self._console
        assert console is not None

        table = Table(title="营销活动列表", box=box.ROUNDED, border_style="yellow")
        table.add_column("ID", style="dim", justify="left")
        table.add_column("名称", style="white", justify="left")
        table.add_column("状态", justify="center")
        table.add_column("进度", justify="right")
        table.add_column("成功率", justify="right")

        status_styles = {
            "draft": "[dim]草稿[/dim]",
            "sending": "[green]发送中[/green]",
            "paused": "[yellow]已暂停[/yellow]",
            "completed": "[blue]已完成[/blue]",
            "failed": "[red]失败[/red]",
        }

        for campaign in campaigns:
            status = campaign.get("status", "draft")
            progress = campaign.get("progress", 0)
            success_rate = campaign.get("success_rate", 0)

            table.add_row(
                campaign.get("id", ""),
                campaign.get("name", ""),
                status_styles.get(status, status),
                f"{progress}%",
                f"{success_rate}%",
            )

        console.print(table)

    def _show_campaigns_plain(self, campaigns: List[Dict[str, Any]]) -> None:
        """纯文本显示活动列表."""
        print("营销活动列表")
        print("-" * 70)
        print(f"  {'ID':<10} {'名称':<20} {'状态':<10} {'进度':>8} {'成功率':>8}")
        print(f"  {'-'*10} {'-'*20} {'-'*10} {'-'*8} {'-'*8}")

        for campaign in campaigns:
            print(
                f"  {campaign.get('id', ''):<10} "
                f"{campaign.get('name', ''):<20} "
                f"{campaign.get('status', ''):<10} "
                f"{campaign.get('progress', 0):>7}% "
                f"{campaign.get('success_rate', 0):>7}%"
            )
        print()

    def show_contacts_overview(
        self,
        total: int,
        groups: Dict[str, int],
    ) -> None:
        """显示联系人概览.

        Args:
            total: 联系人总数.
            groups: {分组名: 数量} 字典.
        """
        if RICH_AVAILABLE and self._console:
            self._show_contacts_rich(total, groups)
        else:
            self._show_contacts_plain(total, groups)

    def _show_contacts_rich(self, total: int, groups: Dict[str, int]) -> None:
        """使用rich显示联系人概览."""
        console = self._console
        assert console is not None

        table = Table(title="联系人概览", box=box.ROUNDED, border_style="green")
        table.add_column("分组", style="white", justify="left")
        table.add_column("数量", style="green", justify="right")

        for group_name, count in groups.items():
            table.add_row(group_name, str(count))

        table.add_row("[bold]总计[/bold]", f"[bold]{total}[/bold]")
        console.print(table)

    def _show_contacts_plain(self, total: int, groups: Dict[str, int]) -> None:
        """纯文本显示联系人概览."""
        print("联系人概览")
        print("-" * 30)
        for group_name, count in groups.items():
            print(f"  {group_name}: {count}")
        print(f"  总计: {total}")
        print()

    def show_progress(
        self,
        current: int,
        total: int,
        description: str = "发送进度",
    ) -> None:
        """显示发送进度.

        Args:
            current: 当前进度.
            total: 总数.
            description: 描述文本.
        """
        if total <= 0:
            return

        percent = (current / total) * 100
        bar_width = 40
        filled = int(bar_width * current / total)
        empty = bar_width - filled

        bar = "[" + "=" * filled + "-" * empty + "]"
        print(f"\r  {description}: {bar} {current}/{total} ({percent:.1f}%)", end="", flush=True)

        if current >= total:
            print()

    def show_group_stats(self, group_stats: Dict[str, Dict[str, Any]]) -> None:
        """显示分组统计对比.

        Args:
            group_stats: 分组统计数据.
        """
        if not group_stats:
            print("  暂无分组统计数据")
            return

        if RICH_AVAILABLE and self._console:
            self._show_group_stats_rich(group_stats)
        else:
            self._show_group_stats_plain(group_stats)

    def _show_group_stats_rich(self, group_stats: Dict[str, Dict[str, Any]]) -> None:
        """使用rich显示分组统计."""
        console = self._console
        assert console is not None

        table = Table(title="分组统计对比", box=box.ROUNDED, border_style="magenta")
        table.add_column("分组", style="white", justify="left")
        table.add_column("总数", justify="right")
        table.add_column("成功", style="green", justify="right")
        table.add_column("失败", style="red", justify="right")
        table.add_column("退信", style="yellow", justify="right")
        table.add_column("成功率", justify="right")

        for group_name, stats in group_stats.items():
            table.add_row(
                group_name,
                str(stats.get("total", 0)),
                str(stats.get("success", 0)),
                str(stats.get("failed", 0)),
                str(stats.get("bounces", 0)),
                f"{stats.get('success_rate', 0)}%",
            )

        console.print(table)

    def _show_group_stats_plain(self, group_stats: Dict[str, Dict[str, Any]]) -> None:
        """纯文本显示分组统计."""
        print("分组统计对比")
        print("-" * 60)
        print(f"  {'分组':<15} {'总数':>6} {'成功':>6} {'失败':>6} {'退信':>6} {'成功率':>8}")
        print(f"  {'-'*15} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*8}")

        for group_name, stats in group_stats.items():
            print(
                f"  {group_name:<15} "
                f"{stats.get('total', 0):>6} "
                f"{stats.get('success', 0):>6} "
                f"{stats.get('failed', 0):>6} "
                f"{stats.get('bounces', 0):>6} "
                f"{stats.get('success_rate', 0):>7}%"
            )
        print()

    def show_time_series(self, series: List[Dict[str, Any]]) -> None:
        """显示时间序列数据.

        Args:
            series: 时间序列数据列表.
        """
        if not series:
            print("  暂无时间序列数据")
            return

        if RICH_AVAILABLE and self._console:
            self._show_time_series_rich(series)
        else:
            self._show_time_series_plain(series)

    def _show_time_series_rich(self, series: List[Dict[str, Any]]) -> None:
        """使用rich显示时间序列."""
        console = self._console
        assert console is not None

        table = Table(title="发送趋势", box=box.ROUNDED, border_style="cyan")
        table.add_column("时间段", style="white", justify="left")
        table.add_column("总数", justify="right")
        table.add_column("成功", style="green", justify="right")
        table.add_column("失败", style="red", justify="right")
        table.add_column("成功率", justify="right")

        for item in series:
            table.add_row(
                item.get("period", ""),
                str(item.get("total", 0)),
                str(item.get("success", 0)),
                str(item.get("failed", 0)),
                f"{item.get('success_rate', 0)}%",
            )

        console.print(table)

    def _show_time_series_plain(self, series: List[Dict[str, Any]]) -> None:
        """纯文本显示时间序列."""
        print("发送趋势")
        print("-" * 55)
        print(f"  {'时间段':<20} {'总数':>6} {'成功':>6} {'失败':>6} {'成功率':>8}")
        print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*6} {'-'*8}")

        for item in series:
            print(
                f"  {item.get('period', ''):<20} "
                f"{item.get('total', 0):>6} "
                f"{item.get('success', 0):>6} "
                f"{item.get('failed', 0):>6} "
                f"{item.get('success_rate', 0):>7}%"
            )
        print()

    def show_help(self) -> None:
        """显示帮助信息."""
        if RICH_AVAILABLE and self._console:
            console = self._console
            assert console is not None
            console.print(
                Panel(
                    "[bold]快捷键[/bold]\n\n"
                    "  [cyan]q[/cyan] - 退出仪表盘\n"
                    "  [cyan]r[/cyan] - 刷新数据\n"
                    "  [cyan]s[/cyan] - 发送统计\n"
                    "  [cyan]c[/cyan] - 活动列表\n"
                    "  [cyan]g[/cyan] - 分组概览\n"
                    "  [cyan]h[/cyan] - 帮助信息\n",
                    title="帮助",
                    border_style="blue",
                )
            )
        else:
            print("快捷键:")
            print("  q - 退出仪表盘")
            print("  r - 刷新数据")
            print("  s - 发送统计")
            print("  c - 活动列表")
            print("  g - 分组概览")
            print("  h - 帮助信息")
            print()

    def run_interactive(
        self,
        get_stats_func: Any = None,
        get_campaigns_func: Any = None,
        get_contacts_func: Any = None,
    ) -> None:
        """运行交互式仪表盘.

        Args:
            get_stats_func: 获取统计数据的回调函数.
            get_campaigns_func: 获取活动列表的回调函数.
            get_contacts_func: 获取联系人概览的回调函数.
        """
        if not sys.stdin.isatty():
            logger.warning("非交互式终端，无法启动交互式仪表盘")
            return

        self.clear()
        self.show_banner()
        self.show_help()

        print("  按 q 退出，h 查看帮助")
        print()

        try:
            while True:
                try:
                    key = input("  > ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    break

                if key == "q" or key == "quit":
                    break
                elif key == "h" or key == "help":
                    self.show_help()
                elif key == "r" or key == "refresh":
                    self.clear()
                    self.show_banner()
                    print("  数据已刷新")
                    print()
                elif key == "s" or key == "stats":
                    if get_stats_func:
                        stats = get_stats_func()
                        self.show_stats(stats)
                    else:
                        print("  统计数据不可用")
                elif key == "c" or key == "campaigns":
                    if get_campaigns_func:
                        campaigns = get_campaigns_func()
                        self.show_campaigns(campaigns)
                    else:
                        print("  活动数据不可用")
                elif key == "g" or key == "groups":
                    if get_contacts_func:
                        contacts = get_contacts_func()
                        self.show_contacts_overview(contacts.get("total", 0), contacts.get("groups", {}))
                    else:
                        print("  联系人数据不可用")
                elif key:
                    print(f"  未知命令: {key}，输入 h 查看帮助")

        except KeyboardInterrupt:
            pass

        print("\n  再见！")
