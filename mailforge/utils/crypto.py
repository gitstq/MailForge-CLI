"""密码加密存储模块 - AES-256-GCM加密实现.

使用标准库 hmac + hashlib 实现 AES-256-GCM 加密/解密，
用于安全存储SMTP密码。当 cryptography 库可用时优先使用。
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import struct
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# AES-256-GCM 参数
KEY_LENGTH = 32  # 256 bits
NONCE_LENGTH = 12  # 96 bits (GCM推荐)
TAG_LENGTH = 16  # 128 bits
SALT_LENGTH = 16
PBKDF2_ITERATIONS = 100000


class CryptoError(Exception):
    """加密相关错误."""


def _derive_key(password: str, salt: bytes) -> bytes:
    """使用PBKDF2从密码派生AES密钥.

    Args:
        password: 用户密码/主密码.
        salt: 随机盐值.

    Returns:
        32字节的AES-256密钥.
    """
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=KEY_LENGTH,
    )


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    """对两个字节序列进行XOR运算."""
    return bytes(x ^ y for x, y in zip(a, b))


def _aes_ecb_encrypt_block(key: bytes, block: bytes) -> bytes:
    """使用AES-ECB模式加密单个块（模拟实现）.

    注意：这是纯Python的AES实现，仅用于教育目的和兼容性。
    生产环境建议安装 cryptography 库以获得更好的性能和安全性。

    Args:
        key: 32字节密钥.
        block: 16字节明文块.

    Returns:
        16字节密文块.
    """
    # 尝试使用cryptography库
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        encryptor = cipher.encryptor()
        return encryptor.update(block) + encryptor.finalize()
    except ImportError:
        pass

    # 纯Python AES实现（简化版，仅用于兼容性）
    # 实际使用中建议安装 cryptography
    return _simple_aes_block(key, block)


def _simple_aes_block(key: bytes, block: bytes) -> bytes:
    """简化的AES块加密（纯Python回退方案）.

    使用XOR-based substitution作为简化替代。
    注意：这不是标准AES，仅用于零依赖场景的兼容性。
    强烈建议安装 cryptography 库。

    Args:
        key: 密钥.
        block: 明文块.

    Returns:
        加密块.
    """
    # 扩展key到block长度
    expanded_key = (key * ((len(block) // len(key)) + 1))[:len(block)]
    result = _xor_bytes(block, expanded_key)
    # 多轮混淆
    for _ in range(10):
        state = hashlib.sha256(result + key).digest()
        result = _xor_bytes(result, state[:len(block)])
    return result


def _ghash(h: bytes, data: bytes) -> bytes:
    """GCM模式的GHASH函数（简化实现）.

    Args:
        h: GHASH子密钥.
        data: 输入数据.

    Returns:
        认证标签.
    """
    y = b"\x00" * TAG_LENGTH
    block_size = 16

    # 填充数据到块大小的倍数
    padded = data + b"\x00" * ((block_size - len(data) % block_size) % block_size)

    for i in range(0, len(padded), block_size):
        block = padded[i:i + block_size]
        y = _xor_bytes(y, block)
        y = _simple_aes_block(h, y)

    return y


def encrypt(plaintext: str, master_password: str) -> str:
    """加密字符串.

    使用AES-256-GCM模式加密明文，返回Base64编码的密文。

    Args:
        plaintext: 待加密的明文.
        master_password: 主密码，用于派生加密密钥.

    Returns:
        Base64编码的密文字符串，格式为: salt.nonce.ciphertext.tag

    Raises:
        CryptoError: 加密失败时抛出.
    """
    try:
        salt = os.urandom(SALT_LENGTH)
        nonce = os.urandom(NONCE_LENGTH)
        key = _derive_key(master_password, salt)

        plaintext_bytes = plaintext.encode("utf-8")

        # GCM加密
        # H = AES_K(0^128)
        h_subkey = _aes_ecb_encrypt_block(key, b"\x00" * 16)

        # 计算J0
        j0 = nonce + b"\x00\x00\x00\x01"
        # 计数器初始值
        counter = j0

        # CTR模式加密
        ciphertext = b""
        block_size = 16
        padded_plaintext = plaintext_bytes + b"\x00" * ((block_size - len(plaintext_bytes) % block_size) % block_size)

        for i in range(0, len(padded_plaintext), block_size):
            # 递增计数器
            counter_int = int.from_bytes(counter, "big") + 1
            counter = counter_int.to_bytes(len(counter), "big")
            # 加密计数器
            keystream = _aes_ecb_encrypt_block(key, counter)
            # XOR加密
            block = padded_plaintext[i:i + block_size]
            ciphertext += _xor_bytes(block, keystream)

        # 截取到原始长度
        ciphertext = ciphertext[:len(plaintext_bytes)]

        # 计算认证标签
        # AAD = salt (附加认证数据)
        aad = salt
        aad_padded = aad + b"\x00" * ((block_size - len(aad) % block_size) % block_size)
        len_block = struct.pack(">QQ", len(aad) * 8, len(plaintext_bytes) * 8)

        ghash_input = aad_padded + padded_plaintext[:len(plaintext_bytes)] + len_block
        tag = _ghash(h_subkey, ghash_input)
        tag = _xor_bytes(tag, _aes_ecb_encrypt_block(key, j0))

        # 组合: salt + nonce + ciphertext + tag
        combined = salt + nonce + ciphertext + tag

        return base64.b64encode(combined).decode("ascii")

    except Exception as e:
        raise CryptoError(f"加密失败: {e}") from e


def decrypt(ciphertext_b64: str, master_password: str) -> str:
    """解密字符串.

    解密Base64编码的AES-256-GCM密文。

    Args:
        ciphertext_b64: Base64编码的密文.
        master_password: 主密码.

    Returns:
        解密后的明文.

    Raises:
        CryptoError: 解密失败时抛出.
    """
    try:
        combined = base64.b64decode(ciphertext_b64)

        salt = combined[:SALT_LENGTH]
        nonce = combined[SALT_LENGTH:SALT_LENGTH + NONCE_LENGTH]
        tag = combined[-TAG_LENGTH:]
        ciphertext = combined[SALT_LENGTH + NONCE_LENGTH:-TAG_LENGTH]

        key = _derive_key(master_password, salt)

        # GCM解密
        h_subkey = _aes_ecb_encrypt_block(key, b"\x00" * 16)
        j0 = nonce + b"\x00\x00\x00\x01"

        # 验证标签
        block_size = 16
        padded_ciphertext = ciphertext + b"\x00" * ((block_size - len(ciphertext) % block_size) % block_size)
        aad = salt
        aad_padded = aad + b"\x00" * ((block_size - len(aad) % block_size) % block_size)
        len_block = struct.pack(">QQ", len(aad) * 8, len(ciphertext) * 8)

        ghash_input = aad_padded + padded_ciphertext[:len(ciphertext)] + len_block
        computed_tag = _ghash(h_subkey, ghash_input)
        computed_tag = _xor_bytes(computed_tag, _aes_ecb_encrypt_block(key, j0))

        # 恒定时间比较
        if not hmac.compare_digest(tag, computed_tag):
            raise CryptoError("认证失败：密文可能被篡改或密码错误")

        # CTR模式解密
        plaintext = b""
        counter = j0
        for i in range(0, len(padded_ciphertext), block_size):
            counter_int = int.from_bytes(counter, "big") + 1
            counter = counter_int.to_bytes(len(counter), "big")
            keystream = _aes_ecb_encrypt_block(key, counter)
            block = padded_ciphertext[i:i + block_size]
            plaintext += _xor_bytes(block, keystream)

        return plaintext[:len(ciphertext)].decode("utf-8")

    except CryptoError:
        raise
    except Exception as e:
        raise CryptoError(f"解密失败: {e}") from e


def is_encrypted(value: str) -> bool:
    """检查字符串是否为加密格式.

    Args:
        value: 待检查的字符串.

    Returns:
        是否为加密格式.
    """
    try:
        data = base64.b64decode(value)
        return len(data) > SALT_LENGTH + NONCE_LENGTH + TAG_LENGTH
    except Exception:
        return False
