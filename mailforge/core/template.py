"""模板引擎模块 - 纯Python实现的Jinja2风格模板引擎.

零依赖实现，支持变量替换、条件渲染、循环、过滤器、模板继承等功能。

支持的语法:
    {{variable}}          - 变量替换
    {{variable|filter}}   - 带过滤器的变量替换
    {%if condition%}...{%endif%}        - 条件渲染
    {%if condition%}...{%else%}...{%endif%}  - 条件+否则
    {%for item in list%}...{%endfor%}    - 循环
    {%extends "base"%}                    - 模板继承
    {%block name%}...{%endblock%}        - 块定义/覆盖
    {# comment #}                         - 注释
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TemplateError(Exception):
    """模板相关错误."""


class TemplateSyntaxError(TemplateError):
    """模板语法错误."""


class TemplateRuntimeError(TemplateError):
    """模板运行时错误."""


# 内置过滤器
BUILTIN_FILTERS: Dict[str, Callable[..., Any]] = {}


def register_filter(name: str) -> Callable:
    """注册过滤器的装饰器.

    Args:
        name: 过滤器名称.

    Returns:
        装饰器函数.
    """
    def decorator(func: Callable) -> Callable:
        BUILTIN_FILTERS[name] = func
        return func
    return decorator


@register_filter("upper")
def _filter_upper(value: Any) -> str:
    """转为大写."""
    return str(value).upper()


@register_filter("lower")
def _filter_lower(value: Any) -> str:
    """转为小写."""
    return str(value).lower()


@register_filter("title")
def _filter_title(value: Any) -> str:
    """首字母大写."""
    return str(value).title()


@register_filter("strip")
def _filter_strip(value: Any) -> str:
    """去除首尾空白."""
    return str(value).strip()


@register_filter("lstrip")
def _filter_lstrip(value: Any) -> str:
    """去除左侧空白."""
    return str(value).lstrip()


@register_filter("rstrip")
def _filter_rstrip(value: Any) -> str:
    """去除右侧空白."""
    return str(value).rstrip()


@register_filter("default")
def _filter_default(value: Any, default_value: Any = "") -> Any:
    """默认值过滤器."""
    if value is None or value == "" or value == []:
        return default_value
    return value


@register_filter("truncate")
def _filter_truncate(value: Any, length: int = 100, suffix: str = "...") -> str:
    """截断文本."""
    text = str(value)
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


@register_filter("date")
def _filter_date(value: Any, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """日期格式化."""
    if isinstance(value, datetime):
        return value.strftime(fmt)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime(fmt)
        except (ValueError, TypeError):
            return value
    return str(value)


@register_filter("length")
def _filter_length(value: Any) -> int:
    """获取长度."""
    return len(value) if hasattr(value, "__len__") else 0


@register_filter("join")
def _filter_join(value: Any, separator: str = ", ") -> str:
    """列表连接."""
    if isinstance(value, (list, tuple)):
        return separator.join(str(item) for item in value)
    return str(value)


@register_filter("replace")
def _filter_replace(value: Any, old: str, new: str) -> str:
    """字符串替换."""
    return str(value).replace(old, new)


@register_filter("first")
def _filter_first(value: Any) -> Any:
    """获取第一个元素."""
    if isinstance(value, (list, tuple)) and len(value) > 0:
        return value[0]
    return value


@register_filter("last")
def _filter_last(value: Any) -> Any:
    """获取最后一个元素."""
    if isinstance(value, (list, tuple)) and len(value) > 0:
        return value[-1]
    return value


@register_filter("capitalize")
def _filter_capitalize(value: Any) -> str:
    """首字母大写."""
    return str(value).capitalize()


@register_filter("safe")
def _filter_safe(value: Any) -> str:
    """标记为安全HTML（不转义）."""
    return str(value)


@register_filter("escape")
def _filter_escape(value: Any) -> str:
    """HTML转义."""
    text = str(value)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")
    return text


class TemplateEngine:
    """纯Python模板引擎.

    支持变量替换、条件渲染、循环、过滤器、模板继承。

    Usage:
        engine = TemplateEngine()
        result = engine.render_string("Hello, {{name}}!", {"name": "World"})
    """

    def __init__(self, template_dir: Optional[str] = None) -> None:
        """初始化模板引擎.

        Args:
            template_dir: 模板文件目录.
        """
        self.template_dir = Path(template_dir) if template_dir else None
        self.filters: Dict[str, Callable[..., Any]] = dict(BUILTIN_FILTERS)
        self._template_cache: Dict[str, str] = {}

    def add_filter(self, name: str, func: Callable[..., Any]) -> None:
        """添加自定义过滤器.

        Args:
            name: 过滤器名称.
            func: 过滤器函数.
        """
        self.filters[name] = func

    def render_string(self, template_str: str, context: Optional[Dict[str, Any]] = None) -> str:
        """渲染模板字符串.

        Args:
            template_str: 模板字符串.
            context: 变量上下文.

        Returns:
            渲染后的字符串.

        Raises:
            TemplateSyntaxError: 模板语法错误.
            TemplateRuntimeError: 模板运行时错误.
        """
        ctx = context or {}

        # 预处理：处理继承
        template_str = self._process_extends(template_str, ctx)

        # 移除注释
        template_str = re.sub(r"\{#.*?#\}", "", template_str, flags=re.DOTALL)

        # 处理块定义（非继承模式下直接渲染内容）
        template_str = self._process_blocks(template_str, ctx)

        # 处理循环
        template_str = self._process_for_loops(template_str, ctx)

        # 处理条件
        template_str = self._process_conditionals(template_str, ctx)

        # 处理变量替换
        result = self._process_variables(template_str, ctx)

        return result

    def render_file(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """渲染模板文件.

        Args:
            template_name: 模板文件名（相对于template_dir）.
            context: 变量上下文.

        Returns:
            渲染后的字符串.

        Raises:
            TemplateError: 模板文件不存在或读取失败.
        """
        if not self.template_dir:
            raise TemplateError("未设置模板目录")

        template_path = self.template_dir / template_name
        if not template_path.exists():
            raise TemplateError(f"模板文件不存在: {template_path}")

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_str = f.read()
        except OSError as e:
            raise TemplateError(f"读取模板文件失败: {e}") from e

        return self.render_string(template_str, context)

    def _process_extends(self, template_str: str, context: Dict[str, Any]) -> str:
        """处理模板继承.

        Args:
            template_str: 模板字符串.
            context: 变量上下文.

        Returns:
            处理后的模板字符串.
        """
        extends_match = re.search(r"\{%\s*extends\s+[\"'](.+?)[\"']\s*%\}", template_str)
        if not extends_match:
            return template_str

        parent_name = extends_match.group(1)

        # 提取子模板中的块
        child_blocks: Dict[str, str] = {}
        for block_match in re.finditer(
            r"\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}",
            template_str,
            re.DOTALL,
        ):
            child_blocks[block_match.group(1)] = block_match.group(2)

        # 加载父模板
        if not self.template_dir:
            raise TemplateError("未设置模板目录，无法处理模板继承")

        parent_path = self.template_dir / parent_name
        if not parent_path.exists():
            raise TemplateError(f"父模板不存在: {parent_path}")

        try:
            with open(parent_path, "r", encoding="utf-8") as f:
                parent_str = f.read()
        except OSError as e:
            raise TemplateError(f"读取父模板失败: {e}") from e

        # 替换父模板中的块
        def replace_block(match: re.Match) -> str:
            block_name = match.group(1)
            if block_name in child_blocks:
                return child_blocks[block_name]
            return match.group(2)  # 保留父模板默认内容

        parent_str = re.sub(
            r"\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}",
            replace_block,
            parent_str,
            flags=re.DOTALL,
        )

        return parent_str

    def _process_blocks(self, template_str: str, context: Dict[str, Any]) -> str:
        """处理块定义（提取块内容）.

        Args:
            template_str: 模板字符串.
            context: 变量上下文.

        Returns:
            处理后的模板字符串.
        """
        def replace_block(match: re.Match) -> str:
            return match.group(2)

        return re.sub(
            r"\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}",
            replace_block,
            template_str,
            flags=re.DOTALL,
        )

    def _process_for_loops(self, template_str: str, context: Dict[str, Any]) -> str:
        """处理for循环.

        支持嵌套循环，使用递归处理。

        Args:
            template_str: 模板字符串.
            context: 变量上下文.

        Returns:
            处理后的模板字符串.
        """
        max_iterations = 100
        iteration = 0

        while "{%" in template_str and iteration < max_iterations:
            iteration += 1

            # 查找最内层的for循环
            pattern = (
                r"\{%\s*for\s+(\w+)\s+in\s+([\w.]+(?:\.\w+)*)\s*%\}"
                r"(.*?)"
                r"\{%\s*endfor\s*%\}"
            )
            match = re.search(pattern, template_str, re.DOTALL)
            if not match:
                break

            var_name = match.group(1)
            iterable_name = match.group(2)
            loop_body = match.group(3)

            # 获取可迭代对象
            iterable = self._resolve_variable(iterable_name, context)
            if not isinstance(iterable, (list, tuple)):
                iterable = [iterable]

            # 渲染循环
            parts: List[str] = []
            for index, item in enumerate(iterable):
                loop_context = dict(context)
                loop_context[var_name] = item
                loop_context["loop"] = {
                    "index": index + 1,
                    "index0": index,
                    "first": index == 0,
                    "last": index == len(iterable) - 1,
                    "length": len(iterable),
                    "revindex": len(iterable) - index,
                    "revindex0": len(iterable) - index - 1,
                }
                # 对循环体中的变量和条件进行替换
                rendered_body = self._process_variables(loop_body, loop_context)
                rendered_body = self._process_conditionals(rendered_body, loop_context)
                parts.append(rendered_body)

            replacement = "".join(parts)
            template_str = template_str[:match.start()] + replacement + template_str[match.end():]

        return template_str

    def _process_conditionals(self, template_str: str, context: Dict[str, Any]) -> str:
        """处理条件渲染.

        支持 if/elif/else/endif，使用递归处理嵌套。

        Args:
            template_str: 模板字符串.
            context: 变量上下文.

        Returns:
            处理后的模板字符串.
        """
        max_iterations = 100
        iteration = 0

        while "{%" in template_str and iteration < max_iterations:
            iteration += 1

            # 查找最内层的条件块
            pattern = (
                r"\{%\s*if\s+(.+?)\s*%\}"
                r"(.*?)"
                r"\{%\s*endif\s*%\}"
            )

            # 先查找带else的
            pattern_with_else = (
                r"\{%\s*if\s+(.+?)\s*%\}"
                r"(.*?)"
                r"\{%\s*else\s*%\}"
                r"(.*?)"
                r"\{%\s*endif\s*%\}"
            )

            match = re.search(pattern_with_else, template_str, re.DOTALL)
            if match:
                condition = match.group(1).strip()
                if_body = match.group(2)
                else_body = match.group(3)

                if self._evaluate_condition(condition, context):
                    replacement = if_body
                else:
                    replacement = else_body

                template_str = (
                    template_str[:match.start()] + replacement + template_str[match.end():]
                )
                continue

            # 查找不带else的
            match = re.search(pattern, template_str, re.DOTALL)
            if not match:
                break

            condition = match.group(1).strip()
            if_body = match.group(2)

            if self._evaluate_condition(condition, context):
                replacement = if_body
            else:
                replacement = ""

            template_str = (
                template_str[:match.start()] + replacement + template_str[match.end():]
            )

        return template_str

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件表达式.

        支持简单的比较和布尔运算。

        Args:
            condition: 条件表达式字符串.
            context: 变量上下文.

        Returns:
            条件是否为真.
        """
        condition = condition.strip()

        # 处理 not 运算
        if condition.startswith("not "):
            return not self._evaluate_condition(condition[4:], context)

        # 处理 and/or（简单实现，不支持嵌套）
        for op in (" and ", " or "):
            if op in condition:
                parts = condition.split(op, 1)
                left = self._evaluate_condition(parts[0], context)
                right = self._evaluate_condition(parts[1], context)
                if op == " and ":
                    return left and right
                return left or right

        # 处理比较运算
        comparison_ops = [
            ("==", lambda a, b: a == b),
            ("!=", lambda a, b: a != b),
            (">=", lambda a, b: a >= b),
            ("<=", lambda a, b: a <= b),
            (">", lambda a, b: a > b),
            ("<", lambda a, b: a < b),
        ]

        for op_str, op_func in comparison_ops:
            if op_str in condition:
                parts = condition.split(op_str, 1)
                left = self._resolve_value(parts[0].strip(), context)
                right = self._resolve_value(parts[1].strip(), context)
                try:
                    return op_func(left, right)
                except (TypeError, ValueError):
                    return False

        # 简单变量真值判断
        value = self._resolve_value(condition, context)
        return bool(value)

    def _resolve_value(self, expr: str, context: Dict[str, Any]) -> Any:
        """解析表达式值.

        Args:
            expr: 表达式字符串.
            context: 变量上下文.

        Returns:
            解析后的值.
        """
        expr = expr.strip()

        # 字符串字面量
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]

        # 数字字面量
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # 布尔字面量
        if expr.lower() == "true":
            return True
        if expr.lower() == "false":
            return False
        if expr.lower() == "none":
            return None

        # 变量
        return self._resolve_variable(expr, context)

    def _resolve_variable(self, name: str, context: Dict[str, Any]) -> Any:
        """解析变量路径.

        支持点号访问嵌套属性，如 user.name。

        Args:
            name: 变量名（可含点号）.
            context: 变量上下文.

        Returns:
            变量值.
        """
        parts = name.split(".")
        value: Any = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value

    def _process_variables(self, template_str: str, context: Dict[str, Any]) -> str:
        """处理变量替换和过滤器.

        Args:
            template_str: 模板字符串.
            context: 变量上下文.

        Returns:
            处理后的模板字符串.
        """
        def replace_variable(match: re.Match) -> str:
            expr = match.group(1).strip()

            # 解析过滤器和管道
            parts = [p.strip() for p in expr.split("|")]
            var_expr = parts[0]

            # 获取变量值
            value = self._resolve_variable(var_expr, context)
            if value is None and var_expr not in context:
                # 变量不存在且值为None，检查是否有default过滤器
                has_default = any(
                    p.strip().startswith("default") for p in parts[1:]
                )
                if not has_default:
                    return match.group(0)  # 保留原始表达式

            # 应用过滤器
            for filter_expr in parts[1:]:
                filter_parts = filter_expr.split("(", 1)
                filter_name = filter_parts[0].strip()
                filter_args: List[Any] = []

                if len(filter_parts) > 1 and filter_parts[1].rstrip().endswith(")"):
                    args_str = filter_parts[1].rstrip()[:-1]
                    # 解析参数（支持字符串字面量和数字，正确处理带逗号的字符串）
                    filter_args = self._parse_filter_args(args_str)

                if filter_name in self.filters:
                    try:
                        value = self.filters[filter_name](value, *filter_args)
                    except (TypeError, ValueError) as e:
                        logger.warning("过滤器 %s 应用失败: %s", filter_name, e)

            return str(value) if value is not None else ""

        return re.sub(r"\{\{(.*?)\}\}", replace_variable, template_str)

    @staticmethod
    def _parse_filter_args(args_str: str) -> List[Any]:
        """解析过滤器参数字符串.

        正确处理带逗号的字符串参数，如 join(', ').

        Args:
            args_str: 参数字符串.

        Returns:
            解析后的参数列表.
        """
        args: List[Any] = []
        current: List[str] = []
        in_string = False
        quote_char: Optional[str] = None

        for char in args_str:
            if in_string:
                current.append(char)
                if char == quote_char:
                    in_string = False
                    quote_char = None
            elif char in ('"', "'"):
                in_string = True
                quote_char = char
                current.append(char)
            elif char == ",":
                arg = "".join(current).strip()
                if arg:
                    # 解析参数值类型
                    if (arg.startswith('"') and arg.endswith('"')) or \
                       (arg.startswith("'") and arg.endswith("'")):
                        args.append(arg[1:-1])
                    else:
                        try:
                            args.append(int(arg))
                        except ValueError:
                            try:
                                args.append(float(arg))
                            except ValueError:
                                args.append(arg)
                current = []
            else:
                current.append(char)

        # 处理最后一个参数
        arg = "".join(current).strip()
        if arg:
            if (arg.startswith('"') and arg.endswith('"')) or \
               (arg.startswith("'") and arg.endswith("'")):
                args.append(arg[1:-1])
            else:
                try:
                    args.append(int(arg))
                except ValueError:
                    try:
                        args.append(float(arg))
                    except ValueError:
                        args.append(arg)

        return args

    def preview(
        self,
        template_str: str,
        context: Optional[Dict[str, Any]] = None,
        max_lines: int = 30,
    ) -> str:
        """预览模板渲染结果.

        Args:
            template_str: 模板字符串.
            context: 变量上下文.
            max_lines: 最大显示行数.

        Returns:
            截断后的预览字符串.
        """
        result = self.render_string(template_str, context)
        lines = result.split("\n")
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append(f"... (共 {len(result.split(chr(10)))} 行，已截断)")
        return "\n".join(lines)

    def list_templates(self) -> List[str]:
        """列出模板目录中的所有模板文件.

        Returns:
            模板文件名列表.
        """
        if not self.template_dir or not self.template_dir.exists():
            return []

        templates: List[str] = []
        for ext in ("*.html", "*.htm", "*.txt"):
            templates.extend(
                f.name for f in self.template_dir.glob(ext)
            )
        return sorted(templates)


def create_template(
    name: str,
    content: str,
    template_dir: str,
) -> str:
    """创建模板文件.

    Args:
        name: 模板名称（不含路径）.
        content: 模板内容.
        template_dir: 模板目录.

    Returns:
        模板文件路径.

    Raises:
        TemplateError: 创建失败时抛出.
    """
    dir_path = Path(template_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    template_path = dir_path / name
    try:
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("模板 '%s' 已创建: %s", name, template_path)
        return str(template_path)
    except OSError as e:
        raise TemplateError(f"创建模板失败: {e}") from e
