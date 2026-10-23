#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广州市南武中学2026年陈彦健康体育节校本部图片直播 —— 本地服务器

作用：
  1. 把 index.html 托管到 http://localhost:8000
  2. 对外提供 /api/photos 接口，实时扫描 pic 文件夹，返回图片数量、文件名和修改时间
     （前端靠它做到「图片数量自动读取」+「刷新实时更新」）
  3. --manifest 模式：生成 pic/manifest.json，用于纯静态托管（如直接丢到学校服务器/对象存储）

用法：
  python server.py              # 启动服务并自动打开浏览器
  python server.py --port 9000  # 指定端口
  python server.py --no-browser # 不自动打开浏览器
  python server.py --manifest   # 只生成 pic/manifest.json（静态托管时用）
"""

import http.server
import json
import mimetypes
import os
import socketserver
import sys
import time
import urllib.parse
import webbrowser

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PIC_DIR = os.path.join(BASE_DIR, "pic")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".avif", ".heic", ".jfif"}
DEFAULT_PORT = 8000


def scan_photos():
    """实时扫描 pic 文件夹，返回按修改时间从新到旧排序的图片列表"""
    items = []
    if not os.path.isdir(PIC_DIR):
        return items
    for name in os.listdir(PIC_DIR):
        path = os.path.join(PIC_DIR, name)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(name)[1].lower() not in IMAGE_EXT:
            continue
        try:
            st = os.stat(path)
        except OSError:
            continue
        items.append({
            "name": name,
            "url": "pic/" + urllib.parse.quote(name),
            "mtime": int(st.st_mtime),
            "size": st.st_size,
        })
    # 修改时间新的排前面；时间相同则按文件名倒序
    items.sort(key=lambda x: (x["mtime"], x["name"]), reverse=True)
    for it in items:
        it["time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(it["mtime"]))
    return items


def build_payload():
    photos = scan_photos()
    return {
        "count": len(photos),
        "photos": photos,
        "scanTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "updated": int(time.time()),
    }


class LiveHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path.rstrip("/")
        if path == "/api/photos":
            payload = json.dumps(build_payload(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def end_headers(self):
        # 禁用缓存，保证新增图片能立刻被前端刷出来
        try:
            self.send_header("Cache-Control", "no-store, must-revalidate")
        except Exception:
            pass
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


class ThreadedServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def write_manifest():
    """生成根目录 manifest.json（与 GitHub Actions 里 tools/build_manifest.py 输出一致）"""
    payload = build_payload()
    out = os.path.join(BASE_DIR, "manifest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("已生成 %s（共 %d 张图片）" % (out, payload["count"]))


def main():
    args = sys.argv[1:]
    if "--manifest" in args:
        write_manifest()
        return

    port = DEFAULT_PORT
    if "--port" in args:
        idx = args.index("--port")
        if idx + 1 < len(args):
            port = int(args[idx + 1])

    if not os.path.isdir(PIC_DIR):
        os.makedirs(PIC_DIR, exist_ok=True)

    photos = scan_photos()
    server = ThreadedServer(("0.0.0.0", port), LiveHandler)
    url = "http://localhost:%d/" % port
    print("=" * 60)
    print("  南武中学体育节图片直播 已启动")
    print("  访问地址：%s" % url)
    print("  图片目录：%s" % PIC_DIR)
    print("  当前图片：%d 张" % len(photos))
    print("  直接把新照片丢进 pic 文件夹，前端点刷新即可看到")
    print("  停止服务：按 Ctrl + C")
    print("=" * 60)

    if "--no-browser" not in args:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
