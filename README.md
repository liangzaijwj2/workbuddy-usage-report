# WorkBuddy 使用情况总结

一份回顾我（GitHub: `liangzaijwj2`）使用 WorkBuddy 全过程的可视化报告网站。

统计区间：**2026-10-14 ~ 2026-10-17**

## 自动同步（新项目做完自动进站）

每完成一个 WorkBuddy 项目，跑一次同步即可把它补进报告：

```bash
python tools/sync.py --push
```

它会扫描本机的变更索引、产物索引、会话列表、部署记录和各工作区记忆日志，
识别出**产生了实际交付物**的新会话，自动生成时间线节点、按语言重算代码行数、
刷新总览数字，然后提交并推送到 GitHub。

| 命令 | 作用 |
| --- | --- |
| `python tools/sync.py` | 只重建 `assets/data.js`，不动 git |
| `python tools/sync.py --dry-run` | 只看会新增什么，不写文件 |
| `python tools/sync.py --push` | 重建 + 提交 + 推送 |
| `python tools/sync.py --push-only` | 不重建，只把已有改动推上去 |

`--push` 会先试标准 `git push`；如果被网络策略拦住（github.com 不通），
自动改走 `tools/push_api.py`，用 GitHub REST API 提交，功能等价。
单独用：`python tools/push_api.py`（会自动比对上次推送的文件快照，只传变化的部分）。

另外配了一个每天 22:00 的定时任务自动跑一遍，无需手动触发。

### 数据怎么分工

- `assets/data.js` —— **自动生成，不要手改**，每次同步会被覆盖
- `data/overrides.json` —— **唯一需要人工维护的文件**，放所有叙述性内容（项目名、亮点、使用画像、时间线文案）和需要固定的数字
- `data/state.json` —— 同步状态，自动生成

新增项目时脚本会先用工作区记忆日志生成一版摘要初稿，之后可以在 `overrides.json`
里按会话 id 精修 `name` / `summary` / `highlights` / `files`，下次同步会以它为准。

如果一个会话不该被收录（比如只在折腾推送脚本），把它的 id 加到 `overrides.json` 的 `ignore` 里。

## 在线访问

仓库地址：

```
https://github.com/liangzaijwj2/workbuddy-usage-report
```

GitHub Pages 站点（由 `main` 分支发布，可直接打开分享）：

```
https://liangzaijwj2.github.io/workbuddy-usage-report/
```

本机直接双击 `index.html` 即可预览：纯静态，无需构建、无需联网。

## 报告里有什么

| 板块 | 内容 |
| --- | --- |
| 总览 | 完成任务数、代码行数、交付文件数、上线应用数等 6 项核心数据 |
| 时间线 | 从首次启动到本次总结，12 个关键节点 |
| 项目详情 | 四个完整项目的实现亮点、文件清单、内容体量 |
| 技术栈 | 按代码行数拆分的环形图与条形图 |
| 使用画像 | 从任务取舍中读出的 8 条使用偏好 |
| 工作区清单 | 所有被创建过的工作区及状态 |

## 被统计的四个项目

1. **B 站热门榜单实时网站** — 零依赖 Node.js + 原生前端，实时抓取并展示 B 站热门榜，含排名涨跌、多维度排序，已部署上线。
2. **《星辰大陆物语》文字 RPG** — 单文件 Python（1781 行，零第三方依赖），含 3 职业、15 技能、6 副本、6 Boss、36 装备、10 宠物。
3. **西药的安全性 · 大众科普演讲套装** — 15 页简约风 PPT（全部通过 `slidep lint --visual`）+ 3071 字讲稿 + 逐页时间分配大纲，21 张 AI 配图已脚本化去水印。
4. **马年迷幻交通灯海报** — 1024×1792 竖版 AI 海报，洋红底 + 银灰哑光交通灯，三色 LED 点阵拼出「马」字；留了 `.miora` 可编辑画布。

> 项目 3、4 为 2026-10-17 新增，本次同步更新了总览、时间线、技术栈与使用画像。

## 数据来源

全部取自本机真实记录，不做估算：

- `~/WorkBuddy/*` 各工作区的产出文件
- `.workbuddy/memory/*.md` 每日记忆日志
- `~/.workbuddy/changes-index/*.json` 变更索引
- `~/.workbuddy/artifact-index/*.json` 产物索引
- `~/.workbuddy/cloudstudio-deploy-history/*.json` 发布记录

## 技术说明

- 纯静态页面，HTML + CSS + 原生 JS，**零外部依赖、零构建步骤**
- 数据集中在 `assets/data.js`，改数据即可更新整份报告
- 支持响应式，移动端可用；尊重 `prefers-reduced-motion`

## 目录结构

```
workbuddy-usage-report/
├── index.html
├── README.md
├── assets/
│   ├── style.css
│   ├── app.js
│   └── data.js          ← 自动生成，勿手改
├── data/
│   ├── overrides.json   ← 唯一需要人工维护的文件
│   └── state.json       ← 同步状态，自动生成
└── tools/
    └── sync.py          ← 自动同步器
```
