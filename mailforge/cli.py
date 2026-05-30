"""CLI入口模块 - argparse命令定义.

定义MailForge-CLI的所有命令行接口，包括配置管理、联系人管理、
模板管理、营销活动管理、邮件发送、收件箱查看、分析统计、TUI仪表盘等。
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mailforge import __version__

logger = logging.getLogger(__name__)

# 配置日志
def _setup_logging(verbose: bool = False) -> None:
    """配置日志级别.

    Args:
        verbose: 是否启用详细日志.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_parser() -> argparse.ArgumentParser:
    """创建CLI参数解析器.

    Returns:
        argparse.ArgumentParser实例.
    """
    parser = argparse.ArgumentParser(
        prog="mailforge",
        description="MailForge-CLI - 轻量级终端邮件营销智能引擎",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="启用详细日志")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init 命令
    subparsers.add_parser("init", help="初始化配置")

    # config 命令
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_sub = config_parser.add_subparsers(dest="config_command")

    config_set = config_sub.add_parser("set", help="设置配置项")
    config_set.add_argument("key", help="配置键")
    config_set.add_argument("value", help="配置值")

    config_sub.add_parser("list", help="列出所有配置")

    # contact 命令
    contact_parser = subparsers.add_parser("contact", help="联系人管理")
    contact_sub = contact_parser.add_subparsers(dest="contact_command")

    contact_import = contact_sub.add_parser("import", help="导入联系人")
    contact_import.add_argument("file", help="文件路径（CSV或JSON）")
    contact_import.add_argument("--group", default="default", help="导入到的分组")
    contact_import.add_argument("--email-column", help="邮箱列名")
    contact_import.add_argument("--name-column", help="姓名列名")

    contact_sub.add_parser("list", help="列出联系人")
    contact_sub.add_parser("groups", help="列出分组")

    contact_export = contact_sub.add_parser("export", help="导出联系人")
    contact_export.add_argument("file", help="输出文件路径")
    contact_export.add_argument("--format", choices=["csv", "json"], default="csv", help="导出格式")
    contact_export.add_argument("--group", help="按分组过滤")

    contact_group = contact_sub.add_parser("group", help="分组管理")
    contact_group_sub = contact_group.add_subparsers(dest="group_command")
    contact_group_create = contact_group_sub.add_parser("create", help="创建分组")
    contact_group_create.add_argument("name", help="分组名称")
    contact_group_delete = contact_group_sub.add_parser("delete", help="删除分组")
    contact_group_delete.add_argument("name", help="分组名称")
    contact_group_delete.add_argument("--remove-contacts", action="store_true", help="同时删除联系人")

    contact_dedup = contact_sub.add_parser("dedup", help="去重")

    # template 命令
    template_parser = subparsers.add_parser("template", help="模板管理")
    template_sub = template_parser.add_subparsers(dest="template_command")

    template_sub.add_parser("list", help="列出模板")

    template_create = template_sub.add_parser("create", help="创建模板")
    template_create.add_argument("name", help="模板名称")
    template_create.add_argument("--content", help="模板内容")
    template_create.add_argument("--file", help="从文件读取模板内容")

    template_preview = template_sub.add_parser("preview", help="预览模板渲染")
    template_preview.add_argument("name", help="模板名称")
    template_preview.add_argument("--var", action="append", help="模板变量（格式: key=value）")

    # campaign 命令
    campaign_parser = subparsers.add_parser("campaign", help="营销活动管理")
    campaign_sub = campaign_parser.add_subparsers(dest="campaign_command")

    campaign_create = campaign_sub.add_parser("create", help="创建营销活动")
    campaign_create.add_argument("name", help="活动名称")
    campaign_create.add_argument("--template", help="模板名称")
    campaign_create.add_argument("--group", default="default", help="目标联系人分组")
    campaign_create.add_argument("--subject", help="邮件主题")
    campaign_create.add_argument("--schedule", help="计划发送时间（ISO格式）")

    campaign_sub.add_parser("list", help="列出活动")

    campaign_start = campaign_sub.add_parser("start", help="启动活动")
    campaign_start.add_argument("id", help="活动ID")

    campaign_pause = campaign_sub.add_parser("pause", help="暂停活动")
    campaign_pause.add_argument("id", help="活动ID")

    campaign_cancel = campaign_sub.add_parser("cancel", help="取消活动")
    campaign_cancel.add_argument("id", help="活动ID")

    campaign_report = campaign_sub.add_parser("report", help="查看活动报告")
    campaign_report.add_argument("id", help="活动ID")
    campaign_report.add_argument("--format", choices=["json", "text"], default="text", help="报告格式")

    # send 命令
    send_parser = subparsers.add_parser("send", help="发送邮件")
    send_parser.add_argument("--to", help="收件人邮箱")
    send_parser.add_argument("--subject", help="邮件主题")
    send_parser.add_argument("--body", help="邮件正文")
    send_parser.add_argument("--html", help="HTML正文")
    send_parser.add_argument("--file", help="从文件读取正文")
    send_parser.add_argument("--template", help="使用模板")
    send_parser.add_argument("--group", help="发送到联系人分组")
    send_parser.add_argument("--cc", help="抄送（逗号分隔）")
    send_parser.add_argument("--bcc", help="密送（逗号分隔）")
    send_parser.add_argument("--attach", help="附件路径（逗号分隔）")
    send_parser.add_argument("--reply-to", help="回复地址")
    send_parser.add_argument("--dry-run", action="store_true", help="试运行（不实际发送）")

    # inbox 命令
    inbox_parser = subparsers.add_parser("inbox", help="查看收件箱")
    inbox_sub = inbox_parser.add_subparsers(dest="inbox_command")

    inbox_sub.add_parser("list", help="列出邮件")
    inbox_sub.add_parser("unread", help="列出未读邮件")

    inbox_search = inbox_sub.add_parser("search", help="搜索邮件")
    inbox_search.add_argument("query", help="搜索关键词")

    inbox_bounces = inbox_sub.add_parser("bounces", help="查看退信")

    # analytics 命令
    analytics_parser = subparsers.add_parser("analytics", help="发送统计")
    analytics_parser.add_argument("--export", help="导出报告（JSON/CSV/Markdown文件路径）")
    analytics_parser.add_argument("--format", choices=["json", "csv", "markdown"], default="text", help="报告格式")
    analytics_parser.add_argument("--interval", choices=["hour", "day", "week"], default="hour", help="时间间隔")

    # dashboard 命令
    subparsers.add_parser("dashboard", help="打开TUI仪表盘")

    # version 命令
    subparsers.add_parser("version", help="版本信息")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI主入口.

    Args:
        argv: 命令行参数列表.

    Returns:
        退出码.
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    _setup_logging(getattr(args, "verbose", False))

    if not args.command:
        parser.print_help()
        return 0

    try:
        handler = CommandHandler(args)
        return handler.dispatch()
    except KeyboardInterrupt:
        print("\n操作已取消")
        return 130
    except Exception as e:
        logger.error("命令执行失败: %s", e, exc_info=True)
        print(f"错误: {e}", file=sys.stderr)
        return 1


class CommandHandler:
    """命令处理器.

    根据解析后的参数执行对应的命令逻辑。
    """

    def __init__(self, args: argparse.Namespace) -> None:
        """初始化命令处理器.

        Args:
            args: 解析后的命令行参数.
        """
        self.args = args

    def dispatch(self) -> int:
        """分发命令到对应的处理方法.

        Returns:
            退出码.
        """
        command = self.args.command

        dispatch_map = {
            "init": self._cmd_init,
            "config": self._cmd_config,
            "contact": self._cmd_contact,
            "template": self._cmd_template,
            "campaign": self._cmd_campaign,
            "send": self._cmd_send,
            "inbox": self._cmd_inbox,
            "analytics": self._cmd_analytics,
            "dashboard": self._cmd_dashboard,
            "version": self._cmd_version,
        }

        handler = dispatch_map.get(command)
        if handler:
            return handler()
        else:
            print(f"未知命令: {command}")
            return 1

    def _cmd_init(self) -> int:
        """初始化配置."""
        from mailforge.core.config import Config

        config = Config()
        config.init_default()
        print("MailForge 配置已初始化")
        print(f"  配置目录: {config.config_dir}")
        print(f"  模板目录: {config.template_dir}")
        print(f"  联系人目录: {config.contact_dir}")
        print()
        print("下一步:")
        print("  1. 编辑配置文件设置SMTP账户信息:")
        print(f"     {config.config_file}")
        print("  2. 或使用环境变量:")
        print("     MAILFORGE_SMTP_HOST, MAILFORGE_SMTP_PORT, ...")
        return 0

    def _cmd_config(self) -> int:
        """配置管理."""
        from mailforge.core.config import Config

        config = Config()
        config.load()

        sub_cmd = getattr(self.args, "config_command", None)

        if sub_cmd == "set":
            key = self.args.key
            value = self.args.value
            # 尝试转换为合适的类型
            try:
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                else:
                    value = int(value)
            except (ValueError, AttributeError):
                pass

            config.set(key, value)
            config.save()
            print(f"配置已更新: {key} = {value}")
            return 0

        elif sub_cmd == "list":
            all_config = config.list_all()
            print(json.dumps(all_config, indent=2, ensure_ascii=False))
            return 0

        else:
            print("请指定子命令: set, list")
            return 1

    def _cmd_contact(self) -> int:
        """联系人管理."""
        from mailforge.core.config import Config
        from mailforge.core.contact import ContactManager
        from mailforge.utils.formatters import print_table_to_stdout

        config = Config()
        config.load()
        manager = ContactManager(storage_dir=config.contact_dir)
        manager.load()

        sub_cmd = getattr(self.args, "contact_command", None)

        if sub_cmd == "import":
            file_path = self.args.file
            group = self.args.group

            if file_path.endswith(".json"):
                success, fail, errors = manager.import_json(
                    file_path, group=group,
                )
            else:
                success, fail, errors = manager.import_csv(
                    file_path,
                    group=group,
                    email_column=self.args.email_column,
                    name_column=self.args.name_column,
                )

            print(f"导入完成: 成功={success}, 失败={fail}")
            if errors:
                print("错误详情:")
                for err in errors[:10]:
                    print(f"  - {err}")
                if len(errors) > 10:
                    print(f"  ... 还有 {len(errors) - 10} 个错误")

            manager.save()
            return 0

        elif sub_cmd == "list":
            contacts = manager.list_contacts(limit=100)
            if not contacts:
                print("暂无联系人")
                return 0

            headers = ["邮箱", "姓名", "分组"]
            rows = [
                [c.email, c.name or "-", c.group]
                for c in contacts
            ]
            print_table_to_stdout(headers, rows, title=f"联系人列表 (共{manager.total_count}个)")
            return 0

        elif sub_cmd == "groups":
            groups = manager.groups
            if not groups:
                print("暂无分组")
                return 0

            headers = ["分组名称", "联系人数量"]
            rows = [[g, str(manager.get_group_count(g))] for g in groups]
            print_table_to_stdout(headers, rows, title="分组列表")
            return 0

        elif sub_cmd == "export":
            file_path = self.args.file
            fmt = self.args.format
            group = self.args.group

            if fmt == "json":
                count = manager.export_json(file_path, group=group)
            else:
                count = manager.export_csv(file_path, group=group)

            print(f"已导出 {count} 个联系人到 {file_path}")
            return 0

        elif sub_cmd == "group":
            group_cmd = getattr(self.args, "group_command", None)
            if group_cmd == "create":
                ok, msg = manager.create_group(self.args.name)
                print(msg)
                manager.save()
                return 0 if ok else 1
            elif group_cmd == "delete":
                ok, msg = manager.delete_group(
                    self.args.name,
                    remove_contacts=self.args.remove_contacts,
                )
                print(msg)
                manager.save()
                return 0 if ok else 1
            else:
                print("请指定子命令: create, delete")
                return 1

        elif sub_cmd == "dedup":
            count = manager.deduplicate()
            print(f"已删除 {count} 个重复联系人")
            manager.save()
            return 0

        else:
            print("请指定子命令: import, list, groups, export, group, dedup")
            return 1

    def _cmd_template(self) -> int:
        """模板管理."""
        from mailforge.core.config import Config
        from mailforge.core.template import TemplateEngine, create_template

        config = Config()
        config.load()

        sub_cmd = getattr(self.args, "template_command", None)

        if sub_cmd == "list":
            engine = TemplateEngine(template_dir=config.template_dir)
            templates = engine.list_templates()
            if not templates:
                print("暂无模板")
                return 0

            print("模板列表:")
            for tpl in templates:
                print(f"  - {tpl}")
            return 0

        elif sub_cmd == "create":
            name = self.args.name
            content = self.args.content

            if self.args.file:
                try:
                    with open(self.args.file, "r", encoding="utf-8") as f:
                        content = f.read()
                except OSError as e:
                    print(f"读取文件失败: {e}", file=sys.stderr)
                    return 1

            if not content:
                print("请提供模板内容（--content 或 --file）", file=sys.stderr)
                return 1

            if not config.template_dir:
                config.init_default()

            path = create_template(name, content, config.template_dir)
            print(f"模板已创建: {path}")
            return 0

        elif sub_cmd == "preview":
            name = self.args.name
            engine = TemplateEngine(template_dir=config.template_dir)

            try:
                template_str = engine.render_file(name)
            except Exception as e:
                print(f"加载模板失败: {e}", file=sys.stderr)
                return 1

            # 解析变量
            context: Dict[str, Any] = {}
            if self.args.var:
                for var in self.args.var:
                    if "=" in var:
                        key, value = var.split("=", 1)
                        context[key] = value

            preview = engine.preview(template_str, context)
            print(f"模板预览: {name}")
            print("-" * 40)
            print(preview)
            return 0

        else:
            print("请指定子命令: list, create, preview")
            return 1

    def _cmd_campaign(self) -> int:
        """营销活动管理."""
        from mailforge.core.config import Config
        from mailforge.core.campaign import CampaignManager
        from mailforge.utils.formatters import print_table_to_stdout

        config = Config()
        config.load()
        manager = CampaignManager(storage_dir=config.contact_dir)
        manager.load()

        sub_cmd = getattr(self.args, "campaign_command", None)

        if sub_cmd == "create":
            campaign = manager.create(
                name=self.args.name,
                template_name=self.args.template or "",
                group_name=self.args.group,
                subject=self.args.subject or "",
                schedule_time=self.args.schedule,
            )
            print(f"营销活动已创建:")
            print(f"  ID: {campaign.id}")
            print(f"  名称: {campaign.name}")
            print(f"  状态: {campaign.status.value}")
            print(f"  分组: {campaign.group_name}")
            manager.save()
            return 0

        elif sub_cmd == "list":
            campaigns = manager.list_campaigns()
            if not campaigns:
                print("暂无营销活动")
                return 0

            headers = ["ID", "名称", "模板", "分组", "状态", "进度"]
            rows = [
                [
                    c.id,
                    c.name,
                    c.template_name or "-",
                    c.group_name,
                    c.status.value,
                    f"{c.progress:.1f}%",
                ]
                for c in campaigns
            ]
            print_table_to_stdout(headers, rows, title="营销活动列表")
            return 0

        elif sub_cmd == "start":
            try:
                manager.start(self.args.id)
                print(f"活动已启动: {self.args.id}")
                manager.save()
                return 0
            except Exception as e:
                print(f"启动失败: {e}", file=sys.stderr)
                return 1

        elif sub_cmd == "pause":
            try:
                manager.pause(self.args.id)
                print(f"活动已暂停: {self.args.id}")
                manager.save()
                return 0
            except Exception as e:
                print(f"暂停失败: {e}", file=sys.stderr)
                return 1

        elif sub_cmd == "cancel":
            try:
                manager.cancel(self.args.id)
                print(f"活动已取消: {self.args.id}")
                manager.save()
                return 0
            except Exception as e:
                print(f"取消失败: {e}", file=sys.stderr)
                return 1

        elif sub_cmd == "report":
            try:
                report = manager.generate_report(self.args.id)
                if self.args.format == "json":
                    print(json.dumps(report, indent=2, ensure_ascii=False))
                else:
                    campaign = report["campaign"]
                    print(f"活动报告: {campaign['name']} (ID={campaign['id']})")
                    print("-" * 40)
                    print(f"  状态: {campaign['status']}")
                    print(f"  总收件人: {campaign['total_recipients']}")
                    print(f"  已发送: {campaign['sent_count']}")
                    print(f"  成功: {campaign['success_count']}")
                    print(f"  失败: {campaign['fail_count']}")
                    print(f"  成功率: {campaign['success_rate']}%")
                    print(f"  耗时: {report['duration_seconds']}秒")
                    print(f"  平均速率: {report['average_rate']}封/秒")
                    if report["error_summary"]:
                        print("  错误统计:")
                        for error, count in report["error_summary"].items():
                            print(f"    - {error}: {count}")
                return 0
            except Exception as e:
                print(f"生成报告失败: {e}", file=sys.stderr)
                return 1

        else:
            print("请指定子命令: create, list, start, pause, cancel, report")
            return 1

    def _cmd_send(self) -> int:
        """发送邮件."""
        from mailforge.core.config import Config
        from mailforge.core.mailer import Mailer
        from mailforge.core.contact import ContactManager
        from mailforge.core.template import TemplateEngine
        from mailforge.utils.formatters import ProgressBar
        from mailforge.utils.validators import validate_email

        config = Config()
        config.load()

        account = config.get_smtp_account()
        if not account or not account.host:
            print("错误: 未配置SMTP账户", file=sys.stderr)
            print("请先运行 'mailforge init' 并配置SMTP信息", file=sys.stderr)
            return 1

        # 获取正文
        body = self.args.body or ""
        html_body = self.args.html or ""

        if self.args.file:
            try:
                with open(self.args.file, "r", encoding="utf-8") as f:
                    content = f.read()
                if self.args.file.endswith(".html") or self.args.file.endswith(".htm"):
                    html_body = content
                else:
                    body = content
            except OSError as e:
                print(f"读取文件失败: {e}", file=sys.stderr)
                return 1

        # 模板模式
        if self.args.template:
            engine = TemplateEngine(template_dir=config.template_dir)
            try:
                template_content = engine.render_file(self.args.template)
                html_body = template_content
            except Exception as e:
                print(f"加载模板失败: {e}", file=sys.stderr)
                return 1

        # 解析附件
        attachments = []
        if self.args.attach:
            attachments = [a.strip() for a in self.args.attach.split(",")]

        # 解析抄送/密送
        cc = [c.strip() for c in self.args.cc.split(",")] if self.args.cc else None
        bcc = [b.strip() for b in self.args.bcc.split(",")] if self.args.bcc else None

        # 试运行模式
        if self.args.dry_run:
            print("[试运行模式] 不会实际发送邮件")
            print(f"  收件人: {self.args.to or '(分组: ' + (self.args.group or 'default') + ')'}")
            print(f"  主题: {self.args.subject or '(无)'}")
            print(f"  正文长度: {len(body)} 字符")
            print(f"  HTML长度: {len(html_body)} 字符")
            if attachments:
                print(f"  附件: {', '.join(attachments)}")
            return 0

        # 分组发送模式
        if self.args.group:
            manager = ContactManager(storage_dir=config.contact_dir)
            manager.load()
            contacts = manager.list_contacts(group=self.args.group)

            if not contacts:
                print(f"分组 '{self.args.group}' 中没有联系人", file=sys.stderr)
                return 1

            print(f"准备发送 {len(contacts)} 封邮件到分组 '{self.args.group}'")

            rate_limiter = None
            mailer = Mailer(
                account,
                rate_limiter=rate_limiter,
                retry_max=config.retry_max,
                retry_delay=config.retry_delay,
                timeout=config.connection_timeout,
            )

            recipients = [
                {"email": c.email, "name": c.name}
                for c in contacts
            ]

            progress = ProgressBar(total=len(recipients), description="发送中")

            def on_progress(idx: int, total: int, result: Any) -> None:
                progress.update(1)
                if not result.success:
                    print(f"\n  发送失败: {result.email} - {result.error}")

            try:
                results = mailer.send_batch(
                    recipients=recipients,
                    subject=self.args.subject or "",
                    html_body=html_body,
                    text_body=body,
                    attachments=attachments,
                    progress_callback=on_progress,
                )
                progress.finish()

                success = sum(1 for r in results if r.success)
                fail = sum(1 for r in results if not r.success)
                print(f"\n发送完成: 成功={success}, 失败={fail}")
                mailer.close()
                return 0
            except Exception as e:
                progress.finish()
                print(f"发送失败: {e}", file=sys.stderr)
                mailer.close()
                return 1

        # 单封发送模式
        if not self.args.to:
            print("错误: 请指定收件人 (--to) 或分组 (--group)", file=sys.stderr)
            return 1

        valid, msg = validate_email(self.args.to)
        if not valid:
            print(f"错误: 收件人邮箱无效 - {msg}", file=sys.stderr)
            return 1

        if not body and not html_body:
            print("错误: 请提供邮件正文 (--body, --html, --file, 或 --template)", file=sys.stderr)
            return 1

        print(f"发送邮件到: {self.args.to}")

        mailer = Mailer(
            account,
            retry_max=config.retry_max,
            retry_delay=config.retry_delay,
            timeout=config.connection_timeout,
        )

        try:
            result = mailer.send(
                to=self.args.to,
                subject=self.args.subject or "",
                html_body=html_body,
                text_body=body,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                reply_to=self.args.reply_to,
            )

            if result.success:
                print(f"发送成功! Message-ID: {result.message_id}")
                return 0
            else:
                print(f"发送失败: {result.error}", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"发送失败: {e}", file=sys.stderr)
            return 1
        finally:
            mailer.close()

    def _cmd_inbox(self) -> int:
        """查看收件箱."""
        from mailforge.core.config import Config
        from mailforge.core.receiver import Receiver
        from mailforge.utils.formatters import print_table_to_stdout

        config = Config()
        config.load()

        if not config.imap_account or not config.imap_account.host:
            print("错误: 未配置IMAP账户", file=sys.stderr)
            print("请在配置文件中设置 imap.host, imap.username, imap.password", file=sys.stderr)
            return 1

        receiver = Receiver(config.imap_account, timeout=config.connection_timeout)

        try:
            receiver.connect()
        except Exception as e:
            print(f"IMAP连接失败: {e}", file=sys.stderr)
            return 1

        try:
            sub_cmd = getattr(self.args, "inbox_command", None) or "list"

            if sub_cmd == "list":
                messages = receiver.search("ALL", limit=20)
            elif sub_cmd == "unread":
                messages = receiver.search_unread(limit=20)
            elif sub_cmd == "search":
                query = self.args.query
                messages = receiver.search(f'SUBJECT "{query}"', limit=20)
            elif sub_cmd == "bounces":
                messages = receiver.search_bounces(limit=20)
            else:
                messages = receiver.search("ALL", limit=20)

            if not messages:
                print("没有找到邮件")
                return 0

            headers = ["UID", "发件人", "主题", "日期", "状态"]
            rows = [
                [
                    msg.uid[:8],
                    msg.from_addr[:30],
                    msg.subject[:40],
                    msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "-",
                    "退信" if msg.is_bounce else ("已读" if msg.is_read else "未读"),
                ]
                for msg in messages
            ]
            print_table_to_stdout(headers, rows, title=f"收件箱 ({len(messages)}封)")
            return 0

        finally:
            receiver.close()

    def _cmd_analytics(self) -> int:
        """发送统计."""
        from mailforge.core.config import Config
        from mailforge.core.analytics import Analytics
        from mailforge.tui.dashboard import Dashboard

        config = Config()
        config.load()

        analytics = Analytics(storage_dir=config.contact_dir)
        analytics.load()

        dashboard = Dashboard()

        if not analytics.records:
            print("暂无发送记录")
            return 0

        # 显示统计概览
        summary = analytics.get_summary()
        dashboard.show_stats(summary)

        # 分组统计
        group_stats = analytics.get_group_stats()
        if group_stats:
            dashboard.show_group_stats(group_stats)

        # 时间序列
        interval = getattr(self.args, "interval", "hour")
        series = analytics.get_time_series(interval=interval)
        if series:
            dashboard.show_time_series(series)

        # 导出
        export_path = getattr(self.args, "export", None)
        if export_path:
            fmt = getattr(self.args, "format", "text")
            if fmt == "json" or export_path.endswith(".json"):
                analytics.export_json(export_path)
            elif fmt == "csv" or export_path.endswith(".csv"):
                analytics.export_csv(export_path)
            else:
                analytics.export_markdown(export_path)
            print(f"报告已导出到: {export_path}")

        return 0

    def _cmd_dashboard(self) -> int:
        """打开TUI仪表盘."""
        from mailforge.core.config import Config
        from mailforge.core.analytics import Analytics
        from mailforge.core.campaign import CampaignManager
        from mailforge.core.contact import ContactManager
        from mailforge.tui.dashboard import Dashboard

        config = Config()
        config.load()

        analytics = Analytics(storage_dir=config.contact_dir)
        analytics.load()

        campaign_mgr = CampaignManager(storage_dir=config.contact_dir)
        campaign_mgr.load()

        contact_mgr = ContactManager(storage_dir=config.contact_dir)
        contact_mgr.load()

        dashboard = Dashboard()

        def get_stats() -> Dict[str, Any]:
            return analytics.get_summary()

        def get_campaigns() -> List[Dict[str, Any]]:
            return [c.to_dict() for c in campaign_mgr.list_campaigns()]

        def get_contacts() -> Dict[str, Any]:
            groups = {g: contact_mgr.get_group_count(g) for g in contact_mgr.groups}
            return {"total": contact_mgr.total_count, "groups": groups}

        dashboard.run_interactive(
            get_stats_func=get_stats,
            get_campaigns_func=get_campaigns,
            get_contacts_func=get_contacts,
        )
        return 0

    def _cmd_version(self) -> int:
        """版本信息."""
        from mailforge import __version__

        print(f"MailForge-CLI v{__version__}")
        print("轻量级终端邮件营销智能引擎")

        # 检查可选依赖
        try:
            import rich  # noqa: F401
            print("  rich: 已安装")
        except ImportError:
            print("  rich: 未安装 (TUI仪表盘将使用纯文本模式)")

        try:
            import textual  # noqa: F401
            print("  textual: 已安装")
        except ImportError:
            print("  textual: 未安装")

        return 0


if __name__ == "__main__":
    sys.exit(main())
