"""联系人管理模块 - CSV/JSON导入导出、分组管理、去重.

支持CSV和JSON格式的联系人导入导出，自动字段映射、分组管理、
基于邮箱地址的去重、邮箱格式验证、批量操作等功能。
"""

import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from mailforge.utils.validators import validate_email

logger = logging.getLogger(__name__)


class ContactError(Exception):
    """联系人管理相关错误."""


class Contact:
    """单个联系人.

    Attributes:
        email: 邮箱地址.
        name: 姓名.
        group: 分组名称.
        extra: 额外自定义字段.
    """

    def __init__(
        self,
        email: str,
        name: str = "",
        group: str = "default",
        **extra: Any,
    ) -> None:
        """初始化联系人.

        Args:
            email: 邮箱地址.
            name: 姓名.
            group: 分组名称.
            **extra: 额外字段.
        """
        self.email = email.strip().lower()
        self.name = name.strip()
        self.group = group.strip()
        self.extra = extra

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        data: Dict[str, Any] = {
            "email": self.email,
            "name": self.name,
            "group": self.group,
        }
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        """从字典创建联系人."""
        email = data.pop("email", "")
        name = data.pop("name", "")
        group = data.pop("group", "default")
        return cls(email=email, name=name, group=group, **data)

    def __repr__(self) -> str:
        return f"Contact(email={self.email!r}, name={self.name!r}, group={self.group!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Contact):
            return NotImplemented
        return self.email == other.email

    def __hash__(self) -> int:
        return hash(self.email)


class ContactManager:
    """联系人管理器.

    管理联系人列表，支持导入导出、分组、去重、批量操作。

    Usage:
        manager = ContactManager()
        manager.import_csv("contacts.csv")
        manager.list_contacts(group="vip")
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        """初始化联系人管理器.

        Args:
            storage_dir: 联系人数据存储目录.
        """
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.contacts: Dict[str, Contact] = {}  # email -> Contact
        self._groups: Dict[str, Set[str]] = {}  # group_name -> set of emails

    @property
    def total_count(self) -> int:
        """联系人总数."""
        return len(self.contacts)

    @property
    def groups(self) -> List[str]:
        """所有分组列表."""
        return sorted(self._groups.keys())

    def add_contact(self, contact: Contact, skip_validation: bool = False) -> Tuple[bool, str]:
        """添加单个联系人.

        Args:
            contact: Contact实例.
            skip_validation: 是否跳过邮箱验证.

        Returns:
            (是否成功, 消息) 元组.
        """
        if not skip_validation:
            valid, msg = validate_email(contact.email)
            if not valid:
                return False, f"邮箱验证失败: {msg}"

        if contact.email in self.contacts:
            return False, f"联系人已存在: {contact.email}"

        self.contacts[contact.email] = contact
        self._add_to_group(contact.email, contact.group)
        logger.debug("联系人已添加: %s", contact.email)
        return True, f"已添加: {contact.email}"

    def remove_contact(self, email: str) -> bool:
        """删除联系人.

        Args:
            email: 邮箱地址.

        Returns:
            是否成功删除.
        """
        email = email.strip().lower()
        if email not in self.contacts:
            return False

        contact = self.contacts[email]
        self._remove_from_group(email, contact.group)
        del self.contacts[email]
        logger.debug("联系人已删除: %s", email)
        return True

    def update_contact(self, email: str, **fields: Any) -> Tuple[bool, str]:
        """更新联系人信息.

        Args:
            email: 邮箱地址.
            **fields: 要更新的字段.

        Returns:
            (是否成功, 消息) 元组.
        """
        email = email.strip().lower()
        if email not in self.contacts:
            return False, f"联系人不存在: {email}"

        contact = self.contacts[email]
        old_group = contact.group

        if "email" in fields:
            new_email = fields["email"].strip().lower()
            valid, msg = validate_email(new_email)
            if not valid:
                return False, f"邮箱验证失败: {msg}"
            if new_email != email and new_email in self.contacts:
                return False, f"目标邮箱已存在: {new_email}"
            self._remove_from_group(email, contact.group)
            del self.contacts[email]
            contact.email = new_email
            email = new_email

        for key, value in fields.items():
            if key == "email":
                continue
            setattr(contact, key, value)

        if "group" in fields and fields["group"] != old_group:
            self._remove_from_group(email, old_group)
            self._add_to_group(email, contact.group)

        self.contacts[email] = contact
        logger.debug("联系人已更新: %s", email)
        return True, f"已更新: {email}"

    def get_contact(self, email: str) -> Optional[Contact]:
        """获取联系人.

        Args:
            email: 邮箱地址.

        Returns:
            Contact实例或None.
        """
        return self.contacts.get(email.strip().lower())

    def list_contacts(
        self,
        group: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Contact]:
        """列出联系人.

        Args:
            group: 按分组过滤.
            search: 搜索关键词（匹配姓名或邮箱）.
            limit: 返回数量限制.
            offset: 偏移量.

        Returns:
            联系人列表.
        """
        contacts = list(self.contacts.values())

        if group:
            group_emails = self._groups.get(group, set())
            contacts = [c for c in contacts if c.email in group_emails]

        if search:
            search_lower = search.lower()
            contacts = [
                c for c in contacts
                if search_lower in c.name.lower() or search_lower in c.email.lower()
            ]

        contacts.sort(key=lambda c: c.name or c.email)
        return contacts[offset:offset + limit]

    def import_csv(
        self,
        file_path: str,
        group: str = "default",
        email_column: Optional[str] = None,
        name_column: Optional[str] = None,
        skip_invalid: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """从CSV文件导入联系人.

        自动识别name/email列，支持自定义列映射。

        Args:
            file_path: CSV文件路径.
            group: 导入到的分组.
            email_column: 邮箱列名（为空则自动识别）.
            name_column: 姓名列名（为空则自动识别）.
            skip_invalid: 是否跳过无效记录.

        Returns:
            (成功数, 失败数, 错误信息列表) 元组.
        """
        path = Path(file_path)
        if not path.exists():
            raise ContactError(f"文件不存在: {file_path}")

        success_count = 0
        fail_count = 0
        errors: List[str] = []

        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ContactError("CSV文件为空或格式错误")

                # 自动识别列名
                email_col = email_column or self._detect_column(
                    list(reader.fieldnames), ["email", "e-mail", "mail", "邮箱", "电子邮件"]
                )
                name_col = name_column or self._detect_column(
                    list(reader.fieldnames), ["name", "姓名", "名字", "full_name", "fullname", "username"]
                )

                if not email_col:
                    raise ContactError("无法识别邮箱列，请使用 --email-column 指定")

                for row_num, row in enumerate(reader, start=2):
                    try:
                        email = row.get(email_col, "").strip()
                        if not email:
                            fail_count += 1
                            errors.append(f"第{row_num}行: 邮箱为空")
                            continue

                        name = row.get(name_col, "").strip() if name_col else ""

                        # 提取额外字段（排除已知字段）
                        reserved_keys = {"email", "name", "group"}
                        extra = {}
                        for key, value in row.items():
                            if key not in (email_col, name_col) and key not in reserved_keys and value.strip():
                                extra[key] = value.strip()

                        # 如果CSV中有group列，优先使用CSV中的值
                        csv_group = row.get("group", "").strip()
                        contact_group = csv_group if csv_group else group

                        contact = Contact(
                            email=email,
                            name=name,
                            group=contact_group,
                            **extra,
                        )
                        ok, msg = self.add_contact(contact)
                        if ok:
                            success_count += 1
                        else:
                            fail_count += 1
                            errors.append(f"第{row_num}行: {msg}")

                    except Exception as e:
                        fail_count += 1
                        errors.append(f"第{row_num}行: {e}")

        except ContactError:
            raise
        except Exception as e:
            raise ContactError(f"读取CSV文件失败: {e}") from e

        logger.info(
            "CSV导入完成: 成功=%d, 失败=%d, 文件=%s",
            success_count, fail_count, file_path,
        )
        return success_count, fail_count, errors

    def import_json(
        self,
        file_path: str,
        group: str = "default",
        skip_invalid: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """从JSON文件导入联系人.

        Args:
            file_path: JSON文件路径.
            group: 导入到的分组.
            skip_invalid: 是否跳过无效记录.

        Returns:
            (成功数, 失败数, 错误信息列表) 元组.
        """
        path = Path(file_path)
        if not path.exists():
            raise ContactError(f"文件不存在: {file_path}")

        success_count = 0
        fail_count = 0
        errors: List[str] = []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ContactError("JSON格式错误：期望数组")

            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    fail_count += 1
                    errors.append(f"第{idx + 1}项: 不是有效的对象")
                    continue

                try:
                    email = item.get("email", "").strip()
                    if not email:
                        fail_count += 1
                        errors.append(f"第{idx + 1}项: 邮箱为空")
                        continue

                    name = item.get("name", "").strip()
                    item_group = item.get("group", group)

                    extra = {k: v for k, v in item.items() if k not in ("email", "name", "group")}

                    contact = Contact(email=email, name=name, group=item_group, **extra)
                    ok, msg = self.add_contact(contact)
                    if ok:
                        success_count += 1
                    else:
                        fail_count += 1
                        errors.append(f"第{idx + 1}项: {msg}")

                except Exception as e:
                    fail_count += 1
                    errors.append(f"第{idx + 1}项: {e}")

        except json.JSONDecodeError as e:
            raise ContactError(f"JSON解析失败: {e}") from e
        except ContactError:
            raise
        except Exception as e:
            raise ContactError(f"读取JSON文件失败: {e}") from e

        logger.info(
            "JSON导入完成: 成功=%d, 失败=%d, 文件=%s",
            success_count, fail_count, file_path,
        )
        return success_count, fail_count, errors

    def export_csv(self, file_path: str, group: Optional[str] = None) -> int:
        """导出联系人为CSV文件.

        Args:
            file_path: 输出文件路径.
            group: 按分组过滤（为空则导出全部）.

        Returns:
            导出的联系人数量.

        Raises:
            ContactError: 导出失败时抛出.
        """
        contacts = self.list_contacts(group=group, limit=999999)

        if not contacts:
            logger.warning("没有联系人可导出")
            return 0

        # 收集所有字段
        all_keys: List[str] = ["email", "name", "group"]
        for contact in contacts:
            for key in contact.extra:
                if key not in all_keys:
                    all_keys.append(key)

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=all_keys)
                writer.writeheader()
                for contact in contacts:
                    writer.writerow(contact.to_dict())
        except OSError as e:
            raise ContactError(f"导出CSV失败: {e}") from e

        logger.info("已导出 %d 个联系人到 %s", len(contacts), file_path)
        return len(contacts)

    def export_json(self, file_path: str, group: Optional[str] = None) -> int:
        """导出联系人为JSON文件.

        Args:
            file_path: 输出文件路径.
            group: 按分组过滤（为空则导出全部）.

        Returns:
            导出的联系人数量.

        Raises:
            ContactError: 导出失败时抛出.
        """
        contacts = self.list_contacts(group=group, limit=999999)

        if not contacts:
            logger.warning("没有联系人可导出")
            return 0

        data = [c.to_dict() for c in contacts]

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise ContactError(f"导出JSON失败: {e}") from e

        logger.info("已导出 %d 个联系人到 %s", len(contacts), file_path)
        return len(contacts)

    def deduplicate(self) -> int:
        """基于邮箱地址去重.

        Returns:
            删除的重复联系人数量.
        """
        seen_emails: Set[str] = set()
        duplicates: List[str] = []

        for email in list(self.contacts.keys()):
            if email in seen_emails:
                duplicates.append(email)
            else:
                seen_emails.add(email)

        for email in duplicates:
            contact = self.contacts[email]
            self._remove_from_group(email, contact.group)
            del self.contacts[email]

        logger.info("已删除 %d 个重复联系人", len(duplicates))
        return len(duplicates)

    def get_group_contacts(self, group: str) -> List[Contact]:
        """获取指定分组的所有联系人.

        Args:
            group: 分组名称.

        Returns:
            该分组的联系人列表.
        """
        group_emails = self._groups.get(group, set())
        return [self.contacts[e] for e in group_emails if e in self.contacts]

    def get_group_count(self, group: str) -> int:
        """获取分组联系人数量.

        Args:
            group: 分组名称.

        Returns:
            联系人数量.
        """
        return len(self._groups.get(group, set()))

    def create_group(self, group: str) -> Tuple[bool, str]:
        """创建分组.

        Args:
            group: 分组名称.

        Returns:
            (是否成功, 消息) 元组.
        """
        if group in self._groups:
            return False, f"分组已存在: {group}"
        self._groups[group] = set()
        return True, f"分组已创建: {group}"

    def delete_group(self, group: str, remove_contacts: bool = False) -> Tuple[bool, str]:
        """删除分组.

        Args:
            group: 分组名称.
            remove_contacts: 是否同时删除分组中的联系人.

        Returns:
            (是否成功, 消息) 元组.
        """
        if group not in self._groups:
            return False, f"分组不存在: {group}"

        if remove_contacts:
            for email in list(self._groups[group]):
                if email in self.contacts:
                    del self.contacts[email]
        else:
            # 将联系人移到default组
            for email in self._groups[group]:
                if email in self.contacts:
                    self.contacts[email].group = "default"
                    self._add_to_group(email, "default")

        del self._groups[group]
        return True, f"分组已删除: {group}"

    def batch_add(self, contacts: List[Contact]) -> Tuple[int, int]:
        """批量添加联系人.

        Args:
            contacts: Contact列表.

        Returns:
            (成功数, 失败数) 元组.
        """
        success = 0
        fail = 0
        for contact in contacts:
            ok, _ = self.add_contact(contact)
            if ok:
                success += 1
            else:
                fail += 1
        return success, fail

    def batch_remove(self, emails: List[str]) -> int:
        """批量删除联系人.

        Args:
            emails: 邮箱地址列表.

        Returns:
            成功删除的数量.
        """
        count = 0
        for email in emails:
            if self.remove_contact(email):
                count += 1
        return count

    def _add_to_group(self, email: str, group: str) -> None:
        """将邮箱添加到分组."""
        if group not in self._groups:
            self._groups[group] = set()
        self._groups[group].add(email)

    def _remove_from_group(self, email: str, group: str) -> None:
        """将邮箱从分组移除."""
        if group in self._groups:
            self._groups[group].discard(email)

    @staticmethod
    def _detect_column(headers: List[str], candidates: List[str]) -> Optional[str]:
        """自动识别列名.

        Args:
            headers: CSV表头列表.
            candidates: 候选列名列表.

        Returns:
            匹配的列名或None.
        """
        headers_lower = {h.lower().strip(): h for h in headers}
        for candidate in candidates:
            if candidate.lower() in headers_lower:
                return headers_lower[candidate.lower()]
        return None

    def save(self, file_path: Optional[str] = None) -> None:
        """保存联系人数据到文件.

        Args:
            file_path: 文件路径，默认使用storage_dir/contacts.json.
        """
        if file_path is None:
            if not self.storage_dir:
                raise ContactError("未设置存储目录")
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(self.storage_dir / "contacts.json")

        data = [c.to_dict() for c in self.contacts.values()]
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("联系人数据已保存到 %s", file_path)
        except OSError as e:
            raise ContactError(f"保存联系人数据失败: {e}") from e

    def load(self, file_path: Optional[str] = None) -> None:
        """从文件加载联系人数据.

        Args:
            file_path: 文件路径，默认使用storage_dir/contacts.json.
        """
        if file_path is None:
            if not self.storage_dir:
                return
            file_path = str(self.storage_dir / "contacts.json")

        path = Path(file_path)
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "email" in item:
                        contact = Contact.from_dict(item)
                        self.contacts[contact.email] = contact
                        self._add_to_group(contact.email, contact.group)

            logger.info("已从 %s 加载 %d 个联系人", file_path, len(self.contacts))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("加载联系人数据失败: %s", e)
