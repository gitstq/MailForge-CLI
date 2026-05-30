"""输出格式化模块 - 表格、进度条、彩色输出、JSON美化.

提供终端友好的输出格式化工具，支持彩色输出（rich可用时自动启用）。
"""

import json
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


# ANSI 颜色代码
class Colors:
    """ANSI 终端颜色代码."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def supports_color() -> bool:
    """检测终端是否支持彩色输出.

    Returns:
        是否支持ANSI颜色.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            return kernel32.GetConsoleMode(kernel32.GetStdHandle(-11)) & 0x0004 != 0
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# 全局颜色开关
_color_enabled = supports_color()


def enable_color(enabled: bool = True) -> None:
    """启用或禁用彩色输出.

    Args:
        enabled: 是否启用彩色输出.
    """
    global _color_enabled
    _color_enabled = enabled and supports_color()


def colorize(text: str, color: str) -> str:
    """为文本添加颜色.

    Args:
        text: 原始文本.
        color: 颜色代码（如 Colors.RED）.

    Returns:
        带颜色代码的文本.
    """
    if not _color_enabled:
        return text
    return f"{color}{text}{Colors.RESET}"


def style(text: str, bold: bool = False, dim: bool = False) -> str:
    """应用文本样式.

    Args:
        text: 原始文本.
        bold: 是否加粗.
        dim: 是否变暗.

    Returns:
        带样式的文本.
    """
    if not _color_enabled:
        return text
    result = text
    if bold:
        result = f"{Colors.BOLD}{result}"
    if dim:
        result = f"{Colors.DIM}{result}"
    return f"{result}{Colors.RESET}"


# 状态图标
STATUS_ICONS = {
    "success": ("[OK]", Colors.GREEN),
    "error": ("[FAIL]", Colors.RED),
    "warning": ("[WARN]", Colors.YELLOW),
    "info": ("[INFO]", Colors.BLUE),
    "pending": ("[...]", Colors.DIM),
    "running": ("[>>>]", Colors.CYAN),
    "paused": ("[|||]", Colors.YELLOW),
    "draft": ("[DFT]", Colors.DIM),
}


def status_icon(status: str) -> str:
    """获取状态图标.

    Args:
        status: 状态名称.

    Returns:
        带颜色的状态图标.
    """
    icon, color = STATUS_ICONS.get(status, ("[???]", Colors.WHITE))
    return colorize(icon, color)


def print_status(status: str, message: str) -> None:
    """打印状态消息.

    Args:
        status: 状态名称.
        message: 消息内容.
    """
    print(f"  {status_icon(status)} {message}")


def print_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    title: Optional[str] = None,
    max_col_width: int = 50,
) -> str:
    """格式化输出表格.

    Args:
        headers: 表头列表.
        rows: 数据行列表.
        title: 可选标题.
        max_col_width: 列最大宽度.

    Returns:
        格式化后的表格字符串.
    """
    lines: List[str] = []

    if title:
        lines.append(colorize(title, Colors.BOLD))
        lines.append("")

    # 计算列宽
    col_count = len(headers)
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row):
            if i < col_count:
                col_widths[i] = max(col_widths[i], min(len(str(cell)), max_col_width))

    # 截断列宽
    col_widths = [min(w, max_col_width) for w in col_widths]

    def format_row(cells: Sequence[str], is_header: bool = False) -> str:
        parts: List[str] = []
        for i, cell in enumerate(cells):
            text = str(cell)
            if len(text) > col_widths[i]:
                text = text[:col_widths[i] - 3] + "..."
            if is_header:
                text = colorize(text, Colors.BOLD)
            parts.append(text.ljust(col_widths[i]))
        return " | ".join(parts)

    # 分隔线
    separator = "-+-".join("-" * w for w in col_widths)

    # 构建表格
    lines.append(format_row(headers, is_header=True))
    lines.append(separator)

    for row in rows:
        cells = list(row) + [""] * (col_count - len(row))
        lines.append(format_row(cells[:col_count]))

    return "\n".join(lines)


def print_table_to_stdout(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    title: Optional[str] = None,
    max_col_width: int = 50,
) -> None:
    """打印表格到标准输出.

    Args:
        headers: 表头列表.
        rows: 数据行列表.
        title: 可选标题.
        max_col_width: 列最大宽度.
    """
    output = print_table(headers, rows, title, max_col_width)
    print(output)


class ProgressBar:
    """终端进度条.

    在终端显示进度条，支持百分比、计数、速度估算。

    Attributes:
        total: 总任务数.
        width: 进度条宽度（字符数）.
    """

    def __init__(self, total: int, width: int = 40, description: str = "") -> None:
        """初始化进度条.

        Args:
            total: 总任务数.
            width: 进度条字符宽度.
            description: 进度条描述文本.
        """
        self.total = total
        self.width = width
        self.description = description
        self.current = 0
        self.start_time = time.time()
        self._last_print_len = 0

    def update(self, n: int = 1) -> None:
        """更新进度.

        Args:
            n: 增加的进度数.
        """
        self.current = min(self.current + n, self.total)
        self._render()

    def set_progress(self, current: int) -> None:
        """直接设置当前进度.

        Args:
            current: 当前进度.
        """
        self.current = min(current, self.total)
        self._render()

    def _render(self) -> None:
        """渲染进度条."""
        if self.total <= 0:
            return

        percent = self.current / self.total
        filled = int(self.width * percent)
        empty = self.width - filled

        # 进度条字符
        if _color_enabled:
            bar = (
                colorize("[" + "=" * filled, Colors.GREEN)
                + colorize("-" * empty + "]", Colors.DIM)
            )
        else:
            bar = "[" + "=" * filled + "-" * empty + "]"

        # 速度估算
        elapsed = time.time() - self.start_time
        if elapsed > 0 and self.current > 0:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            speed_info = f"{rate:.1f}/s | ETA: {remaining:.0f}s"
        else:
            speed_info = ""

        # 组合输出
        desc = f"{self.description} " if self.description else ""
        line = f"\r{desc}{bar} {self.current}/{self.total} ({percent:.1%}) {speed_info}"

        # 清除之前的输出
        clear = "\b" * self._last_print_len
        sys.stdout.write(clear + line)
        sys.stdout.flush()
        self._last_print_len = len(line)

    def finish(self) -> None:
        """完成进度条，换行."""
        self._render()
        print()
        self._last_print_len = 0

    def __enter__(self) -> "ProgressBar":
        """支持上下文管理器."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """退出上下文时完成进度条."""
        self.finish()


def format_json(data: Any, indent: int = 2) -> str:
    """美化JSON输出.

    Args:
        data: JSON数据.
        indent: 缩进空格数.

    Returns:
        格式化后的JSON字符串.
    """
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def format_size(size_bytes: int) -> str:
    """格式化文件大小.

    Args:
        size_bytes: 字节数.

    Returns:
        人类可读的大小字符串.
    """
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_number(number: int) -> str:
    """格式化数字（千位分隔符）.

    Args:
        number: 数字.

    Returns:
        带千位分隔符的字符串.
    """
    return f"{number:,}"


def format_duration(seconds: float) -> str:
    """格式化时长.

    Args:
        seconds: 秒数.

    Returns:
        人类可读的时长字符串.
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
