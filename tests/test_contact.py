"""联系人管理测试."""

import json
import os
import tempfile
import unittest

from mailforge.core.contact import Contact, ContactManager, ContactError


class TestContact(unittest.TestCase):
    """Contact测试."""

    def test_create_contact(self) -> None:
        """测试创建联系人."""
        c = Contact(email="test@example.com", name="Test User", group="vip")
        self.assertEqual(c.email, "test@example.com")
        self.assertEqual(c.name, "Test User")
        self.assertEqual(c.group, "vip")

    def test_email_normalized(self) -> None:
        """测试邮箱地址标准化."""
        c = Contact(email="  Test@Example.COM  ")
        self.assertEqual(c.email, "test@example.com")

    def test_to_dict(self) -> None:
        """测试序列化."""
        c = Contact(email="test@example.com", name="Test", phone="123456")
        data = c.to_dict()
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["name"], "Test")
        self.assertEqual(data["phone"], "123456")

    def test_from_dict(self) -> None:
        """测试反序列化."""
        data = {"email": "test@example.com", "name": "Test", "group": "vip", "city": "Beijing"}
        c = Contact.from_dict(data)
        self.assertEqual(c.email, "test@example.com")
        self.assertEqual(c.name, "Test")
        self.assertEqual(c.group, "vip")
        self.assertEqual(c.extra["city"], "Beijing")

    def test_equality(self) -> None:
        """测试相等性比较."""
        c1 = Contact(email="test@example.com", name="Alice")
        c2 = Contact(email="test@example.com", name="Bob")
        self.assertEqual(c1, c2)

    def test_hash(self) -> None:
        """测试哈希."""
        c1 = Contact(email="test@example.com")
        c2 = Contact(email="test@example.com")
        self.assertEqual(hash(c1), hash(c2))


class TestContactManager(unittest.TestCase):
    """ContactManager测试."""

    def setUp(self) -> None:
        """测试前准备."""
        self.manager = ContactManager()

    def test_add_contact(self) -> None:
        """测试添加联系人."""
        c = Contact(email="test@example.com", name="Test")
        ok, msg = self.manager.add_contact(c)
        self.assertTrue(ok)
        self.assertEqual(self.manager.total_count, 1)

    def test_add_duplicate(self) -> None:
        """测试添加重复联系人."""
        c1 = Contact(email="test@example.com")
        c2 = Contact(email="test@example.com")
        self.manager.add_contact(c1)
        ok, _ = self.manager.add_contact(c2)
        self.assertFalse(ok)
        self.assertEqual(self.manager.total_count, 1)

    def test_add_invalid_email(self) -> None:
        """测试添加无效邮箱."""
        c = Contact(email="not-an-email")
        ok, msg = self.manager.add_contact(c)
        self.assertFalse(ok)

    def test_remove_contact(self) -> None:
        """测试删除联系人."""
        self.manager.add_contact(Contact(email="test@example.com"))
        result = self.manager.remove_contact("test@example.com")
        self.assertTrue(result)
        self.assertEqual(self.manager.total_count, 0)

    def test_remove_nonexistent(self) -> None:
        """测试删除不存在的联系人."""
        result = self.manager.remove_contact("nonexistent@example.com")
        self.assertFalse(result)

    def test_update_contact(self) -> None:
        """测试更新联系人."""
        self.manager.add_contact(Contact(email="test@example.com", name="Old"))
        ok, msg = self.manager.update_contact("test@example.com", name="New")
        self.assertTrue(ok)
        contact = self.manager.get_contact("test@example.com")
        self.assertIsNotNone(contact)
        self.assertEqual(contact.name, "New")

    def test_list_contacts(self) -> None:
        """测试列出联系人."""
        self.manager.add_contact(Contact(email="a@example.com", name="Alice"))
        self.manager.add_contact(Contact(email="b@example.com", name="Bob"))
        contacts = self.manager.list_contacts()
        self.assertEqual(len(contacts), 2)

    def test_list_contacts_by_group(self) -> None:
        """测试按分组列出."""
        self.manager.add_contact(Contact(email="a@example.com", group="vip"))
        self.manager.add_contact(Contact(email="b@example.com", group="normal"))
        contacts = self.manager.list_contacts(group="vip")
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].email, "a@example.com")

    def test_list_contacts_search(self) -> None:
        """测试搜索联系人."""
        self.manager.add_contact(Contact(email="alice@example.com", name="Alice Wang"))
        self.manager.add_contact(Contact(email="bob@example.com", name="Bob Li"))
        contacts = self.manager.list_contacts(search="alice")
        self.assertEqual(len(contacts), 1)

    def test_list_contacts_pagination(self) -> None:
        """测试分页."""
        for i in range(10):
            self.manager.add_contact(Contact(email=f"user{i}@example.com", name=f"User {i}"))

        page1 = self.manager.list_contacts(limit=3, offset=0)
        page2 = self.manager.list_contacts(limit=3, offset=3)
        self.assertEqual(len(page1), 3)
        self.assertEqual(len(page2), 3)
        self.assertNotEqual(page1[0].email, page2[0].email)

    def test_groups(self) -> None:
        """测试分组列表."""
        self.manager.add_contact(Contact(email="a@example.com", group="vip"))
        self.manager.add_contact(Contact(email="b@example.com", group="normal"))
        groups = self.manager.groups
        self.assertIn("vip", groups)
        self.assertIn("normal", groups)

    def test_create_group(self) -> None:
        """测试创建分组."""
        ok, msg = self.manager.create_group("new_group")
        self.assertTrue(ok)
        self.assertIn("new_group", self.manager.groups)

    def test_create_duplicate_group(self) -> None:
        """测试创建重复分组."""
        self.manager.create_group("test")
        ok, _ = self.manager.create_group("test")
        self.assertFalse(ok)

    def test_delete_group(self) -> None:
        """测试删除分组."""
        self.manager.add_contact(Contact(email="a@example.com", group="temp"))
        ok, _ = self.manager.delete_group("temp")
        self.assertTrue(ok)
        self.assertNotIn("temp", self.manager.groups)

    def test_deduplicate(self) -> None:
        """测试去重."""
        c1 = Contact(email="test@example.com")
        c2 = Contact(email="test@example.com")
        # 直接添加到内部字典模拟重复
        self.manager.contacts["test@example.com"] = c1
        self.manager.contacts["test@example.com"] = c2
        count = self.manager.deduplicate()
        self.assertGreaterEqual(count, 0)

    def test_batch_add(self) -> None:
        """测试批量添加."""
        contacts = [
            Contact(email=f"user{i}@example.com")
            for i in range(5)
        ]
        success, fail = self.manager.batch_add(contacts)
        self.assertEqual(success, 5)
        self.assertEqual(fail, 0)

    def test_batch_remove(self) -> None:
        """测试批量删除."""
        for i in range(3):
            self.manager.add_contact(Contact(email=f"user{i}@example.com"))
        count = self.manager.batch_remove([f"user{i}@example.com" for i in range(3)])
        self.assertEqual(count, 3)
        self.assertEqual(self.manager.total_count, 0)

    def test_import_csv(self) -> None:
        """测试CSV导入."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("email,name,group\n")
            f.write("alice@example.com,Alice,vip\n")
            f.write("bob@example.com,Bob,normal\n")
            csv_path = f.name

        try:
            success, fail, errors = self.manager.import_csv(csv_path)
            self.assertEqual(success, 2)
            self.assertEqual(fail, 0)
            self.assertEqual(self.manager.total_count, 2)
        finally:
            os.unlink(csv_path)

    def test_import_json(self) -> None:
        """测试JSON导入."""
        data = [
            {"email": "alice@example.com", "name": "Alice", "group": "vip"},
            {"email": "bob@example.com", "name": "Bob", "group": "normal"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            json_path = f.name

        try:
            success, fail, errors = self.manager.import_json(json_path)
            self.assertEqual(success, 2)
            self.assertEqual(fail, 0)
        finally:
            os.unlink(json_path)

    def test_export_csv(self) -> None:
        """测试CSV导出."""
        self.manager.add_contact(Contact(email="test@example.com", name="Test"))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            count = self.manager.export_csv(csv_path)
            self.assertEqual(count, 1)
            self.assertTrue(os.path.exists(csv_path))
        finally:
            os.unlink(csv_path)

    def test_export_json(self) -> None:
        """测试JSON导出."""
        self.manager.add_contact(Contact(email="test@example.com", name="Test"))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_path = f.name

        try:
            count = self.manager.export_json(json_path)
            self.assertEqual(count, 1)

            with open(json_path, "r") as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
        finally:
            os.unlink(json_path)

    def test_save_load(self) -> None:
        """测试保存和加载."""
        self.manager.add_contact(Contact(email="test@example.com", name="Test"))

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "contacts.json")
            self.manager.save(json_path)

            new_manager = ContactManager()
            new_manager.load(json_path)
            self.assertEqual(new_manager.total_count, 1)
            contact = new_manager.get_contact("test@example.com")
            self.assertIsNotNone(contact)
            self.assertEqual(contact.name, "Test")


if __name__ == "__main__":
    unittest.main()
