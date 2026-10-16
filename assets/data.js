/**
 * WorkBuddy 使用情况总结 - 数据源
 * 所有内容来自本地工作区、记忆日志、变更索引与发布记录的真实统计。
 */
window.REPORT_DATA = {
  meta: {
    owner: 'liangzaijwj2',
    generatedAt: '2026-10-16',
    period: '2026-10-14 ~ 2026-10-16',
    source: 'WorkBuddy 本地工作区 / 记忆日志 / 变更索引 / 发布记录'
  },
  overview: [
    { label: '完成任务会话', value: 2, unit: '个', desc: '产生了实际交付物' },
    { label: '累计产出代码', value: 3153, unit: '行', desc: '两个主项目合计' },
    { label: '交付文件', value: 12, unit: '份', desc: '代码 + 文档' },
    { label: '上线应用', value: 1, unit: '个', desc: '已部署可公网访问' },
    { label: '有效编码时长', value: 37, unit: '分钟', desc: '10-15 16:09 ~ 16:46' },
    { label: '使用天数', value: 3, unit: '天', desc: '10-14 首次启动' }
  ],
  timeline: [
    {
      date: '10-14 22:18',
      title: '首次启动 WorkBuddy',
      desc: '创建初始工作区 Claw，处于环境熟悉阶段，未产出实质内容。',
      tag: '起点'
    },
    {
      date: '10-15 16:09',
      title: 'B 站热门榜单实时网站开工',
      desc: '零依赖 Node.js 服务 + 原生前端，12 分钟内完成 4 个核心文件。',
      tag: '项目一'
    },
    {
      date: '10-15 16:15',
      title: '网站成功发布上线',
      desc: '经腾讯云 EdgeOne 部署，拿到公网访问地址，可直接在浏览器打开。',
      tag: '上线'
    },
    {
      date: '10-15 16:21',
      title: '域名绑定咨询与指南',
      desc: '希望绑定自有域名 jwj2662406042.com，经查证尚未注册，遂产出保姆级绑定指南。',
      tag: '追加'
    },
    {
      date: '10-15 16:37',
      title: '《星辰大陆物语》文字 RPG 开工',
      desc: '单文件 Python，一口气写完 1781 行的完整游戏系统。',
      tag: '项目二'
    },
    {
      date: '10-15 16:46',
      title: 'RPG 全流程测试通过',
      desc: '模拟输入跑通 创建角色 → 副本 → Boss → 商店 → 强化 → 孵宠 → 存读档，无报错，测试残留已清理。',
      tag: '完成'
    },
    {
      date: '10-16 17:39',
      title: '生成本使用总结网站',
      desc: '回顾全部历史任务，沉淀为可视化报告，并发布到 GitHub 仓库。',
      tag: '现在'
    }
  ],
  projects: [
    {
      name: 'B 站热门榜单实时网站',
      subtitle: 'bilibili-hot-ranking',
      time: '2026-10-15 16:09 ~ 16:21',
      duration: '约 12 分钟',
      status: '已上线',
      color: 'blue',
      stack: ['Node.js', 'HTML', 'CSS', 'JavaScript'],
      summary:
        '实时抓取并展示哔哩哔哩「热门」视频榜单的网站，包含完整的播放、点赞、投币、收藏、评论、弹幕、分享数据，带排名涨跌标记，并已部署上线可公网访问。',
      highlights: [
        '服务端 25 秒 TTL 缓存 + 并发请求去重，扛住频繁访问',
        '图片中转代理，绕过 Referer 防盗链，并设 SSRF 域名白名单防滥用',
        '前端 30 秒自动轮询，页面切到后台时自动暂停、切回自动恢复',
        'TOP 10 / 20 / 30 / 50 切换，5 种排序维度（榜单序 / 播放 / 点赞 / 收藏 / 评论）',
        'localStorage 快照对比，显示 NEW、↑n、↓n 排名涨跌',
        '热度分公式：播放 + 点赞×8 + 投币×10 + 收藏×10 + 评论×6 + 弹幕×3 + 分享×8',
        '并列拉取每位 UP 主粉丝数（10 分钟缓存，失败不阻断主流程）'
      ],
      files: [
        { name: 'server.js', lines: 346, desc: '接口代理 + 图片中转 + 静态托管' },
        { name: 'public/app.js', lines: 351, desc: '轮询 / 渲染 / 涨跌计算' },
        { name: 'public/style.css', lines: 336, desc: '样式与骨架屏' },
        { name: 'public/index.html', lines: 137, desc: '页面结构' },
        { name: 'README.md', lines: 80, desc: '使用与实现说明' },
        { name: '域名绑定指南.md', lines: 122, desc: '域名注册与 HTTPS 绑定教程' }
      ],
      online: 'https://bilibili-hot-top10.app.workbuddy.host/'
    },
    {
      name: '《星辰大陆物语》文字 RPG',
      subtitle: 'rpg_game.py',
      time: '2026-10-15 16:37 ~ 16:46',
      duration: '约 9 分钟',
      status: '已完成并通过测试',
      color: 'purple',
      stack: ['Python 3.14'],
      summary:
        '功能完备的单文件终端文字冒险 RPG，零第三方依赖，包含回合制战斗、副本、Boss、装备强化、宠物养成、商店、转盘与存档系统。',
      highlights: [
        '3 职业（战士 / 法师 / 游侠），各自独立的属性成长曲线',
        '15 个技能按等级解锁，涵盖伤害、减益、增益、多段、治疗 5 种类型',
        '6 大副本递进：微风草原 Lv1 → 亡者墓穴 → 毒雾沼泽 → 熔岩地心 → 无底深渊 → 星辰之巅 Lv48',
        '6 个专属 Boss，终局是 9000 HP 的「星辰吞噬者·尼德霍格」',
        '20 种小怪、36 件装备、5 档稀有度，强化 +1~+10 且 100% 成功',
        '10 种宠物，支持孵化、出战协同、觉醒与超进化',
        '商店、铁匠铺、旅馆、幸运转盘、JSON 存档读档一应俱全',
        'ANSI 彩色终端 UI：血条、分隔线面板、打字机剧情效果'
      ],
      contentScale: [
        { label: '职业', value: 3 },
        { label: '技能', value: 15 },
        { label: '副本', value: 6 },
        { label: 'Boss', value: 6 },
        { label: '小怪', value: 20 },
        { label: '装备', value: 36 },
        { label: '宠物', value: 10 }
      ],
      files: [
        { name: 'rpg_game.py', lines: 1781, desc: '全部游戏逻辑，单文件' },
        { name: 'rpg_save.json', lines: 37, desc: '存档（角色「靓仔」/ 法师 / Lv1）' }
      ],
      online: null
    }
  ],
  techStack: [
    { name: 'Python', lines: 1781, share: 56.5, note: '终端 RPG 游戏', color: '#6366f1' },
    { name: 'JavaScript', lines: 697, share: 22.1, note: '服务端 + 前端逻辑', color: '#0ea5e9' },
    { name: 'CSS', lines: 336, share: 10.7, note: '榜单站样式', color: '#14b8a6' },
    { name: 'Markdown', lines: 202, share: 6.4, note: 'README + 域名指南', color: '#f59e0b' },
    { name: 'HTML', lines: 137, share: 4.3, note: '页面结构', color: '#ec4899' }
  ],
  insights: [
    {
      icon: 'target',
      title: '要「能跑的完整成品」，不要 demo',
      desc: '榜单站要真实抓取、自动刷新、多维排序；RPG 要战斗、副本、Boss、强化、宠物一应俱全。交付标准是完整体验，而不是跑通一个示例。'
    },
    {
      icon: 'package',
      title: '偏爱零依赖、单文件、开箱即用',
      desc: 'Node 项目的 package.json 里没有任何 dependencies，全用原生 http / fs / path 手写；Python 游戏只导入标准库。降低环境成本是明确的偏好。'
    },
    {
      icon: 'heart',
      title: '游戏口味偏轻松爽快',
      desc: 'RPG 刻意做了低难度设计：怪物伤害低、逃跑 80% 成功、死亡仅损失 15% 金币、装备强化 100% 成功。追求正反馈，规避挫败感。'
    },
    {
      icon: 'rocket',
      title: '有真实上线与自有域名的诉求',
      desc: '不满足于本地跑通，主动推动部署公网访问，并希望绑定自有域名 jwj2662406042.com；对注册、备案、解析流程不熟悉，需要含价格与坑点的保姆级指引。'
    },
    {
      icon: 'zap',
      title: '产出密度极高',
      desc: '10-15 下午 37 分钟内产出 3153 行可用代码并完成一次上线部署，平均每分钟约 85 行，是一段高强度的集中使用。'
    }
  ],
  workspaces: [
    { name: 'Claw', created: '2026-10-14 22:18', status: '空壳', note: '首次启动时的初始工作区，未产出', tone: 'muted' },
    { name: 'workspace', created: '2026-10-15 16:09', status: '已上线', note: 'B 站热门榜单网站', tone: 'blue' },
    { name: 'game', created: '2026-10-15 16:37', status: '已完成', note: '星辰大陆物语 RPG', tone: 'purple' },
    { name: '2026-10-16-17-39-37', created: '2026-10-16 17:39', status: '进行中', note: '本总结网站', tone: 'green' }
  ]
};
