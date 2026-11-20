#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gohlint.py — GoH 模组深度检查
  python gohlint.py <mod目录>

检查项：
  1. 所有 .mi/.inc/.set/.def 括号平衡
  2. 实体 ID 冲突（同一文件/整个 mod）
  3. include 目标存在性（mod 内或游戏 pak 内）
  4. 模板标签 vs 触发器引用（menu:: 标签）
"""
import sys, os, re, zipfile, collections

GAME = r"G:/SteamLibrary/steamapps/common/Call to Arms - Gates of Hell"


def game_paths():
    """收集游戏 pak 中的所有资源路径"""
    paths = set()
    for root, _, files in os.walk(os.path.join(GAME, "resource")):
        for f in files:
            if not f.endswith(".pak"):
                continue
            try:
                z = zipfile.ZipFile(os.path.join(root, f))
            except Exception:
                continue
            for n in z.namelist():
                paths.add("/" + n)
                paths.add("/" + n.rsplit("/", 1)[-1])
    return paths


def main(mod):
    res = os.path.join(mod, "resource")
    if not os.path.isdir(res):
        print("缺少 resource 目录:", res)
        return 1

    files = []
    for root, _, fs in os.walk(res):
        for f in fs:
            if f.endswith((".mi", ".inc", ".set", ".def", ".ext")):
                files.append(os.path.join(root, f))

    print(f"检查 {len(files)} 个脚本文件\n")

    issues = 0
    all_ids = collections.defaultdict(list)
    includes = set()
    tags_added, tags_used = set(), set()

    for path in files:
        try:
            text = open(path, encoding="utf-8-sig", errors="ignore").read()
        except Exception as e:
            print(f"✗ 读取失败 {path}: {e}")
            issues += 1
            continue

        # 1) 括号
        depth = pdepth = 0
        for ch in text:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            elif ch == "(":
                pdepth += 1
            elif ch == ")":
                pdepth -= 1
        if depth or pdepth:
            print(f"✗ 括号不平衡 {os.path.relpath(path, mod)}: {{}}={depth} ()={pdepth}")
            issues += 1

        # 2) 实体 ID
        for m in re.finditer(r'\b0x([0-9a-fA-F]{4,8})\b', text):
            all_ids[int(m.group(1), 16)].append(os.path.relpath(path, mod))

        # 3) include
        for m in re.finditer(r'\(include "([^"]+)"\)', text):
            includes.add(m.group(1))

        # 4) 标签
        for m in re.finditer(r'\{tag_add "([^"]+)"\}', text):
            tags_added.add(m.group(1))
        for m in re.finditer(r'\{tag "([^"]+)"\}', text):
            tags_used.add(m.group(1))

    # include 存在性
    gpaths = game_paths()
    missing_inc = []
    for inc in sorted(includes):
        if inc.startswith("/"):
            rel = inc.lstrip("/")
            cand_mods = [os.path.join(res, rel.replace("/", os.sep))]
            cand_mods += [os.path.join(res, rel.replace("/", os.sep) + ext) for ext in (".mi", ".inc", ".set")]
            ok = any(os.path.isfile(c) for c in cand_mods) or inc in gpaths
            if not ok:
                missing_inc.append(inc)
    if missing_inc:
        print(f"✗ 找不到的 include ({len(missing_inc)}):")
        for i in missing_inc[:10]:
            print("   ", i)
        issues += len(missing_inc)

    # ID 冲突（不同文件之间）
    cross = {i: ps for i, ps in all_ids.items() if len(set(ps)) > 1}
    if cross:
        print(f"⚠ 实体 ID 跨文件重复 ({len(cross)}):")
        for i, ps in list(cross.items())[:5]:
            print(f"   0x{i:x}: {sorted(set(ps))[:3]}")
        issues += len(cross)

    # 标签引用但从未添加
    unused = {t for t in tags_used if t.startswith(("sm::", "menu::")) and t not in tags_added}
    if unused:
        print(f"⚠ 触发器引用了未定义的标签 ({len(unused)}):", list(unused)[:5])
        issues += len(unused)

    print(f"\n共 {issues} 个问题")
    return 0 if issues == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
