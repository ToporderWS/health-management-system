# -*- coding: utf-8 -*-
"""生成与 Werkzeug 兼容的 pbkdf2:sha256 密码哈希，用于写入初始化 SQL。

运行方式：python tools/gen_password_hash.py
说明：本脚本是开发/运维工具，会持有用于生成哈希的原始口令；
      它不参与产品运行时，也不会把明文写进数据库。
"""
import hashlib
import os
import string


def gen_salt(length=16):
    alphabet = string.ascii_letters + string.digits
    return "".join(alphabet[os.urandom(1)[0] % len(alphabet)] for _ in range(length))


def generate_password_hash(password, method="pbkdf2:sha256", salt_length=16):
    salt = gen_salt(salt_length)
    parts = method.split(":")
    algo = parts[1] if len(parts) > 1 else "sha256"
    iterations = int(parts[2]) if len(parts) > 2 else 600000
    dk = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt.encode("utf-8"), iterations)
    full_method = "%s:%s:%d" % (parts[0], algo, iterations)
    return "%s$%s$%s" % (full_method, salt, dk.hex())


def check_password_hash(pwhash, password):
    try:
        method, salt, hashval = pwhash.split("$", 2)
    except ValueError:
        return False
    parts = method.split(":")
    algo = parts[1] if len(parts) > 1 else "sha256"
    iterations = int(parts[2]) if len(parts) > 2 else 600000
    dk = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return dk.hex() == hashval


if __name__ == "__main__":
    for name in ["admin", "doctor001", "doctor002", "coach001", "coach002", "user001", "user002"]:
        h = generate_password_hash("123456")
        ok = check_password_hash(h, "123456")
        print("%s|%s|%s" % (name, h, ok))
