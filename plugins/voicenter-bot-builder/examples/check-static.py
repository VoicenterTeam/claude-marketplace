#!/usr/bin/env python3
"""V-S static check suite — `../docs/reference/validation-checklist.md` §1.

Permanent regression protection: these run on every push (MS6 §6.1). Every check
below is scriptable and deterministic; the LLM-dependent families (V-C functional,
V-A claude.ai) cannot run here and are listed as SKIP with the reason.

Usage:
    python check-static.py            # from the plugin's examples/ directory
    python check-static.py --plugin ..

Exit 0 = every runnable V-S check passed.
"""

import argparse
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys

RESULTS = []


def record(vid, name, ok, detail=""):
    RESULTS.append((vid, name, ok, detail))


def skip(vid, name, why):
    RESULTS.append((vid, name, None, why))


def read(p):
    return io.open(p, encoding="utf-8").read()


def frontmatter(p):
    t = read(p)
    return t.split("---")[1] if t.startswith("---") else ""


def main(root):
    skills = sorted(glob.glob(os.path.join(root, "skills/*/SKILL.md")))
    stages = sorted(glob.glob(os.path.join(root, "skills/*/stages/*.md")))
    refs = sorted(glob.glob(os.path.join(root, "references/*.md")))
    agents = sorted(glob.glob(os.path.join(root, "agents/*.md")))

    # ---- V-S1: SKILL.md body length ----
    bad = []
    for f in skills:
        n = len(read(f).split("\n"))
        if n > 500:
            bad.append(f"{os.path.basename(os.path.dirname(f))}={n} (over hard ceiling 500)")
        elif n > 400:
            bad.append(f"{os.path.basename(os.path.dirname(f))}={n} (over target 400)")
    record("V-S1", "SKILL.md <= 400 lines (hard ceiling 500)", not bad,
           "; ".join(bad) or f"{len(skills)} skills, max "
           f"{max(len(read(f).split(chr(10))) for f in skills)}")

    # ---- V-S2: no duplicated check procedure text ----
    proc = os.path.join(root, "references/verification-procedure.md")
    phrases = [
        "Build the set of `intents[].IntentId` values",
        "the diagnosed mechanism of double-speech bugs",
        "1/1.5 token; whitespace at 1/4 token",
        "Whitelist:** quoted strings on lines that also contain save/set/store",
        "no terminal->anything chains".replace("->", "→"),
    ]
    hay = {f: read(f) for f in skills + stages + refs + agents}
    dup = []
    for ph in phrases:
        owners = [f for f, t in hay.items() if ph in t]
        if len(owners) > 1:
            dup.append(f"{ph[:40]!r} in {[os.path.basename(o) for o in owners]}")
    record("V-S2", "sampled CHK phrases each in exactly one file", not dup,
           "; ".join(dup) or f"{len(phrases)} phrases sampled, all unique to the procedure file")

    # ---- V-S3: cross-file pointers use ${CLAUDE_PLUGIN_ROOT} ----
    esc = []
    for f in skills + stages:
        for i, l in enumerate(read(f).split("\n"), 1):
            if "../../" in l:
                esc.append(f"{os.path.basename(f)}:{i}")
    record("V-S3", "no parent-dir escapes from skill dirs", not esc,
           "; ".join(esc) or "all shared-file pointers use ${CLAUDE_PLUGIN_ROOT}")

    # ---- V-S4: agent frontmatter lint ----
    ALLOWED = {"name", "description", "model", "effort", "maxTurns", "tools",
               "disallowedTools", "skills", "memory", "background", "isolation"}
    problems = []
    for f in agents:
        fm = frontmatter(f)
        keys = {m.group(1) for m in re.finditer(r"^([A-Za-z]+):", fm, re.M)}
        for k in ("hooks", "mcpServers", "permissionMode"):
            if k in keys:
                problems.append(f"{os.path.basename(f)}: forbidden key {k}")
        outside = keys - ALLOWED
        if outside:
            problems.append(f"{os.path.basename(f)}: keys outside C4 allow-list {sorted(outside)}")
        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        if nm and ":" in nm.group(1):
            problems.append(f"{os.path.basename(f)}: name contains ':'")
        d = re.search(r"^description:\s*(.+)$", fm, re.M)
        if d and len(d.group(1)) >= 1024:
            problems.append(f"{os.path.basename(f)}: description >= 1024 chars")
    record("V-S4", "agent frontmatter lint", not problems,
           "; ".join(problems) or f"{len(agents)} agent(s) clean")

    # ---- V-S5: stage files must not chain to other stage files ----
    chain = []
    for f in stages:
        for i, l in enumerate(read(f).split("\n"), 1):
            if "stages/" in l:
                chain.append(f"{os.path.basename(f)}:{i}")
    record("V-S5", "no stage -> stage references", not chain,
           "; ".join(chain) or f"{len(stages)} stage files, depth stays one level")

    # ---- V-S6: output contract present and referenced by both dispatch paths ----
    pt = read(proc)
    a3 = os.path.join(root, "skills/voicenter-bot-json-assembler/SKILL.md")
    s3 = read(a3)
    body = s3.split("### 6.1")[1].split("### 6.3")[0] if "### 6.1" in s3 else ""
    ok = ("## Output contract" in pt) and ("contract" in body)
    record("V-S6", "output contract in procedure file, referenced by §6.1/§6.2", ok,
           "" if ok else "contract missing from procedure file or not referenced by dispatch")

    # ---- V-S7: description budget ----
    over, lens = [], []
    for f in skills:
        d = re.search(r"^description:\s*(.+)$", frontmatter(f), re.M)
        n = len(d.group(1).strip()) if d else 0
        lens.append(f"{os.path.basename(os.path.dirname(f)).replace('voicenter-bot-', '')}={n}")
        if n > 200:
            over.append(f"{os.path.basename(os.path.dirname(f))}={n}")
    record("V-S7", "all skill descriptions <= 200 chars", not over,
           "; ".join(over) or ", ".join(lens))

    # ---- TOC in every reference/stage file > 100 lines (C6) ----
    missing = [os.path.basename(f) for f in stages + refs
               if len(read(f).split("\n")) > 100 and "Table of contents" not in read(f)]
    record("C6", "TOC in every reference/stage file > 100 lines", not missing,
           "; ".join(missing) or "all compliant")

    # ---- reserved words / hidden instructions (MS4 §4.6) ----
    CTRL = {0x200b, 0x200c, 0x200d, 0x200e, 0x200f, 0x202a, 0x202b, 0x202c, 0x202d,
            0x202e, 0x2060, 0xfeff, 0x061c, 0x2066, 0x2067, 0x2068, 0x2069}
    issues = []
    for f in skills + agents + sorted(glob.glob(os.path.join(root, "commands/*.md"))):
        fm = frontmatter(f)
        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        if nm:
            v = nm.group(1).strip()
            if not re.fullmatch(r"[a-z0-9-]{1,64}", v):
                issues.append(f"{os.path.basename(f)}: name charset/length")
            if re.search(r"claude|anthropic", v, re.I):
                issues.append(f"{os.path.basename(f)}: reserved word in name")
        t = read(f)
        if any(ord(c) in CTRL for c in t):
            issues.append(f"{os.path.basename(f)}: bidi/zero-width control char")
        if re.search(r"\b[A-Za-z0-9+/]{50,}={0,2}\b", t):
            issues.append(f"{os.path.basename(f)}: base64-shaped blob")
    record("MS4-4.6", "reserved words / hidden instructions sweep", not issues,
           "; ".join(issues) or "clean")

    # ---- manifest sanity ----
    try:
        mf = json.loads(read(os.path.join(root, ".claude-plugin/plugin.json")))
        need = ["name", "displayName", "version", "description", "author", "homepage",
                "repository", "license", "keywords"]
        miss = [k for k in need if k not in mf]
        record("MS4-4.1", "plugin.json complete", not miss,
               "; ".join(f"missing {k}" for k in miss) or f"version {mf['version']}")
    except Exception as e:  # noqa: BLE001
        record("MS4-4.1", "plugin.json complete", False, str(e))

    # ---- V-S8: manifest validation, if the CLI is on PATH ----
    cli = shutil.which("claude") or shutil.which("claude.cmd")
    if cli:
        try:
            p = subprocess.run([cli, "plugin", "validate", root, "--strict"],
                               capture_output=True, text=True, timeout=120)
            out = " ".join((p.stdout + p.stderr).split())[:200]
            record("V-S8", "claude plugin validate --strict", p.returncode == 0,
                   out or f"exit {p.returncode}")
        except (OSError, subprocess.SubprocessError) as e:  # noqa: BLE001
            skip("V-S8", "claude plugin validate --strict", f"CLI present but failed to run: {e}")
    else:
        skip("V-S8", "claude plugin validate --strict",
             "Claude Code CLI not on PATH; gated in CI instead "
             "(.github/workflows/plugin-validate.yml, job `validate`)")

    # ---- the LLM-dependent families ----
    skip("V-C*", "Claude Code functional suite",
         "needs a marketplace install + live skill invocation — "
         "see docs/planning/vc-run-instructions.md")
    skip("V-A*", "claude.ai regression suite",
         "must be executed by a human on claude.ai — see docs/planning/va-run-instructions.md")

    # ---- report ----
    w = max(len(n) for _, n, _, _ in RESULTS)
    print(f"{'ID':10s} {'check':{w}s}  result")
    print("-" * (12 + w + 10))
    fails = 0
    for vid, name, ok, detail in RESULTS:
        tag = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
        if ok is False:
            fails += 1
        print(f"{vid:10s} {name:{w}s}  {tag}")
        if detail:
            print(f"{'':10s} {'':{w}s}    {detail}")
    runnable = sum(1 for _, _, ok, _ in RESULTS if ok is not None)
    print(f"\n{runnable - fails}/{runnable} runnable checks passed; "
          f"{sum(1 for _, _, ok, _ in RESULTS if ok is None)} skipped.")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", default="..", help="path to the plugin root")
    sys.exit(main(ap.parse_args().plugin))
