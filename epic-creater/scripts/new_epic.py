#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
new_epic.py — 新建一个 Epic 文档骨架

约定（不依赖任何配置文件）：
    ./prd/                                 Epic 文档目录，不存在时自动创建
    ./prd/epic-{N}-{slug}.md               生成的 Epic 文档
    ./prd/_epic-template.md                模板；不存在时从技能自带模板复制
    ./stories/epic-{N}-{slug}/             仅当 ./stories/ 已存在时创建
    ./tasks/epic-{N}-{slug}/               仅当 ./tasks/ 已存在时创建

编号规则：取 prd/ 下现有 Epic 的最大编号 + 1。不做冲突检测、不做空缺补位。

用法：
    python3 new_epic.py --slug my-feature --title "中文标题" --en-title "English Title"
    python3 new_epic.py --slug my-feature --title "T" --en-title "E" --dry-run
    python3 new_epic.py --slug my-feature --title "T" --en-title "E" --dir path/to/prd
"""

import argparse
import glob
import os
import re
import shutil
import sys

PRD_DIR = "prd"
TEMPLATE_NAME = "_epic-template.md"
SIBLINGS = ("stories", "tasks")
BUNDLED_TEMPLATE = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "assets", "epic-template.md"))


def ensure_template(prd_dir, dry_run=False):
    """确保模板存在；不存在时从技能自带模板复制过去。"""
    dst = os.path.join(prd_dir, TEMPLATE_NAME)
    if os.path.exists(dst):
        return dst
    if not os.path.exists(BUNDLED_TEMPLATE):
        print(f"错误：模板不存在，且技能自带模板也找不到（{BUNDLED_TEMPLATE}）", file=sys.stderr)
        sys.exit(2)
    if dry_run:
        print(f"[dry-run] 将创建模板：{dst}（复制自技能自带模板）")
        return dst
    shutil.copyfile(BUNDLED_TEMPLATE, dst)
    print(f"已创建模板：{dst}")
    return dst


def max_number(prd_dir):
    """返回 prd/ 下现有 Epic 的最大编号；无 Epic 时返回 0。"""
    rx = re.compile(r"epic-(\d+)-.+\.md$")
    nums = []
    for f in glob.glob(os.path.join(prd_dir, "*")):
        base = os.path.basename(f)
        if not os.path.isfile(f) or base.startswith("_"):
            continue
        m = rx.match(base)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) if nums else 0


def build_content(tpl, n, title, en_title):
    lines = open(tpl, encoding="utf-8").read().splitlines()

    # 跳过文件头的模板说明注释块
    start = 0
    if lines and lines[0].lstrip().startswith("<!--"):
        for i, ln in enumerate(lines):
            if ln.strip().endswith("-->"):
                start = i + 1
                break
    body = "\n".join(lines[start:]).lstrip("\n")
    body = re.sub(r"^#\s+.*$", f"# Epic {n}: {title} ({en_title})",
                  body, count=1, flags=re.M)

    header = (f"<!-- 由 epic-creater skill 生成（模板：{PRD_DIR}/{TEMPLATE_NAME}）；"
              f"填写完成后请删除本行与下方模板注释。 -->\n\n")
    return header + body + "\n"


def main():
    ap = argparse.ArgumentParser(description="新建一个 Epic 文档骨架")
    ap.add_argument("--slug", required=True, help="英文短名，如 my-new-feature")
    ap.add_argument("--title", required=True, help="中文标题")
    ap.add_argument("--en-title", required=True, help="英文标题")
    ap.add_argument("--dir", default=PRD_DIR, help=f"Epic 文档目录，默认 ./{PRD_DIR}/")
    ap.add_argument("--dry-run", action="store_true", help="只报告不落盘")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.slug):
        print(f"错误：slug 必须是小写短横线格式，收到：{args.slug}", file=sys.stderr)
        return 2

    prd_dir = os.path.abspath(args.dir)
    if not os.path.isdir(prd_dir):
        if args.dry_run:
            print(f"[dry-run] 将创建目录：{prd_dir}/")
        else:
            os.makedirs(prd_dir)
            print(f"已创建目录：{prd_dir}/")

    n = max_number(prd_dir) + 1
    print(f"Epic 目录：{prd_dir}")
    print(f"本次编号：{n}（当前最大编号 + 1）")

    epic_path = os.path.join(prd_dir, f"epic-{n}-{args.slug}.md")
    targets = [epic_path] + [
        os.path.join(kind, f"epic-{n}-{args.slug}")
        for kind in SIBLINGS if os.path.isdir(kind)
    ]

    existing = [t for t in targets if os.path.exists(t)]
    if existing:
        print("\n错误：以下路径已存在，未做任何改动：", file=sys.stderr)
        for t in existing:
            print(f"  - {t}", file=sys.stderr)
        return 2

    tpl = ensure_template(prd_dir, args.dry_run)

    if args.dry_run:
        print("\n[dry-run] 将要创建：")
        for t in targets:
            print(f"  - {t}")
        return 0

    for t in targets[1:]:
        os.makedirs(t)
    with open(epic_path, "w", encoding="utf-8") as fh:
        fh.write(build_content(tpl, n, args.title, args.en_title))

    print("\n已创建：")
    for t in targets:
        print(f"  - {t}")
    print(f"\n下一步：填写 {epic_path}（[必备] 章节不得省略）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
