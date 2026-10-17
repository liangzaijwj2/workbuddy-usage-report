#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过 GitHub REST API 推送提交 —— 用于 github.com 被网络策略拦截时的备用通道。

原理：把本地的改动打包成一棵 git tree，用 Git Data API 创建 commit 并移动分支引用。
一次请求完成全部文件更新，等价于一次 git push。

用法：
  python tools/push_api.py                 推送本地未推送的改动
  python tools/push_api.py --dry-run       只看会提交哪些文件
  python tools/push_api.py --all-files     不比对 origin，提交工作区全部受版本控制的文件

凭据来源（按顺序）：
  1. 环境变量 GITHUB_TOKEN
  2. 本机 git credential manager 里已存的 GitHub 凭据
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"
OWNER = "liangzaijwj2"
REPO = "workbuddy-usage-report"
BRANCH = "main"

# api.github.com 在本机可以直连；走代理反而会被拒，所以这里显式禁用代理
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def git(args, binary=False):
    r = subprocess.run(["git"] + args, cwd=str(ROOT), capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", errors="ignore")


def get_token():
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t.strip()
    r = subprocess.run(
        ["git", "-c", "credential.helper=manager", "credential", "fill"],
        cwd=str(ROOT), input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, encoding="utf-8", errors="ignore",
    )
    for line in (r.stdout or "").splitlines():
        if line.startswith("password="):
            return line[len("password="):].strip()
    return None


def api(method, path, payload=None, token=None):
    url = API + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "workbuddy-usage-report-sync")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError("GitHub API %s %s 失败：%s %s" % (method, path, e.code, body[:400]))
    except Exception as e:
        raise RuntimeError("无法连接 %s（%s）。若本机网络策略拦截，请改用 git push 或 GitHub Desktop。"
                           % (url, e))


def skip(p):
    """本地工具目录、编辑器垃圾不该进仓库。"""
    q = p.replace("\\", "/")
    return q.startswith(".workbuddy/") or "/.workbuddy/" in q or q.startswith(".git/")


def changed_files(use_all=False):
    """返回 [(status, relpath)]，status ∈ {A, M, D}"""
    if use_all:
        out = git(["ls-files"]).split("\n")
        return [("M", p) for p in out if p.strip() and not skip(p)]
    out = git(["diff", "--name-status", "origin/%s..%s" % (BRANCH, BRANCH)]).strip()
    if not out:
        return []
    res = []
    for line in out.split("\n"):
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        st = parts[0][0]
        rel = parts[-1]
        if skip(rel):
            continue
        res.append(("D" if st == "D" else ("A" if st == "A" else "M"), rel))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all-files", action="store_true", help="提交工作区全部受版本控制的文件")
    ap.add_argument("--message", default=None)
    args = ap.parse_args()

    files = changed_files(args.all_files)
    if not files:
        print("[push-api] 没有需要推送的改动。")
        return 0

    # 未跟踪的新文件也要带上
    if not args.all_files:
        untracked = git(["ls-files", "--others", "--exclude-standard"]).split("\n")
        seen = {p for _, p in files}
        for p in untracked:
            p = p.strip()
            if p and p not in seen and not skip(p):
                files.append(("A", p))
                seen.add(p)

    print("[push-api] 将提交 %d 个文件：" % len(files))
    for st, p in files:
        print("   %s  %s" % (st, p))
    if args.dry_run:
        return 0

    token = get_token()
    if not token:
        print("[push-api] 拿不到 GitHub 凭据。设置 GITHUB_TOKEN 环境变量，或先在 git / GitHub Desktop 登录。")
        return 1

    ref = api("GET", "/repos/%s/%s/git/ref/heads/%s" % (OWNER, REPO, BRANCH), token=token)
    parent = ref["object"]["sha"]

    tree = []
    for st, rel in files:
        if st == "D":
            tree.append({"path": rel.replace("\\", "/"), "mode": "100644", "type": "blob", "sha": None})
            continue
        fp = ROOT / rel
        if not fp.exists():
            print("[push-api] 跳过不存在的文件：%s" % rel)
            continue
        content = fp.read_text(encoding="utf-8")
        tree.append({
            "path": rel.replace("\\", "/"),
            "mode": "100644",
            "type": "blob",
            "content": content,
        })

    if not tree:
        print("[push-api] 没有有效内容，中止。")
        return 1

    new_tree = api("POST", "/repos/%s/%s/git/trees" % (OWNER, REPO),
                   {"base_tree": parent, "tree": tree}, token=token)
    msg = args.message or ("chore(report): 同步 WorkBuddy 新项目 %s" %
                           subprocess.run(["git", "log", "-1", "--format=%ci"], cwd=str(ROOT),
                                          capture_output=True, text=True).stdout.strip()[:16])
    commit = api("POST", "/repos/%s/%s/git/commits" % (OWNER, REPO),
                 {"message": msg, "tree": new_tree["sha"], "parents": [parent]}, token=token)
    api("PATCH", "/repos/%s/%s/git/refs/heads/%s" % (OWNER, REPO, BRANCH),
        {"sha": commit["sha"]}, token=token)

    print("[push-api] 已推送 %s" % commit["sha"][:8])
    print("[push-api] https://github.com/%s/%s/commit/%s" % (OWNER, REPO, commit["sha"][:8]))
    print("[push-api] GitHub Pages 通常 1-3 分钟内完成重建。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
