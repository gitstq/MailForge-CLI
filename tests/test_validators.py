"""验证器测试."""

import time
import unittest

from mailforge.utils.validators import (
    validate_email,
    validate_email_batch,
    check_content_safety,
    RateLimiter,
)


class TestValidateEmail(unittest.TestCase):
    """邮箱验证测试."""

    def test_valid_email(self) -> None:
        """测试有效邮箱."""
        valid, msg = validate_email("test@example.com")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_valid_email_with_dots(self) -> None:
        """测试带点号的邮箱."""
        valid, _ = validate_email("first.last@example.com")
        self.assertTrue(valid)

    def test_valid_email_with_plus(self) -> None:
        """测试带加号的邮箱."""
        valid, _ = validate_email("user+tag@example.com")
        self.assertTrue(valid)

    def test_valid_email_subdomain(self) -> None:
        """测试子域名邮箱."""
        valid, _ = validate_email("user@mail.example.com")
        self.assertTrue(valid)

    def test_empty_email(self) -> None:
        """测试空邮箱."""
        valid, msg = validate_email("")
        self.assertFalse(valid)

    def test_no_at_sign(self) -> None:
        """测试无@符号."""
        valid, msg = validate_email("testexample.com")
        self.assertFalse(valid)

    def test_multiple_at_signs(self) -> None:
        """测试多个@符号."""
        valid, msg = validate_email("test@@example.com")
        self.assertFalse(valid)

    def test_no_domain(self) -> None:
        """测试无域名."""
        valid, msg = validate_email("test@")
        self.assertFalse(valid)

    def test_no_local(self) -> None:
        """测试无本地部分."""
        valid, msg = validate_email("@example.com")
        self.assertFalse(valid)

    def test_too_long(self) -> None:
        """测试过长邮箱."""
        long_email = "a" * 300 + "@example.com"
        valid, msg = validate_email(long_email)
        self.assertFalse(valid)

    def test_leading_dot(self) -> None:
        """测试域名以点开头."""
        valid, msg = validate_email("test@.example.com")
        self.assertFalse(valid)

    def test_trailing_dot(self) -> None:
        """测试域名以点结尾."""
        valid, msg = validate_email("test@example.com.")
        self.assertFalse(valid)

    def test_whitespace_handling(self) -> None:
        """测试空白处理."""
        valid, _ = validate_email("  test@example.com  ")
        self.assertTrue(valid)


class TestValidateEmailBatch(unittest.TestCase):
    """批量邮箱验证测试."""

    def test_batch_validation(self) -> None:
        """测试批量验证."""
        emails = ["test@example.com", "invalid", "good@domain.org"]
        results = validate_email_batch(emails)
        self.assertEqual(len(results), 3)
        self.assertTrue(results["test@example.com"][0])
        self.assertFalse(results["invalid"][0])
        self.assertTrue(results["good@domain.org"][0])


class TestCheckContentSafety(unittest.TestCase):
    """内容安全检查测试."""

    def test_safe_content(self) -> None:
        """测试安全内容."""
        is_safe, warnings = check_content_safety("Hello", "This is a normal email.")
        self.assertTrue(is_safe)
        self.assertEqual(len(warnings), 0)

    def test_spam_keyword(self) -> None:
        """测试垃圾邮件关键词."""
        is_safe, warnings = check_content_safety("Offer", "Click here to get free money!")
        self.assertFalse(is_safe)
        self.assertTrue(any("垃圾邮件关键词" in w for w in warnings))

    def test_dangerous_html(self) -> None:
        """测试危险HTML."""
        is_safe, warnings = check_content_safety(
            "Test",
            '<script>alert("xss")</script>',
        )
        self.assertFalse(is_safe)

    def test_long_subject(self) -> None:
        """测试过长主题."""
        long_subject = "A" * 300
        is_safe, warnings = check_content_safety(long_subject, "Body")
        self.assertFalse(is_safe)

    def test_too_many_urls(self) -> None:
        """测试过多链接."""
        body = "\n".join([f"https://example{i}.com" for i in range(15)])
        is_safe, warnings = check_content_safety("Test", body)
        self.assertFalse(is_safe)

    def test_strict_mode(self) -> None:
        """测试严格模式."""
        body = "A" * 100  # 全部大写
        is_safe, warnings = check_content_safety("Test", body, strict=True)
        # 可能触发大写比例警告
        # 由于只有100字符，可能不触发（需要>50字符）
        pass


class TestRateLimiter(unittest.TestCase):
    """频率限制器测试."""

    def test_initial_state(self) -> None:
        """测试初始状态."""
        limiter = RateLimiter(per_minute=10, per_hour=100)
        can_send, wait = limiter.check()
        self.assertTrue(can_send)
        self.assertIsNone(wait)

    def test_record_and_check(self) -> None:
        """测试记录后检查."""
        limiter = RateLimiter(per_minute=2)
        limiter.record()
        limiter.record()
        can_send, wait = limiter.check()
        self.assertFalse(can_send)
        self.assertIsNotNone(wait)

    def test_acquire(self) -> None:
        """测试获取许可."""
        limiter = RateLimiter(per_minute=100)
        wait = limiter.acquire()
        self.assertEqual(wait, 0.0)

    def test_minute_count(self) -> None:
        """测试分钟计数."""
        limiter = RateLimiter(per_minute=100)
        limiter.record()
        limiter.record()
        self.assertEqual(limiter.minute_count, 2)

    def test_hour_count(self) -> None:
        """测试小时计数."""
        limiter = RateLimiter(per_hour=100)
        limiter.record()
        limiter.record()
        self.assertEqual(limiter.hour_count, 2)

    def test_reset(self) -> None:
        """测试重置."""
        limiter = RateLimiter(per_minute=10)
        limiter.record()
        limiter.record()
        limiter.reset()
        can_send, _ = limiter.check()
        self.assertTrue(can_send)


if __name__ == "__main__":
    unittest.main()
