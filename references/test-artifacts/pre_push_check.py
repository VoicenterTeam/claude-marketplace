"""
Pre-push completeness check for the Voicenter marketplace.
Catches structural gaps the human eye misses.

Checks:
  1. JSON validity (marketplace.json + every plugin.json)
  2. SKILL.md frontmatter has explicit `name:` field
  3. Forbidden plugin.json fields (icon, "skills": "./skills/")
  4. marketplace.json plugin entries match actual plugin folders
  5. Each plugin has a docs/plugins/<name>.md
  6. Each skill has a docs/skills/<skill>/README.md
  7. Markdown link integrity (every relative link in docs/ resolves to a real file)
  8. CHANGELOG mentions every plugin
  9. plugin.json names are consistent across the three places they appear
 10. Skill folder names match SKILL.md `name:` value
"""
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def section(title):
    print(f"\n=== {title} ===")


# ====== 1. JSON validity ======
section("1. JSON validity")

mp_path = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
with open(mp_path, encoding="utf-8") as f:
    mp = json.load(f)
print(f"  [OK] marketplace.json parses")

plugin_jsons = {}
for plugin_dir in os.listdir(os.path.join(ROOT, "plugins")):
    pj = os.path.join(ROOT, "plugins", plugin_dir, ".claude-plugin", "plugin.json")
    if not os.path.exists(pj):
        err(f"plugin folder {plugin_dir} has no .claude-plugin/plugin.json")
        continue
    with open(pj, encoding="utf-8") as f:
        plugin_jsons[plugin_dir] = json.load(f)
    print(f"  [OK] plugins/{plugin_dir}/.claude-plugin/plugin.json parses")


# ====== 2. SKILL.md frontmatter ======
section("2. SKILL.md frontmatter has explicit `name:` field")

skill_md_files = []
for plugin_dir in plugin_jsons:
    skills_root = os.path.join(ROOT, "plugins", plugin_dir, "skills")
    if not os.path.exists(skills_root):
        continue
    for skill_dir in os.listdir(skills_root):
        sm = os.path.join(skills_root, skill_dir, "SKILL.md")
        if not os.path.exists(sm):
            err(f"skill folder {plugin_dir}/skills/{skill_dir} has no SKILL.md")
            continue
        skill_md_files.append((plugin_dir, skill_dir, sm))

for plugin_dir, skill_dir, sm in skill_md_files:
    with open(sm, encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        err(f"{plugin_dir}/{skill_dir}/SKILL.md has no YAML frontmatter")
        continue
    fm_end = content.find("---", 4)
    if fm_end < 0:
        err(f"{plugin_dir}/{skill_dir}/SKILL.md frontmatter not closed")
        continue
    fm = content[3:fm_end]
    name_match = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
    if not name_match:
        err(f"{plugin_dir}/{skill_dir}/SKILL.md frontmatter missing `name:` field")
        continue
    declared_name = name_match.group(1)
    if declared_name != skill_dir:
        err(f"{plugin_dir}/{skill_dir}/SKILL.md `name: {declared_name}` does not match folder name `{skill_dir}`")
    print(f"  [OK] {plugin_dir}/{skill_dir} — name: {declared_name}")


# ====== 3. Forbidden plugin.json fields ======
section("3. plugin.json forbidden fields")

for plugin_dir, pj in plugin_jsons.items():
    if "icon" in pj:
        err(f"{plugin_dir}/plugin.json contains forbidden `icon` field")
    if pj.get("skills") == "./skills/":
        err(f"{plugin_dir}/plugin.json contains redundant `skills: ./skills/` (default discovery handles it)")
    print(f"  [OK] {plugin_dir}/plugin.json has no forbidden fields")


# ====== 4. marketplace.json plugins match plugin folders ======
section("4. marketplace.json plugins ↔ plugin folders")

mp_plugin_names = {p["name"] for p in mp["plugins"]}
folder_names = set(plugin_jsons.keys())

if mp_plugin_names != folder_names:
    only_in_mp = mp_plugin_names - folder_names
    only_in_folders = folder_names - mp_plugin_names
    if only_in_mp:
        err(f"marketplace.json lists plugins with no folder: {only_in_mp}")
    if only_in_folders:
        err(f"plugin folders not registered in marketplace.json: {only_in_folders}")
else:
    print(f"  [OK] marketplace.json plugins = {sorted(mp_plugin_names)}")


# ====== 5. Each plugin has a docs/plugins/<name>.md ======
section("5. docs/plugins/<plugin>.md exists for each plugin")

for pname in sorted(folder_names):
    p = os.path.join(ROOT, "docs", "plugins", f"{pname}.md")
    if os.path.exists(p):
        print(f"  [OK] docs/plugins/{pname}.md")
    else:
        err(f"missing docs/plugins/{pname}.md for plugin {pname}")


# ====== 6. Each skill has a docs/skills/<skill>/README.md ======
section("6. docs/skills/<skill>/README.md exists for each skill")

# Skills are in two namespaces:
#  - voicenter-api skills: the docs folder uses the *skill* name (active-calls, click2call, ...)
#  - voicenter-mcp skill: docs uses 'setup'
#  - voicenter-bot-builder skills: docs uses the full name (voicenter-bot-spec-designer, ...)

for plugin_dir, skill_dir, sm in skill_md_files:
    candidates = [
        os.path.join(ROOT, "docs", "skills", skill_dir, "README.md"),
    ]
    found = next((c for c in candidates if os.path.exists(c)), None)
    if found:
        rel = os.path.relpath(found, ROOT).replace("\\", "/")
        print(f"  [OK] {rel}")
    else:
        err(f"missing docs/skills/{skill_dir}/README.md for skill {plugin_dir}/{skill_dir}")


# ====== 7. Markdown link integrity ======
section("7. Markdown link integrity in docs/ + repo-root .md")

DOCS_ROOTS = [os.path.join(ROOT, "docs"), ROOT]
md_files = []
for d in DOCS_ROOTS:
    if d == ROOT:
        for fn in os.listdir(d):
            if fn.endswith(".md") and os.path.isfile(os.path.join(d, fn)):
                md_files.append(os.path.join(d, fn))
    else:
        for dp, _, fns in os.walk(d):
            for fn in fns:
                if fn.endswith(".md"):
                    md_files.append(os.path.join(dp, fn))

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

broken = []
checked = 0
for mf in md_files:
    with open(mf, encoding="utf-8") as f:
        text = f.read()
    for m in LINK_RE.finditer(text):
        target = m.group(2)
        # Skip absolute, mailto, anchor-only, code blocks
        if target.startswith(("http://", "https://", "mailto:", "#", "[")):
            continue
        # Strip anchor
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        # Resolve relative to the file's dir
        resolved = os.path.normpath(os.path.join(os.path.dirname(mf), clean))
        checked += 1
        if not os.path.exists(resolved):
            broken.append((os.path.relpath(mf, ROOT).replace("\\", "/"),
                           target,
                           os.path.relpath(resolved, ROOT).replace("\\", "/")))

if broken:
    for src, link, resolved in broken:
        err(f"broken link in {src}: '{link}' -> {resolved}")
else:
    print(f"  [OK] {checked} relative links across {len(md_files)} markdown files all resolve")


# ====== 8. CHANGELOG mentions every plugin ======
section("8. CHANGELOG.md mentions every plugin")

with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
    changelog = f.read()

for pname in sorted(folder_names):
    if pname in changelog:
        print(f"  [OK] CHANGELOG mentions {pname}")
    else:
        warn(f"CHANGELOG.md does not mention plugin '{pname}' — consider adding a release entry")


# ====== 9. plugin.json name vs folder name vs marketplace.json ======
section("9. plugin name consistency (folder = plugin.json.name = marketplace.json entry)")

mp_by_name = {p["name"]: p for p in mp["plugins"]}
for plugin_dir, pj in plugin_jsons.items():
    pj_name = pj.get("name")
    if pj_name != plugin_dir:
        err(f"folder 'plugins/{plugin_dir}' has plugin.json name '{pj_name}' (mismatch)")
        continue
    mp_entry = mp_by_name.get(plugin_dir)
    if not mp_entry:
        # Already reported in section 4
        continue
    expected_source = f"./plugins/{plugin_dir}"
    if mp_entry.get("source") != expected_source:
        err(f"marketplace entry for {plugin_dir} has source '{mp_entry.get('source')}' (expected '{expected_source}')")
    if mp_entry.get("version") != pj.get("version"):
        warn(f"version drift: marketplace says {plugin_dir}@{mp_entry.get('version')}, plugin.json says @{pj.get('version')}")
    print(f"  [OK] {plugin_dir}: folder = manifest name = marketplace entry; v{pj.get('version')}")


# ====== 10. README + getting-started.md plugin/skill count consistency ======
section("10. README.md + docs/getting-started.md plugin count")

with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as f:
    readme = f.read()
gs_path = os.path.join(ROOT, "docs", "getting-started.md")
with open(gs_path, encoding="utf-8") as f:
    gs = f.read()

# Heuristics — flag if a known new plugin is missing from these top-level docs
for new_plugin in ["voicenter-bot-builder"]:
    if new_plugin not in readme:
        warn(f"README.md does not mention plugin '{new_plugin}' — onboarding will miss it")
    if new_plugin not in gs:
        warn(f"docs/getting-started.md does not mention plugin '{new_plugin}' — install steps will miss it")

# Total skill count
total_skills = sum(
    len([d for d in os.listdir(os.path.join(ROOT, "plugins", p, "skills"))
         if os.path.isdir(os.path.join(ROOT, "plugins", p, "skills", d))])
    for p in folder_names
    if os.path.exists(os.path.join(ROOT, "plugins", p, "skills"))
)
print(f"  Total skills across all plugins: {total_skills}")
# getting-started.md says "15 skills registered in total" — flag if obsolete
m = re.search(r"(\d+)\s+skills?\s+registered", gs)
if m and int(m.group(1)) != total_skills:
    warn(f"docs/getting-started.md claims {m.group(1)} skills registered but actual total is {total_skills}")


# ====== Summary ======
section("Summary")
print(f"  Errors: {len(errors)}")
print(f"  Warnings: {len(warnings)}")
if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  ✗ {e}")
if warnings:
    print("\nWARNINGS:")
    for w in warnings:
        print(f"  ! {w}")
if not errors and not warnings:
    print("\nNothing missing.")
sys.exit(1 if errors else 0)
