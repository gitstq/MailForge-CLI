"""模板引擎测试."""

import os
import tempfile
import unittest

from mailforge.core.template import TemplateEngine, TemplateError, create_template, BUILTIN_FILTERS


class TestTemplateEngine(unittest.TestCase):
    """TemplateEngine测试."""

    def setUp(self) -> None:
        """测试前准备."""
        self.engine = TemplateEngine()

    def test_variable_replacement(self) -> None:
        """测试变量替换."""
        result = self.engine.render_string("Hello, {{name}}!", {"name": "World"})
        self.assertEqual(result, "Hello, World!")

    def test_variable_not_found(self) -> None:
        """测试未找到变量时保留原始表达式."""
        result = self.engine.render_string("Hello, {{unknown}}!", {})
        self.assertEqual(result, "Hello, {{unknown}}!")

    def test_nested_variable(self) -> None:
        """测试嵌套变量."""
        result = self.engine.render_string(
            "{{user.name}}",
            {"user": {"name": "Alice"}},
        )
        self.assertEqual(result, "Alice")

    def test_filter_upper(self) -> None:
        """测试upper过滤器."""
        result = self.engine.render_string("{{name|upper}}", {"name": "hello"})
        self.assertEqual(result, "HELLO")

    def test_filter_lower(self) -> None:
        """测试lower过滤器."""
        result = self.engine.render_string("{{name|lower}}", {"name": "HELLO"})
        self.assertEqual(result, "hello")

    def test_filter_default(self) -> None:
        """测试default过滤器."""
        result = self.engine.render_string("{{name|default('Guest')}}", {})
        self.assertEqual(result, "Guest")

    def test_filter_truncate(self) -> None:
        """测试truncate过滤器."""
        result = self.engine.render_string(
            "{{text|truncate(10)}}",
            {"text": "This is a very long text"},
        )
        self.assertEqual(result, "This is...")

    def test_filter_strip(self) -> None:
        """测试strip过滤器."""
        result = self.engine.render_string("{{name|strip}}", {"name": "  hello  "})
        self.assertEqual(result, "hello")

    def test_filter_title(self) -> None:
        """测试title过滤器."""
        result = self.engine.render_string("{{name|title}}", {"name": "hello world"})
        self.assertEqual(result, "Hello World")

    def test_filter_length(self) -> None:
        """测试length过滤器."""
        result = self.engine.render_string("{{items|length}}", {"items": [1, 2, 3]})
        self.assertEqual(result, "3")

    def test_filter_join(self) -> None:
        """测试join过滤器."""
        result = self.engine.render_string(
            "{{items|join(', ')}}",
            {"items": ["a", "b", "c"]},
        )
        self.assertEqual(result, "a, b, c")

    def test_filter_replace(self) -> None:
        """测试replace过滤器."""
        result = self.engine.render_string(
            "{{text|replace('old', 'new')}}",
            {"text": "old world"},
        )
        self.assertEqual(result, "new world")

    def test_filter_first_last(self) -> None:
        """测试first/last过滤器."""
        result = self.engine.render_string(
            "{{items|first}}-{{items|last}}",
            {"items": [1, 2, 3]},
        )
        self.assertEqual(result, "1-3")

    def test_filter_escape(self) -> None:
        """测试escape过滤器."""
        result = self.engine.render_string(
            "{{text|escape}}",
            {"text": "<b>bold</b>"},
        )
        self.assertEqual(result, "&lt;b&gt;bold&lt;/b&gt;")

    def test_chained_filters(self) -> None:
        """测试链式过滤器."""
        result = self.engine.render_string(
            "{{name|strip|upper}}",
            {"name": "  hello  "},
        )
        self.assertEqual(result, "HELLO")

    def test_if_condition_true(self) -> None:
        """测试条件渲染 - 真."""
        template = "{%if show%}Visible{%endif%}"
        result = self.engine.render_string(template, {"show": True})
        self.assertEqual(result, "Visible")

    def test_if_condition_false(self) -> None:
        """测试条件渲染 - 假."""
        template = "{%if show%}Visible{%endif%}"
        result = self.engine.render_string(template, {"show": False})
        self.assertEqual(result, "")

    def test_if_else(self) -> None:
        """测试条件+否则."""
        template = "{%if show%}Yes{%else%}No{%endif%}"
        result = self.engine.render_string(template, {"show": False})
        self.assertEqual(result, "No")

    def test_if_with_comparison(self) -> None:
        """测试条件比较."""
        template = "{%if count > 5%}Many{%else%}Few{%endif%}"
        result = self.engine.render_string(template, {"count": 10})
        self.assertEqual(result, "Many")

    def test_if_with_string_equality(self) -> None:
        """测试字符串相等条件."""
        template = '{%if status == "active"%}Active{%else%}Inactive{%endif%}'
        result = self.engine.render_string(template, {"status": "active"})
        self.assertEqual(result, "Active")

    def test_for_loop(self) -> None:
        """测试循环."""
        template = "{%for item in items%}{{item}} {%endfor%}"
        result = self.engine.render_string(template, {"items": ["a", "b", "c"]})
        self.assertEqual(result, "a b c ")

    def test_for_loop_with_loop_var(self) -> None:
        """测试循环变量."""
        template = "{%for item in items%}{{loop.index}}:{{item}} {%endfor%}"
        result = self.engine.render_string(template, {"items": ["a", "b"]})
        self.assertEqual(result, "1:a 2:b ")

    def test_for_loop_first_last(self) -> None:
        """测试循环首尾标记."""
        template = "{%for item in items%}{%if loop.first%}[{%endif%}{{item}}{%if loop.last%}]{%endif%} {%endfor%}"
        result = self.engine.render_string(template, {"items": ["a", "b", "c"]})
        self.assertEqual(result, "[a b c] ")

    def test_comment_removal(self) -> None:
        """测试注释移除."""
        template = "Hello{# this is a comment #} World"
        result = self.engine.render_string(template, {})
        self.assertEqual(result, "Hello World")

    def test_complex_template(self) -> None:
        """测试复杂模板."""
        template = """
Hello, {{name|default('Guest')}}!
{%if items%}
Your items:
{%for item in items%}
- {{item}}
{%endfor%}
{%else%}
No items found.
{%endif%}
Total: {{count|default(0)}} items.
""".strip()
        result = self.engine.render_string(
            template,
            {"name": "Alice", "items": ["Apple", "Banana"], "count": 2},
        )
        self.assertIn("Hello, Alice!", result)
        self.assertIn("- Apple", result)
        self.assertIn("- Banana", result)
        self.assertIn("Total: 2 items.", result)

    def test_preview(self) -> None:
        """测试模板预览."""
        template = "Line 1\nLine 2\nLine 3"
        preview = self.engine.preview(template, {}, max_lines=2)
        lines = preview.split("\n")
        self.assertEqual(len(lines), 3)  # 2 lines + truncation notice


class TestTemplateFile(unittest.TestCase):
    """模板文件测试."""

    def test_create_template(self) -> None:
        """测试创建模板文件."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = create_template("test.html", "<h1>{{title}}</h1>", tmpdir)
            self.assertTrue(os.path.exists(path))

            engine = TemplateEngine(template_dir=tmpdir)
            result = engine.render_file("test.html", {"title": "Hello"})
            self.assertEqual(result, "<h1>Hello</h1>")

    def test_render_file_not_found(self) -> None:
        """测试渲染不存在的文件."""
        engine = TemplateEngine(template_dir="/nonexistent")
        with self.assertRaises(TemplateError):
            engine.render_file("missing.html")

    def test_list_templates(self) -> None:
        """测试列出模板."""
        with tempfile.TemporaryDirectory() as tmpdir:
            create_template("a.html", "", tmpdir)
            create_template("b.html", "", tmpdir)

            engine = TemplateEngine(template_dir=tmpdir)
            templates = engine.list_templates()
            self.assertEqual(len(templates), 2)


class TestBuiltinFilters(unittest.TestCase):
    """内置过滤器测试."""

    def test_all_filters_registered(self) -> None:
        """测试所有内置过滤器已注册."""
        expected_filters = {
            "upper", "lower", "title", "strip", "lstrip", "rstrip",
            "default", "truncate", "date", "length", "join", "replace",
            "first", "last", "capitalize", "safe", "escape",
        }
        self.assertTrue(expected_filters.issubset(set(BUILTIN_FILTERS.keys())))

    def test_custom_filter(self) -> None:
        """测试自定义过滤器."""
        engine = TemplateEngine()
        engine.add_filter("reverse", lambda x: str(x)[::-1])
        result = engine.render_string("{{text|reverse}}", {"text": "hello"})
        self.assertEqual(result, "olleh")


if __name__ == "__main__":
    unittest.main()
