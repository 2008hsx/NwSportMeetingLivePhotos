#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 manifest.json（图片清单），彻底绕开浏览器的 API 配额限制。

为什么要它
----------
页面在浏览器里直接调 Gitee API 列目录时，走的是「匿名配额」，而且是按 IP 计算
（约 60 次/小时）。校园网 / 场馆 Wi-Fi 下所有人共用一个出口 IP，人一多配额立刻打满，
于是大家都看到 HTTP 403。

有了 manifest.json 之后，页面只需要读自己站点上的这一个静态文件，
一次 API 都不用调 —— 不会被限流，也不会跨域，速度还更快。

怎么用
------
1. 在本机运行：    python3 gen_manifest.py
2. 把生成的 manifest.json 上传到「放 index.html 的同一个目录」
   （GitHub Pages 的话就是仓库根目录）
3. 以后每次往 Gitee 的 pic/ 传完新照片，再跑一次本脚本并重新上传 manifest.json
   （或者直接用配套的 GitHub Actions 自动做这件事）

可选：在下面 TOKEN 里填 Gitee 私人令牌，配额会从 60 次/小时 提升到 5000 次/小时。
      令牌获取：Gitee 头像 → 设置 → 私人令牌 → 生成新令牌（只勾读权限即可）。
"""

import json
import re
import time
import urllib.parse
import urllib.request

# ====== 按你的仓库改这里 ==========================================
OWNER = "huangsongxi2008"
REPO = "nw-sport-meeting-live-photos"
BRANCH = "master"
PIC_DIR = "pic"
TOKEN = ""          # 可留空；填了能大幅提高配额
OUT_FILE = "manifest.json"
# =================================================================

IMAGE_EXT = re.compile(r"\.(jpe?g|png|gif|webp|bmp|avif|jfif|heic)$", re.I)
UA = {"User-Agent": "Mozilla/5.0 (manifest-builder)", "Accept": "application/json"}


def api(path):
    url = "https://gitee.com/api/v5/repos/%s/%s/%s" % (OWNER, REPO, path)
    if TOKEN:
        url += ("&" if "?" in url else "?") + "access_token=" + TOKEN
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def raw_url(path):
    # 原图直链：页面会用 referrerPolicy=no-referrer 去取，不受防盗链影响
    quoted = "/".join(urllib.parse.quote(s, safe="") for s in path.split("/"))
    return "https://gitee.com/%s/%s/raw/%s/%s" % (OWNER, REPO, BRANCH, quoted)


def iso_to_ts(s):
    try:
        return int(time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")))
    except Exception:
        return 0


def main():
    # 1) 列出 pic/ 下所有文件
    files, page = [], 1
    while page <= 20:
        data = api("contents/%s?ref=%s&page=%d&per_page=100" % (PIC_DIR, BRANCH, page))
        if not isinstance(data, list) or not data:
            break
        files += data
        if len(data) < 100:
            break
        page += 1
    print("目录里有 %d 个条目" % len(files))

    # 2) 用提交记录补「拍摄/上传时间」（查不到也能用，只是排序会退回按文件名）
    dates = {}
    try:
        commits = api("commits?sha=%s&path=%s&per_page=20" % (BRANCH, PIC_DIR))
        for c in commits:
            ts = iso_to_ts((c.get("commit") or {}).get("committer", {}).get("date", ""))
            if not ts:
                continue
            try:
                detail = api("commits/%s" % c["sha"])
            except Exception:
                continue
            for f in detail.get("files", []) or []:
                dates.setdefault(f.get("filename"), ts)
    except Exception as e:
        print("提交时间获取失败（忽略，排序会退回按文件名）：", e)

    # 3) 组装清单
    items = []
    for f in files:
        if f.get("type") != "file":
            continue
        name = f.get("name", "")
        if not IMAGE_EXT.search(name):
            continue
        path = f.get("path") or (PIC_DIR + "/" + name)
        ts = dates.get(path, 0)
        items.append({
            "name": name,
            "url": raw_url(path),          # 绝对地址：页面放哪个站点都能用
            "mtime": ts,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "",
            "path": path,
        })

    items.sort(key=lambda x: (x["mtime"], x["name"]), reverse=True)

    payload = {
        "count": len(items),
        "photos": items,
        "scanTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "updated": int(time.time()),
    }
    with open(OUT_FILE, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, separators=(",", ":"))

    print("已生成 %s：共 %d 张图片" % (OUT_FILE, len(items)))
    for it in items[:5]:
        print("   %s  %s" % (it["time"] or "(无时间)", it["name"]))
    print("\n下一步：把 %s 上传到放 index.html 的同一个目录即可。" % OUT_FILE)


if __name__ == "__main__":
    main()
