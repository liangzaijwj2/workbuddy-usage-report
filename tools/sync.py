#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy 使用情况报告 · 自动同步器

扫描本机 WorkBuddy 的真实记录，把新完成的项目自动补进报告网站。

数据源：
  ~/.workbuddy/changes-index/*.json              会话级文件变更（含增删行数）
  ~/.workbuddy/artifact-index/*.json             会话产物（PPT / 图片 / 画布等）
  ~/.workbuddy/<uid>/sidebar-list-snapshot.json  会话标题与所属工作区
  ~/.workbuddy/cloudstudio-deploy-history/*.json 上线部署记录
  ~/WorkBuddy/*/.workbuddy/memory/*.md           每日记忆日志（用于生成摘要初稿）

用法：
  python tools/sync.py              扫描并重建 assets/data.js
  python tools/sync.py --dry-run    只看会新增什么，不写文件
  python tools/sync.py --push       重建后 git commit 并尝试 push
  python tools/sync.py --push-only  不重建，只把已有改动推上去

设计约定：
  data/overrides.json 是唯一需要人工（或 AI）维护的文件，存放所有叙述性内容
  与需要固定的数字。其余全部由本脚本从本机记录自动派生。
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_DIR = ROOT / "data"
OVERRIDES = DATA_DIR / "overrides.json"
STATE = DATA_DIR / "state.json"
OUTPUT = ROOT / "assets" / "data.js"

HOME = Path.home()
WB_HOME = HOME / ".workbuddy"
WB_ROOT = HOME / "WorkBuddy"

# 二进制 / 非文本产物：按体积展示，不计入代码行数
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico",
    ".pptx", ".ppt", ".docx", ".doc", ".xlsx", ".xls", ".pdf",
    ".zip", ".rar", ".7z", ".mp4", ".mp3", ".miora", ".ttf", ".woff", ".woff2",
}

LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".css": "CSS", ".scss": "CSS",
    ".html": "HTML", ".htm": "HTML", ".md": "Markdown", ".slide": "Slide DSL",
    ".json": "JSON", ".sh": "Shell", ".bat": "Shell", ".ps1": "PowerShell",
    ".go": "Go", ".java": "Java", ".rs": "Rust", ".vue": "Vue",
}

LANG_COLOR = {
    "Python": "#6366f1", "JavaScript": "#0ea5e9", "TypeScript": "#3178c6",
    "CSS": "#22c55e", "HTML": "#ec4899", "Markdown": "#f59e0b",
    "Slide DSL": "#14b8a6", "JSON": "#94a3b8", "Shell": "#64748b",
    "PowerShell": "#64748b", "Go": "#00add8", "Java": "#f89820",
    "Rust": "#dea584", "Vue": "#42b883",
}

# 这些路径里的文件是 WorkBuddy 自身产物，不算用户交付物
EXCLUDE_PARTS = {
    ".workbuddy", ".git", "node_modules", ".venv", "venv", "__pycache__",
    ".slidep", ".cache", ".idea", ".vscode", "dist", "build", ".next",
}

PROJECT_COLORS = ["blue", "purple", "teal", "amber", "green", "muted"]
TONE_CYCLE = ["blue", "purple", "teal", "amber", "green"]


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def log(msg):
    print(msg, flush=True)


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else None


def ts_to_dt(ms):
    if not ms:
        return None
    try:
        return dt.datetime.fromtimestamp(ms / 1000)
    except Exception:
        return None


def fmt_dt(d, with_year=False):
    if not d:
        return ""
    return d.strftime("%Y-%m-%d %H:%M") if with_year else d.strftime("%m-%d %H:%M")


def count_lines(path):
    try:
        with open(path, "rb") as f:
            return f.read().count(b"\n") + (0 if f.read() else 1)
    except Exception:
        return None


def human_size(nbytes):
    if nbytes is None:
        return "—"
    if nbytes < 1024:
        return "%d B" % nbytes
    if nbytes < 1024 * 1024:
        return "%.0f KB" % (nbytes / 1024)
    return "%.1f MB" % (nbytes / (1024 * 1024))


def is_excluded(path_str):
    low = path_str.replace("\\", "/").lower()
    parts = low.split("/")
    for p in parts:
        if p in EXCLUDE_PARTS:
            return True
    # 记忆日志不算交付物
    if "/.workbuddy/memory/" in low:
        return True
    return False


def rel_name(path_str):
    """把绝对路径压缩成项目内相对名，用于展示。"""
    p = path_str.replace("\\", "/")
    for marker in ("/WorkBuddy/", "/Documents/GitHub/"):
        if marker in p:
            tail = p.split(marker, 1)[1]
            seg = tail.split("/")
            # 去掉工作区目录名（第一层）
            return "/".join(seg[1:]) if len(seg) > 1 else tail
    return p.split("/")[-1]


# --------------------------------------------------------------------------
# 采集
# --------------------------------------------------------------------------
def collect_sessions():
    """汇总所有会话的元信息、文件变更与产物。"""
    sessions = {}

    # 1) 会话标题 + 工作区
    for snap in WB_HOME.glob("*/sidebar-list-snapshot.json"):
        data = load_json(snap, {})
        for item in data.get("items") or []:
            sid = item.get("id")
            if not sid:
                continue
            s = sessions.setdefault(sid, {"id": sid, "files": {}, "artifacts": {},
                                          "first": None, "last": None, "additions": 0})
            s["title"] = item.get("title") or s.get("title") or sid[:8]
            space = (item.get("space") or {}).get("name") or ""
            if space:
                s["workspace"] = space.replace("\\", "/")
            for key in ("lastActivityAt", "updatedAt"):
                d = ts_to_dt(item.get(key))
                if d:
                    s["last"] = max(s["last"], d) if s["last"] else d

    # 2) 文件变更
    for idx in (WB_HOME / "changes-index").glob("*.json"):
        data = load_json(idx, {})
        for ch in data.get("changes") or []:
            sid = ch.get("conversationId") or idx.stem
            s = sessions.setdefault(sid, {"id": sid, "files": {}, "artifacts": {},
                                          "first": None, "last": None, "additions": 0})
            when = ts_to_dt(ch.get("createdAt"))
            if when:
                s["first"] = min(s["first"], when) if s["first"] else when
                s["last"] = max(s["last"], when) if s["last"] else when
            for f in ch.get("files") or []:
                fp = f.get("filePath") or ""
                if not fp or is_excluded(fp):
                    continue
                rec = s["files"].setdefault(fp, {
                    "path": fp, "action": f.get("action", "modify"),
                    "additions": 0, "deletions": 0, "at": None,
                })
                rec["additions"] = max(rec["additions"], f.get("additions") or 0)
                rec["action"] = f.get("action", rec["action"])
                if when:
                    rec["at"] = max(rec["at"], when) if rec["at"] else when
            s["additions"] += ch.get("additions") or 0

    # 3) 产物（PPT / 图片 / 画布等）
    for idx in (WB_HOME / "artifact-index").glob("*.json"):
        sid = idx.stem
        data = load_json(idx, {})
        for a in data.get("artifacts") or []:
            uri = a.get("uri") or ""
            if not uri or uri.startswith("file:///") is False:
                continue
            fp = uri[len("file:///"):]
            fp = fp.replace("%20", " ")
            try:
                from urllib.parse import unquote
                fp = unquote(fp)
            except Exception:
                pass
            if is_excluded(fp):
                continue
            s = sessions.setdefault(sid, {"id": sid, "files": {}, "artifacts": {},
                                          "first": None, "last": None, "additions": 0})
            when = ts_to_dt(a.get("createdAt"))
            if when:
                s["first"] = min(s["first"], when) if s["first"] else when
                s["last"] = max(s["last"], when) if s["last"] else when
            s["artifacts"][fp] = {
                "path": fp,
                "name": a.get("name") or Path(fp).name,
                "size": a.get("size"),
                "type": a.get("contentType") or "",
                "at": when,
            }

    # 4) 上线记录
    deploys = []
    dh = WB_HOME / "cloudstudio-deploy-history"
    if dh.exists():
        for f in dh.glob("*.json"):
            d = load_json(f, {})
            if not d:
                continue
            deploys.append({
                "sid": d.get("taskSessionId") or d.get("conversationId"),
                "title": d.get("title"),
                "url": d.get("shareLink"),
                "at": ts_to_dt(d.get("createdTimestamp")),
            })
    return sessions, deploys


def collect_memory():
    """读取各工作区的每日记忆日志，用于给新项目生成摘要初稿。"""
    notes = {}
    if not WB_ROOT.exists():
        return notes
    for ws in WB_ROOT.iterdir():
        if not ws.is_dir():
            continue
        for md in (ws / ".workbuddy" / "memory").glob("*.md"):
            try:
                notes[ws.name] = md.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass
    return notes


# --------------------------------------------------------------------------
# 构建
# --------------------------------------------------------------------------
def build_file_entries(sess):
    """合并文件变更与产物，生成展示用的文件清单。"""
    entries = []
    seen = set()

    for path, rec in sorted(sess["files"].items(),
                            key=lambda kv: kv[1].get("at") or dt.datetime.min):
        ext = Path(path).suffix.lower()
        key = path.lower()
        if key in seen:
            continue
        seen.add(key)
        if ext in BINARY_EXT:
            size = None
            try:
                size = os.path.getsize(path)
            except Exception:
                pass
            entries.append({
                "name": rel_name(path), "size": human_size(size),
                "desc": "二进制产物", "_lines": 0, "_lang": None, "_at": rec.get("at"),
            })
            continue
        lines = count_lines(path)
        if lines is None:
            lines = rec.get("additions") or 0
        entries.append({
            "name": rel_name(path), "lines": lines,
            "desc": "源文件", "_lines": lines, "_lang": LANG_MAP.get(ext),
            "_at": rec.get("at"),
        })

    for path, art in sorted(sess["artifacts"].items(),
                            key=lambda kv: kv[1].get("at") or dt.datetime.min):
        key = path.lower()
        if key in seen:
            continue
        seen.add(key)
        entries.append({
            "name": rel_name(path), "size": human_size(art.get("size")),
            "desc": "交付产物", "_lines": 0, "_lang": None, "_at": art.get("at"),
        })
    return entries


def summarize_from_memory(sess, memory):
    """从工作区记忆日志里抓一段作为项目摘要初稿。"""
    ws = sess.get("workspace") or ""
    ws_name = ws.rstrip("/").split("/")[-1] if ws else ""
    text = memory.get(ws_name, "")
    if not text:
        return "", []
    title = (sess.get("title") or "").strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # 找到提到该项目的段落
    anchor = -1
    for i, l in enumerate(lines):
        if l.startswith("#") and title and (title[:6] in l or l.strip("# ").startswith(title[:6])):
            anchor = i
            break
    if anchor < 0:
        for i, l in enumerate(lines):
            if l.startswith("#") and "工作日志" not in l:
                anchor = i
                break
    if anchor < 0:
        anchor = 0
    chunk = []
    for l in lines[anchor: anchor + 22]:
        if l.startswith("|---") or l.startswith("| :"):
            continue
        chunk.append(l.lstrip("- ").strip())
    summary = " ".join(chunk)[:220].strip()
    highlights = [c for c in chunk if len(c) > 12][:5]
    return summary, highlights


def build(sessions, deploys, memory, ov):
    ignore = set(ov.get("ignore") or [])
    ov_projects = ov.get("projects") or {}
    ov_ws = ov.get("workspaces") or {}

    # --- 筛选有效项目 ---
    projects = []
    for sid, s in sessions.items():
        if sid in ignore:
            continue
        entries = build_file_entries(sess=s)
        alive = [e for e in entries if (e.get("lines") or e.get("size"))]
        code_lines = sum(e["_lines"] for e in entries)
        # 判定：有存活产物，或代码量够大
        if not alive or (code_lines < 20 and len(alive) < 2):
            continue
        title = s.get("title") or sid[:8]
        first, last = s.get("first"), s.get("last")
        if not first and last:
            first = last
        if not last and first:
            last = first
        if not first or not last:
            continue
        deploy = next((d for d in deploys if d.get("sid") == sid and d.get("url")), None)

        auto_summary, auto_highlights = summarize_from_memory(s, memory)

        p = {
            "name": title,
            "subtitle": (s.get("workspace") or "").rstrip("/").split("/")[-1] or sid[:8],
            "time": "%s ~ %s" % (fmt_dt(first, True), fmt_dt(last, True)),
            "duration": human_duration(first, last),
            "status": "已交付",
            "color": None,
            "stack": sorted({e["_lang"] for e in entries if e.get("_lang")}),
            "summary": auto_summary or "由 WorkBuddy 完成于 %s。" % fmt_dt(first, True),
            "highlights": auto_highlights,
            "files": [{k: v for k, v in e.items() if not k.startswith("_")} for e in entries],
            "online": deploy["url"] if deploy else None,
            "_sid": sid,
            "_first": first,
            "_last": last,
            "_entries": entries,
        }
        if deploy:
            p["status"] = "已上线"
        # 人工覆盖（含已有项目）
        manual = ov_projects.get(sid) or {}
        for k, v in manual.items():
            if k in ("name", "subtitle", "time", "duration", "status", "color",
                     "stack", "summary", "highlights", "contentScale", "files", "online"):
                p[k] = v
        if not p.get("color"):
            p["color"] = PROJECT_COLORS[len(projects) % len(PROJECT_COLORS)]
        projects.append(p)

    def sort_key(p):
        t = (p.get("time") or "").split(" ~ ")[0].strip()
        try:
            return dt.datetime.strptime(t, "%Y-%m-%d %H:%M")
        except Exception:
            return p["_first"] or dt.datetime.max

    projects.sort(key=sort_key)

    # --- 统计口径 ---
    # 使用天数 / 统计区间：以工作区目录创建时间为准，把没产出的工作区也算进去
    ws_days = []
    if WB_ROOT.exists():
        for d in WB_ROOT.iterdir():
            if d.is_dir():
                ws_days.append(dt.datetime.fromtimestamp(d.stat().st_ctime).date())
    all_days = set(ws_days) | {(p["_first"].date()) for p in projects}
    first_day = min(all_days) if all_days else None
    last_day = max(all_days) if all_days else None

    # 累计投入时长：优先用手工写的 duration，拿不到再退回首尾时间差
    minutes = 0
    for p in projects:
        d = parse_duration(p.get("duration"))
        if d is None and p["_first"] and p["_last"]:
            d = max(1, int((p["_last"] - p["_first"]).total_seconds() // 60))
        minutes += d or 0

    # --- techStack ---
    if ov.get("techStack"):
        stack = ov["techStack"]
    else:
        agg = {}
        for p in projects:
            for e in p["_entries"]:
                lang = e.get("_lang")
                if lang and e.get("_lines"):
                    agg[lang] = agg.get(lang, 0) + e["_lines"]
        total = sum(agg.values()) or 1
        stack = []
        for i, (lang, lines) in enumerate(sorted(agg.items(), key=lambda kv: -kv[1])):
            stack.append({
                "name": lang, "lines": lines,
                "share": round(lines * 100.0 / total, 1),
                "note": "", "color": LANG_COLOR.get(lang, "#94a3b8"),
            })
        if stack:
            stack[-1]["share"] = round(100.0 - sum(s["share"] for s in stack[:-1]), 1)

    total_lines = sum(s["lines"] for s in stack)

    # --- overview ---
    n_files = sum(len(p["files"]) for p in projects)
    n_online = sum(1 for p in projects if p.get("online"))

    meta = {
        "owner": ov.get("meta", {}).get("owner", "liangzaijwj2"),
        "generatedAt": dt.datetime.now().strftime("%Y-%m-%d"),
        "period": "%s ~ %s" % (first_day, last_day) if first_day else "",
        "source": "WorkBuddy 本地工作区 / 记忆日志 / 变更索引 / 产物索引 / 部署记录",
    }

    overview = [
        {"label": "完成任务会话", "value": len(projects), "unit": "个", "desc": "均产生实际交付物"},
        {"label": "累计产出代码", "value": total_lines, "unit": "行", "desc": "全部项目合计"},
        {"label": "交付文件", "value": n_files, "unit": "份", "desc": "代码 + 文档 + 设计稿"},
        {"label": "上线应用", "value": n_online, "unit": "个", "desc": "已部署可公网访问"},
        {"label": "累计投入时长", "value": minutes, "unit": "分钟", "desc": "各项目首尾时间合计"},
        {"label": "使用天数", "value": len(all_days), "unit": "天", "desc": "含未产出的工作区"},
    ]

    # --- timeline（手工条目 + 自动追加新项目）---
    timeline = list(ov.get("timeline") or [])
    known = {(t.get("sid"), t.get("kind")) for t in timeline if t.get("sid")}
    for p in projects:
        sid = p["_sid"]
        # 默认只补「开工」和「上线」两个节点；「完成」信息量低且容易与手工条目重复
        kinds = set((ov_projects.get(sid) or {}).get("autoTimeline", ["start", "online"]))
        if "start" in kinds and (sid, "start") not in known:
            timeline.append({
                "date": fmt_dt(p["_first"]),
                "title": "%s 开工" % p["name"],
                "desc": (p.get("summary") or "")[:90],
                "tag": "新项目", "sid": sid, "kind": "start",
            })
        if "online" in kinds and p.get("online") and (sid, "online") not in known:
            d = next((x for x in deploys if x.get("sid") == sid), None)
            timeline.append({
                "date": fmt_dt(d["at"]) if d and d.get("at") else fmt_dt(p["_last"]),
                "title": "%s 发布上线" % p["name"],
                "desc": "部署完成，可公网访问：%s" % p["online"],
                "tag": "上线", "sid": sid, "kind": "online",
            })
        if "done" in kinds and p["_last"] != p["_first"] and (sid, "done") not in known:
            timeline.append({
                "date": fmt_dt(p["_last"]),
                "title": "%s 交付完成" % p["name"],
                "desc": "最后一批产物落盘，项目收尾。",
                "tag": "完成", "sid": sid, "kind": "done",
            })
    timeline.sort(key=lambda t: t.get("date") or "")

    # --- workspaces ---
    workspaces = []
    if WB_ROOT.exists():
        dirs = sorted([d for d in WB_ROOT.iterdir() if d.is_dir()],
                      key=lambda d: d.stat().st_ctime)
        for i, d in enumerate(dirs):
            created = dt.datetime.fromtimestamp(d.stat().st_ctime)
            has_output = any(True for c in d.iterdir() if c.name != ".workbuddy")
            manual = ov_ws.get(d.name) or {}
            workspaces.append({
                "name": d.name,
                "created": created.strftime("%Y-%m-%d %H:%M"),
                "status": manual.get("status") or ("已交付" if has_output else "空壳"),
                "note": manual.get("note") or "",
                "tone": manual.get("tone") or TONE_CYCLE[i % len(TONE_CYCLE)],
            })

    for p in projects:
        p.pop("_sid", None); p.pop("_first", None); p.pop("_last", None)
        p.pop("_entries", None)

    return {
        "meta": meta, "overview": overview, "timeline": timeline,
        "projects": projects, "techStack": stack,
        "insights": ov.get("insights") or [], "workspaces": workspaces,
    }


def human_duration(a, b):
    if not a or not b:
        return ""
    mins = max(1, int((b - a).total_seconds() // 60))
    if mins < 60:
        return "约 %d 分钟" % mins
    return "约 %d 小时 %d 分钟" % (mins // 60, mins % 60)


def parse_duration(s):
    """把「约 1 小时 53 分钟」这类手工文案解析成分钟数。"""
    if not s:
        return None
    mh = re.search(r"(\d+)\s*小时", s)
    mm = re.search(r"(\d+)\s*分钟", s)
    if not (mh or mm):
        return None
    return (int(mh.group(1)) * 60 if mh else 0) + (int(mm.group(1)) if mm else 0)


# --------------------------------------------------------------------------
# 输出
# --------------------------------------------------------------------------
def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def render(data):
    L = []
    L.append("/**")
    L.append(" * WorkBuddy 使用情况总结 - 数据源")
    L.append(" * 本文件由 tools/sync.py 自动生成，请勿手改。")
    L.append(" * 需要人工维护的内容请写到 data/overrides.json 后重跑同步。")
    L.append(" * 生成时间：%s" % dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
    L.append(" */")
    L.append("window.REPORT_DATA = {")

    m = data["meta"]
    L.append("  meta: {")
    L.append("    owner: %s," % js_str(m["owner"]))
    L.append("    generatedAt: %s," % js_str(m["generatedAt"]))
    L.append("    period: %s," % js_str(m["period"]))
    L.append("    source: %s" % js_str(m["source"]))
    L.append("  },")

    L.append("  overview: [")
    for s in data["overview"]:
        L.append("    { label: %s, value: %s, unit: %s, desc: %s },"
                 % (js_str(s["label"]), s["value"], js_str(s["unit"]), js_str(s["desc"])))
    L.append("  ],")

    L.append("  timeline: [")
    for t in data["timeline"]:
        L.append("    {")
        L.append("      date: %s," % js_str(t.get("date", "")))
        L.append("      title: %s," % js_str(t.get("title", "")))
        L.append("      desc: %s," % js_str(t.get("desc", "")))
        L.append("      tag: %s" % js_str(t.get("tag", "")))
        L.append("    },")
    L.append("  ],")

    L.append("  projects: [")
    for p in data["projects"]:
        L.append("    {")
        L.append("      name: %s," % js_str(p["name"]))
        L.append("      subtitle: %s," % js_str(p["subtitle"]))
        L.append("      time: %s," % js_str(p["time"]))
        L.append("      duration: %s," % js_str(p["duration"]))
        L.append("      status: %s," % js_str(p["status"]))
        L.append("      color: %s," % js_str(p["color"]))
        L.append("      stack: [%s]," % ", ".join(js_str(x) for x in p["stack"]))
        L.append("      summary: %s," % js_str(p["summary"]))
        L.append("      highlights: [")
        for h in p["highlights"]:
            L.append("        %s," % js_str(h))
        L.append("      ],")
        if p.get("contentScale"):
            L.append("      contentScale: [")
            for c in p["contentScale"]:
                L.append("        { label: %s, value: %s },"
                         % (js_str(c["label"]), c["value"]))
            L.append("      ],")
        L.append("      files: [")
        for f in p["files"]:
            bits = ["name: %s" % js_str(f["name"])]
            if "size" in f:
                bits.append("size: %s" % js_str(f["size"]))
            else:
                bits.append("lines: %s" % f.get("lines", 0))
            bits.append("desc: %s" % js_str(f.get("desc", "")))
            L.append("        { %s }," % ", ".join(bits))
        L.append("      ],")
        L.append("      online: %s" % (js_str(p["online"]) if p.get("online") else "null"))
        L.append("    },")
    L.append("  ],")

    L.append("  techStack: [")
    for t in data["techStack"]:
        L.append("    { name: %s, lines: %s, share: %s, note: %s, color: %s },"
                 % (js_str(t["name"]), t["lines"], t["share"],
                    js_str(t.get("note", "")), js_str(t["color"])))
    L.append("  ],")

    L.append("  insights: [")
    for it in data["insights"]:
        L.append("    {")
        L.append("      icon: %s," % js_str(it["icon"]))
        L.append("      title: %s," % js_str(it["title"]))
        L.append("      desc: %s" % js_str(it["desc"]))
        L.append("    },")
    L.append("  ],")

    L.append("  workspaces: [")
    for w in data["workspaces"]:
        L.append("    { name: %s, created: %s, status: %s, note: %s, tone: %s },"
                 % (js_str(w["name"]), js_str(w["created"]), js_str(w["status"]),
                    js_str(w["note"]), js_str(w["tone"])))
    L.append("  ]")
    L.append("};")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
# 发布
# --------------------------------------------------------------------------
def git(args, check=False):
    r = subprocess.run(["git"] + args, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    if check and r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip())
    return r


def publish():
    status = git(["status", "--porcelain"])
    if not status.stdout.strip():
        log("[publish] 没有需要提交的改动，跳过。")
        return True
    git(["add", "-A"], check=True)
    msg = "chore(report): 同步 WorkBuddy 新项目 %s" % dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    git(["commit", "-m", msg], check=True)
    log("[publish] 已提交：%s" % msg)

    r = git(["push", "origin", "main"], check=False)
    if r.returncode == 0:
        log("[publish] 已推送到 GitHub，Pages 站点稍后自动刷新。")
        # 让 API 通道的快照跟上来，避免下次重复推送
        subprocess.run([sys.executable, str(HERE / "push_api.py"), "--sync-state"],
                       cwd=str(ROOT), capture_output=True)
        return True

    log("[publish] git push 被网络拦截，改走 GitHub API 通道：")
    log("          %s" % ((r.stderr or r.stdout).strip() or "unknown")[:200])
    api = subprocess.run([sys.executable, str(HERE / "push_api.py")],
                         cwd=str(ROOT), capture_output=True, text=True,
                         encoding="utf-8", errors="ignore")
    out = (api.stdout or "").strip()
    if api.returncode == 0 and "已推送" in out:
        log(out)
        return True

    log("[publish] API 通道也失败了：%s" % ((api.stdout or "") + (api.stderr or ""))[:400])
    log("[publish] 改动已保留在本地 commit，可在 GitHub Desktop 点 Push，或稍后重跑 --push-only。")
    return False


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只预览，不写文件")
    ap.add_argument("--push", action="store_true", help="重建后提交并推送")
    ap.add_argument("--push-only", action="store_true", help="只提交并推送已有改动")
    args = ap.parse_args()

    if args.push_only:
        publish()
        return

    DATA_DIR.mkdir(exist_ok=True)
    ov = load_json(OVERRIDES, {}) or {}
    prev_state = load_json(STATE, {}) or {}
    known_sids = set(prev_state.get("sessions") or [])

    sessions, deploys = collect_sessions()
    memory = collect_memory()
    data = build(sessions, deploys, memory, ov)

    new_sids = [p["name"] for p in data["projects"]]
    log("[scan] 识别到 %d 个有交付物的项目：" % len(data["projects"]))
    for p in data["projects"]:
        log("   - %s（%s）" % (p["name"], p["time"]))

    if args.dry_run:
        log("\n[dry-run] 未写入任何文件。")
        return

    out = render(data)
    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    log("\n[write] assets/data.js 已更新（%d 字节）" % len(out.encode("utf-8")))

    # 把时间线固化回 overrides（保留 sid/kind 以便下次去重）
    ov["timeline"] = [
        {k: t[k] for k in ("date", "title", "desc", "tag", "sid", "kind") if k in t}
        for t in data["timeline"]
    ]
    with open(OVERRIDES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(ov, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # 不写时间戳：state.json 内容保持稳定，才不会每次同步都产生一个空提交
    with open(STATE, "w", encoding="utf-8", newline="\n") as f:
        json.dump({
            "projects": new_sids,
            "sessions": sorted(known_sids | {s for s in sessions}),
        }, f, ensure_ascii=False, indent=2)
        f.write("\n")

    if args.push:
        publish()


if __name__ == "__main__":
    main()
