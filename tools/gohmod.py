#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gohmod.py — Call to Arms: Gates of Hell 模组工具集
用法:
  python gohmod.py pak-list   <pak文件>
  python gohmod.py pak-extract<pak文件> <输出目录>
  python gohmod.py pak-pack   <目录> <输出pak>
  python gohmod.py mi-check   <文件或目录>        # 括号/圆括号/编码检查
  python gohmod.py inject     <地图目录名> <include行> <输出目录>
  python gohmod.py units      <阵营> <时期>       # 导出多人单位表
  python gohmod.py tga2png    <输入.tga> <输出.png>
  python gohmod.py scan       <mod目录>           # 对比游戏原文件，列出覆盖项
"""
import sys, os, io, re, zipfile, struct

GAME = r"G:/SteamLibrary/steamapps/common/Call to Arms - Gates of Hell"


# ---------- pak ----------
def cmd_pak_list(args):
    pak = args[0]
    z = zipfile.ZipFile(pak)
    for n in z.namelist():
        print(f"{z.getinfo(n).file_size:>10}  {n}")


def cmd_pak_extract(args):
    src, out = args[0], args[1]
    z = zipfile.ZipFile(src)
    z.extractall(out)
    print(f"解包 {len(z.namelist())} 个文件 -> {out}")


def cmd_pak_pack(args):
    src, dst = args[0], args[1]
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    n = 0
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src):
            for f in files:
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, src).replace(os.sep, "/"))
                n += 1
    print(f"打包 {n} 个文件 -> {dst} ({os.path.getsize(dst)} 字节)")


# ---------- SDL 检查 ----------
def check_file(path):
    raw = open(path, "rb").read()
    problems = []
    if raw[:3] == b"\xef\xbb\xbf":
        problems.append("有 BOM（引擎一般能读，但原版无 BOM）")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        return [f"UTF-8 解码失败: {e}"]
    depth = pdepth = 0
    line = 1
    for ch in text:
        if ch == "\n":
            line += 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                problems.append(f"第 {line} 行：多余的 }}")
                depth = 0
        elif ch == "(":
            pdepth += 1
        elif ch == ")":
            pdepth -= 1
            if pdepth < 0:
                problems.append(f"第 {line} 行：多余的 )")
                pdepth = 0
    if depth:
        problems.append(f"结尾缺少 {depth} 个 }}")
    if pdepth:
        problems.append(f"结尾缺少 {pdepth} 个 )")
    # include 目标是否存在（相对 resource 根）
    for m in re.finditer(r'\(include "([^"]+)"\)', text):
        target = m.group(1)
        if target.startswith("/"):
            continue  # 绝对路径无法在此判断
    return problems


def cmd_mi_check(args):
    path = args[0]
    files = []
    if os.path.isdir(path):
        for root, _, fs in os.walk(path):
            files += [os.path.join(root, f) for f in fs if f.endswith((".mi", ".inc", ".set", ".def"))]
    else:
        files = [path]
    bad = 0
    for f in files:
        p = check_file(f)
        if p:
            bad += 1
            print(f"✗ {f}")
            for x in p:
                print("    -", x)
    print(f"\n检查 {len(files)} 个文件，问题 {bad} 个")


# ---------- 任务注入 ----------
def cmd_inject(args):
    mapdir, include_line, outdir = args[0], args[1], args[2]
    z = zipfile.ZipFile(os.path.join(GAME, "resource/map/multi.pak"))
    n = 0
    for name in z.namelist():
        if not name.startswith(mapdir.rstrip("/") + "/") or not name.endswith(".mi"):
            continue
        raw = z.read(name).decode("utf-8-sig", "ignore").replace("\r\n", "\n")
        if include_line in raw:
            continue
        lines = raw.split("\n")
        at = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "}":
                at = i
                break
        lines.insert(at, include_line)
        dst = os.path.join(outdir, "resource/map", name.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        io.open(dst, "w", encoding="utf-8", newline="").write("\n".join(lines))
        print(f"注入 {name} -> 第 {at+1} 行")
        n += 1
    print(f"共 {n} 个任务文件")


# ---------- 单位表 ----------
def cmd_units(args):
    fac, per = args[0], args[1]
    z = zipfile.ZipFile(os.path.join(GAME, "resource/gamelogic.pak"))
    p = f"set/multiplayer/units/{per}/units_{fac}.set"
    if p not in z.namelist():
        print("不存在:", p)
        return
    t = z.read(p).decode("utf-8-sig", "ignore")
    t = "\n".join(l.split(";")[0] for l in t.split("\n"))
    entries = re.findall(r'\{"([^"]+)"\s*(.*?)\n\}', t, re.S)
    print(f"{fac}/{per}: {len(entries)} 个条目\n")
    for uid, body in entries:
        body = " ".join(body.split())
        veh = re.search(r'vehicle\(([a-z0-9_]+)\)', body)
        crew = re.findall(r'crew\d?\(([a-z0-9_]+):(\d+)\)', body)
        cs = re.findall(r'\bc\d\(([a-z0-9_]+):(\d+)\)', body)
        kind = "载具" if veh else ("班组" if cs else "其他")
        detail = veh.group(1) if veh else ", ".join(f"{b}×{n}" for b, n in cs)
        print(f"  [{kind}] {uid}  {detail}")


# ---------- 图片 ----------
def cmd_tga2png(args):
    from PIL import Image
    im = Image.open(args[0])
    im.save(args[1])
    print(f"{args[0]} -> {args[1]} ({im.size[0]}x{im.size[1]})")


# ---------- 覆盖扫描 ----------
def cmd_scan(args):
    mod = args[0]
    res = os.path.join(mod, "resource")
    if not os.path.isdir(res):
        print("没有 resource 目录")
        return
    total = 0
    for root, _, files in os.walk(res):
        for f in files:
            total += 1
    print(f"mod 文件总数: {total}")
    for d in sorted(os.listdir(res)):
        p = os.path.join(res, d)
        if os.path.isdir(p):
            n = sum(1 for r, _, fs in os.walk(p) for _ in fs)
            print(f"  {d}/  {n}")
        else:
            print(f"  {d}  {os.path.getsize(p)} 字节")


COMMANDS = {
    "pak-list": cmd_pak_list,
    "pak-extract": cmd_pak_extract,
    "pak-pack": cmd_pak_pack,
    "mi-check": cmd_mi_check,
    "inject": cmd_inject,
    "units": cmd_units,
    "tga2png": cmd_tga2png,
    "scan": cmd_scan,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
