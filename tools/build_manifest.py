#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成图片清单 manifest.json（供 GitHub Pages 静态托管使用）

GitHub Pages 是纯静态托管，页面无法自己扫描文件夹，
所以由本脚本在 GitHub Actions 里（每次往 pic/ 推送图片时）自动执行：
  1. 扫描 pic 文件夹里所有图片
  2. 用 git 提交时间作为「图片修改时间」（Actions 里文件系统的 mtime 全是 checkout 时间，不能用）
  3. 解析图片宽高（零依赖，纯标准库读取文件头）
  4. 按时间从新到旧排序，写出 manifest.json 到仓库根目录

用法：
  python3 tools/build_manifest.py
"""

import json
import os
import struct
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIC_DIR = os.path.join(ROOT, "pic")
OUT_FILE = os.path.join(ROOT, "manifest.json")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".avif", ".jfif", ".heic"}


# ---------- 图片宽高解析（零依赖） ----------
def _jpeg_size(f):
    f.seek(2)
    while True:
        b = f.read(1)
        while b and b != b"\xff":
            b = f.read(1)
        marker = f.read(1)
        while marker == b"\xff":
            marker = f.read(1)
        if not marker:
            return None
        m = marker[0]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            f.read(3)
            h, w = struct.unpack(">HH", f.read(4))
            return w, h
        ln = struct.unpack(">H", f.read(2))[0]
        f.seek(ln - 2, 1)


def _png_size(f):
    head = f.read(24)
    if len(head) < 24:
        return None
    return struct.unpack(">II", head[16:24])


def _gif_size(f):
    head = f.read(10)
    if len(head) < 10:
        return None
    w, h = struct.unpack("<HH", head[6:10])
    return w, h


def _webp_size(f):
    head = f.read(30)
    if len(head) < 30 or head[12:16] != b"VP8 ":
        return None
    w = struct.unpack("<H", head[26:28])[0] & 0x3FFF
    h = struct.unpack("<H", head[28:30])[0] & 0x3FFF
    return w, h


def _bmp_size(f):
    head = f.read(26)
    if len(head) < 26:
        return None
    w, h = struct.unpack("<ii", head[18:26])
    return abs(w), abs(h)


def image_size(path):
    try:
        with open(path, "rb") as f:
            magic = f.read(12)
            f.seek(0)
            if magic[:2] == b"\xff\xd8":
                return _jpeg_size(f)
            if magic[:8] == b"\x89PNG\r\n\x1a\n":
                return _png_size(f)
            if magic[:6] in (b"GIF87a", b"GIF89a"):
                return _gif_size(f)
            if magic[:4] == b"RIFF" and magic[8:12] == b"WEBP":
                return _webp_size(f)
            if magic[:2] == b"BM":
                return _bmp_size(f)
    except Exception:
        pass
    return None


# ---------- 时间：优先用 git 提交时间 ----------
def git_mtime(rel_path):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", rel_path],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        v = out.stdout.strip()
        if v:
            return int(v)
    except Exception:
        pass
    return None


def build():
    items = []
    if not os.path.isdir(PIC_DIR):
        os.makedirs(PIC_DIR, exist_ok=True)

    for name in sorted(os.listdir(PIC_DIR)):
        path = os.path.join(PIC_DIR, name)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(name)[1].lower() not in IMAGE_EXT:
            continue

        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        mtime = git_mtime(rel)
        if mtime is None:
            mtime = int(os.stat(path).st_mtime)
        size = image_size(path)

        items.append({
            "name": name,
            "url": "pic/" + name.replace(" ", "%20").replace("#", "%23"),
            "mtime": mtime,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)),
            "width": size[0] if size else 0,
            "height": size[1] if size else 0,
            "bytes": os.path.getsize(path),
        })

    # 修改时间从新到旧；时间相同按文件名倒序
    items.sort(key=lambda x: (x["mtime"], x["name"]), reverse=True)

    payload = {
        "count": len(items),
        "photos": items,
        "scanTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "updated": int(time.time()),
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print("已生成 %s：共 %d 张图片" % (OUT_FILE, len(items)))
    for it in items[:5]:
        print("   %s  %s  %sx%s" % (it["time"], it["name"], it["width"], it["height"]))


if __name__ == "__main__":
    build()
