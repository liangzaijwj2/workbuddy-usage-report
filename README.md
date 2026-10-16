# WorkBuddy 使用情况总结

一份回顾我（GitHub: `liangzaijwj2`）使用 WorkBuddy 全过程的可视化报告网站。

统计区间：**2026-10-14 ~ 2026-10-16**

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
| 时间线 | 从首次启动到本次总结，7 个关键节点 |
| 项目详情 | 两个完整项目的实现亮点、文件清单、内容体量 |
| 技术栈 | 按代码行数拆分的环形图与条形图 |
| 使用画像 | 从任务取舍中读出的 5 条使用偏好 |
| 工作区清单 | 所有被创建过的工作区及状态 |

## 被统计的两个项目

1. **B 站热门榜单实时网站** — 零依赖 Node.js + 原生前端，实时抓取并展示 B 站热门榜，含排名涨跌、多维度排序，已部署上线。
2. **《星辰大陆物语》文字 RPG** — 单文件 Python（1781 行，零第三方依赖），含 3 职业、15 技能、6 副本、6 Boss、36 装备、10 宠物。

## 数据来源

全部取自本机真实记录，不做估算：

- `~/WorkBuddy/*` 各工作区的产出文件
- `.workbuddy/memory/*.md` 每日记忆日志
- `~/.workbuddy/changes-index/*.json` 变更索引
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
└── assets/
    ├── style.css
    ├── app.js
    └── data.js      ← 报告数据源，改这里
```
