# 广州市南武中学2026年陈彦健康体育节校本部图片直播

部署在 GitHub Pages 的静态图片直播站：**照片往仓库的 `pic/` 文件夹一推，页面自动显示，无需手动选择文件夹、无需改代码。**

## 一、目录结构

```
仓库根目录/
├── index.html                          ← 直播页面（封面 + 密码 + 两列图片流）
├── manifest.json                       ← 图片清单（GitHub Actions 自动生成，不用手改）
├── .nojekyll                           ← 跳过 Jekyll 编译，部署更快
├── pic/                                ← ★ 照片放这里（demo_01~06 为示例图，正式用前删掉）
├── tools/build_manifest.py             ← 生成清单的脚本（Actions 调用）
├── server.py                           ← 可选：本地预览用
└── .github/workflows/update-manifest.yml ← 推送照片后自动生成清单
```

## 二、部署步骤（一次性，约 5 分钟）

1. 在 GitHub 新建仓库（例如 `nanwu-sports-2026`，**设为 Public**）
2. 把本文件夹里的**全部内容**（含 `.github`、`.nojekyll`）上传到仓库
   - 网页上传：直接拖拽（`.github` 这类隐藏文件建议用下面的命令行方式）
   - 命令行：`git init` → `git add -A` → `git commit -m init` → `git remote add origin ...` → `git push -u origin main`
3. 进入仓库 **Settings → Pages → Build and deployment**
   - Source 选 **Deploy from a branch**
   - Branch 选 **main** / 目录 `/ (root)` → Save
4. 等 1～2 分钟，访问 `https://<用户名>.github.io/<仓库名>/` 即可

## 三、日常使用：赛程中如何更新照片

在仓库网页上打开 `pic/` 文件夹 → **Add file → Upload files** → 拖入照片 → Commit changes。

之后全自动：

1. 推送触发 Actions「更新图片清单」，扫描 `pic/` 并生成 `manifest.json` 提交回仓库
2. GitHub Pages 自动重新部署（约 1～3 分钟）
3. 观众端页面 **每 60 秒自动刷新**一次，也可手动点「刷新」或按 `R` 键

> 照片数量、顺序完全由 `pic/` 里的内容决定，加多少张就显示多少张，**不用改任何代码**。

## 四、页面功能

| 项目 | 说明 |
|---|---|
| 封面页 | 标题正上方居中，点「进入直播」弹出密码框 |
| 访问密码 | `nanwuXYH2026`（源码里只存 SHA-256 值，明文不暴露） |
| 图片来源 | 自动读取仓库 `pic/` 文件夹，**无手动选文件夹步骤** |
| 显示框 | 固定 **16:9 横屏**，`object-fit: contain`——照片自动缩放完整放进框内，竖图的留白用同图模糊填充，不裁人头 |
| 布局 | 左右两列，按时间顺序 #1 左 / #2 右 / #3 左 … 交替，右上角显示序号 |
| 排列顺序 | 按图片**修改时间从新到旧**（`order: "asc"` 可反转） |
| 查看大图 | 单击任意照片打开灯箱，支持 ‹ › 按钮、左右方向键翻页、ESC 关闭 |
| 刷新方式 | 「刷新」按钮 / `R` 键 / `F5` / 手机下拉 / 每 60 秒自动 / 切回页面自动 |
| 新照片 | 后刷出来的照片带红色「新」角标和金边，顶部提示本次新增数量 |

## 五、可调参数（index.html 顶部 CONFIG）

```js
password:     "nanwuXYH2026",  // 改密码时同步改 passwordHash（新密码的 SHA-256 小写 64 位）
order:        "desc",          // desc=最新在最上面；asc=最早在最上面
fit:          "contain",       // contain=完整显示（默认）；cover=裁切填满 16:9
aspect:       "16 / 9",        // 显示框比例，可改 "4 / 3"、"1 / 1"
autoInterval: 60000,           // 自动刷新间隔（毫秒）
```

封面大标题：搜索 `广州市南武中学2026年陈彦健康体育节校本部图片直播`（`<title>` 与封面 `<h1>` 两处）。

## 六、注意事项

- **正式使用前删除 `pic/` 里的 `demo_01.jpg` ~ `demo_06.jpg`**
- 照片建议先压缩到单张 2MB 以内（手机原图动辄 5MB，几十张就会拖慢加载）；仓库总大小控制在 1GB 内
- 上传到 `pic/` 后若页面没更新：先在仓库 **Actions** 页看任务是否跑完（绿色 ✓），再点页面「刷新」；Pages 部署通常 1～3 分钟
- 这是公开静态站，密码只是**前端门槛**（防止随手转发，非强安全）。若照片涉及学生肖像，建议仅在家长群内发布链接，并遵守学校肖像权相关规定
- 本地预览（可选，不上传也能看效果）：`python3 server.py` 后访问 `http://localhost:8000`
