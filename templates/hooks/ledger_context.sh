#!/usr/bin/env bash
# SessionStart hook — claude_work 대장(LEDGER.md)의 진행 중 건과 미결을 컨텍스트에 주입한다.
# claude_work 밖에서는 아무것도 출력하지 않는다.
set -u
ROOT="$HOME/claude_work"
# second_brain 의 Orca 워크트리도 같은 대장·위키를 쓴다 — 예전 조건은 ~/claude_work 밖이면 아무것도 안 보여
# 워크트리 세션에서 대장·위키 신선도 주입이 조용히 꺼져 있었다 (2026-10-08).
SBWT="$HOME/orca/workspaces/second_brain"
CWD="$(pwd -P)"
case "$CWD" in "$ROOT"|"$ROOT"/*|"$SBWT"/*) ;; *) exit 0 ;; esac
INPUT="$(cat 2>/dev/null || true)"
SOURCE="$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("source",""))
except Exception: print("")' 2>/dev/null)"

LEDGER="$ROOT/LEDGER.md"
[ -f "$LEDGER" ] || exit 0

echo "# claude_work 작업 대장 (LEDGER.md)"
echo
echo "**규율: 새 작업은 LEDGER.md에 행이 생긴 뒤 시작한다.** 착수는 \`case-intake\` 스킬."
echo

# 진행 중 · 미확인 — 건마다 한 줄(경로 · 상태 · 「지금」 앞부분 · 이력 페이지). 행 전체는 LEDGER.md 에 있다.
# 행 전체를 싣던 판은 세션마다 1.4만 자였다 (2026-10-21 사용자 「second brain 이 무거워지는 것은 원하지 않는다」).
#  - '## 상태 어휘' 이후는 범례이므로 읽지 않는다
#  - 구분선(|---|)과 열이 5개 미만인 행(범례)은 제외한다
echo "## 진행 중 · 미확인 (건마다 한 줄 — 전체 행은 LEDGER.md)"
echo
python3 - "$LEDGER" <<'PY' 2>/dev/null
import re, sys
n = 0
for line in open(sys.argv[1], encoding="utf-8"):
    if line.startswith("## 상태 어휘"):
        break
    cols = [c.strip() for c in line.rstrip("\n").split("|")]
    if not line.startswith("|") or len(cols) < 6 or re.match(r"^[ :-]*$", cols[1]):
        continue
    # 표마다 열이 다르다(platform: 디렉토리 | 무엇 | 상태 …, case: 건 | 대상 | 요지 | 상태 …) — 짧은 상태 칸을 찾는다
    si = next((i for i in range(2, len(cols)) if 0 < len(cols[i]) <= 20
               and re.search(r"진행중|미확인|STALE|대기|보류|완료|운영|폐기|종결", cols[i])), None)
    if si is None or not re.search(r"진행중|미확인|STALE|대기|보류", cols[si]):
        continue
    state, desc = cols[si], cols[si - 1]
    works = re.search(r"\[works/([\w-]+)\]", desc)
    now = re.search(r"\*\*지금\*\*\s*:\s*(.*?)(?: · 이력 |$)", desc)
    text = re.sub(r"\*\*|`", "", (now.group(1) if now else desc.split(" · ")[0]))
    text = text if len(text) <= 80 else text[:79] + "…"
    tail = f" (works/{works.group(1)})" if works else ""
    print(f"  - {cols[1]} — {state} · {text}{tail}")
    n += 1
    if n >= 40:
        break
PY
echo

# 미결 절 — 항목 제목만 한 줄씩. 결판 조건 · 경위는 LEDGER.md 「미결」.
if grep -q '^## 미결' "$LEDGER"; then
  echo "## 미결 (건을 넘어 남은 것 — 제목만, 상세는 LEDGER.md)"
  echo
  python3 - "$LEDGER" <<'PY' 2>/dev/null
import re, sys
f = False
for line in open(sys.argv[1], encoding="utf-8"):
    if line.startswith("## 미결"):
        f = True
        continue
    if f and line.startswith("## "):
        break
    if not f:
        continue
    if line.startswith("### "):
        print("  " + line.strip())
    elif line.startswith("- ") and not line.startswith("- ~~"):
        m = re.match(r"- \*\*(.+?)\*\*", line)
        t = re.sub(r"`", "", m.group(1) if m else line[2:].strip())
        print("  - " + (t if len(t) <= 90 else t[:89] + "…"))
PY
  echo
fi

# 수확 대기 큐
Q="$ROOT/.ops/harvest_queue.jsonl"
if [ -s "$Q" ]; then
  n=$(wc -l < "$Q")
  echo "## ⚠ 수확 의례 미실행 세션 ${n}건"
  echo
  echo "  아래 세션이 파일을 고쳤는데 지식 승격·대장 갱신 없이 끝났다."
  tail -5 "$Q" | sed 's/^/  /'
  echo
  echo "  이번 세션에서 다룬다면: \`~/.claude/skills/analysis-asset-kit/references/harvest.md\`의"
  echo "  판정 3문을 돌리고, LEDGER.md 상태를 갱신한 뒤 위 큐 파일을 비운다."
  echo "  다루지 않는다면 큐를 그대로 둔다 — 사라지지 않는 것이 이 장치의 요점이다."
  echo
fi

# second_brain 위키 신선도 — 위키를 고치는 주체는 세션이므로 세션 시작에 보인다 (2026-10-01).
# stale.md 는 매회 정확히 재계산됐지만 9/18~10/01 아무도 열지 않아 6장이 +35~235통 낡았다.
SB="$ROOT/second_brain"
case "$CWD" in "$SB"|"$SB"/*|"$SBWT"/*)
  # 직전 세션 인계 — 새로 시작한 세션만 (compact 는 같은 세션이라 보일 필요가 없다)
  case "$SOURCE" in compact) ;; *) python3 "$SB/scripts/session_handoff.py" show "$CWD" 2>/dev/null ;; esac
  # 세션 증류 승인 대기 줄은 뺐다 — 증류 단계가 10-19 부터 멈춰 있고 대기열은 화면에서도 내렸다 (10-20 · 10-21 사용자 결정).
  # 메모리 위생 — 문제가 있을 때만 한 줄 (refresh 가 매 회차 재계산, 2026-10-08)
  python3 - "$SB" <<'PY' 2>/dev/null
import json, sys, pathlib
try:
    d = json.loads((pathlib.Path(sys.argv[1]) / "results/memory_lint.json").read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)
iss = d.get("issues", [])
if iss:
    kinds = {}
    for k, *_ in iss:
        kinds[k] = kinds.get(k, 0) + 1
    print(f"## 메모리 위생 ({d.get('generated','')[5:16]}) — " + " · ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
          + f" · 색인 {d.get('n_index')}줄/{d.get('budget')}")
    print("  새 메모리를 쓰기 전 같은 주제가 있는지 먼저 보고 UPDATE 한다. 정리는 사용자 승인 뒤. 상세: `python3 scripts/lint_memory.py`")
    print()
PY
  python3 - "$SB" <<'PY' 2>/dev/null
import json, re, sys, pathlib
sb = pathlib.Path(sys.argv[1])
try:
    d = json.loads((sb / "results/stale_state.json").read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)
rows = d.get("rows", [])
inbox = sb / "wiki/inbox.md"
m = re.search(r"페이지 없는 개체 (\d+)", inbox.read_text(encoding="utf-8")) if inbox.exists() else None
if not rows and not m:
    sys.exit(0)
print(f"## second_brain 위키 신선도 ({d.get('generated','')}) — 내용 페이지 {d.get('n_doc','?')}장 중 낡음 {len(rows)}장")
print()
for r in rows[:4]:
    print(f"  - {r['page']} — {r['entity']} +{r['after']}통 ({r['updated']} 이후)")
if len(rows) > 4:
    print(f"  - 외 {len(rows) - 4}장 — wiki/stale.md")
if m:
    print(f"  - 페이지 없는 개체 {m.group(1)}개 (수요순 wiki/inbox.md ②)")
print()
print("  이 세션이 메일 질의를 다룬다면 관련 페이지가 위에 있는지 먼저 보고, 낡았으면 갱신한 뒤 인용한다.")
print("  갱신: `python3 scripts/wiki_source.py entity <이름>` → 증분만 읽고 `updated:` 올림. 다루지 않으면 그대로 둔다.")
print()
PY
  # 작업 이력(works/) 신선도 + 수확 대기열을 페이지로 잇는다 (2026-10-08).
  # works 페이지는 총괄 소유다 — 건 세션은 쓰지 않으므로 여기(second_brain 세션 시작)에서만 보인다.
  python3 - "$SB" "$ROOT" <<'PY' 2>/dev/null
import json, re, sys, pathlib
sb, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
try:
    d = json.loads((sb / "results/stale_state.json").read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)
stale = [r for r in d.get("rows", []) if str(r.get("entity", "")).startswith("작업:")]
reg = {}
for m in re.finditer(r"^\| ([a-z0-9-]+) \| ([^|]+?) \|", (sb / "docs/templates/work_slugs.md").read_text(encoding="utf-8"), re.M):
    for part in re.split(r"\s*\+\s*", m.group(2)):
        reg[part.split(" (")[0].strip().strip("/")] = m.group(1)
hint = {}
q = root / ".ops/harvest_queue.jsonl"
if q.exists():
    for line in q.read_text().splitlines():
        try:
            e = json.loads(line); cwd = e.get("cwd", ""); ended = e.get("ended", "")[:10]
        except ValueError:
            continue
        best = max((k for k in reg if cwd == k or cwd.startswith(k + "/")), key=len, default=None)
        if not best:
            continue
        pg = sb / "wiki/works" / f"{reg[best]}.md"
        up = re.search(r"^updated:\s*(\S+)", pg.read_text(encoding="utf-8"), re.M) if pg.exists() else None
        if up and ended <= up.group(1):
            continue                      # 페이지가 이미 이 세션 이후에 쓰였다
        hint[reg[best]] = hint.get(reg[best], 0) + 1
if not stale and not hint:
    sys.exit(0)
print(f"## 작업 이력(works/) 갱신 대기 — 낡음 {len(stale)}장 · 수확 대기열이 가리키는 건 {len(hint)}개")
print()
for r in stale[:6]:
    slug = pathlib.Path(r["page"]).stem
    print(f"  - {slug} — 새 커밋·파일 {r['after']}개 ({r['updated']} 이후, 최신 {r.get('last', '')})")
if len(stale) > 6:
    print(f"  - 외 {len(stale) - 6}장 — wiki/stale.md")
for slug, n in sorted(hint.items(), key=lambda x: -x[1])[:6]:
    if not any(pathlib.Path(r["page"]).stem == slug for r in stale):
        print(f"  - {slug} — 수확 대기 세션 {n}건 (아직 낡음 판정 전)")
print()
print("  갱신: `python3 scripts/work_source.py --page <slug>` → 증분만 읽고 흐름·결정·미결 보강 → `updated:` 올림.")
print("  works 페이지는 총괄 소유 — 건 세션은 쓰지 않는다. 다루지 않으면 그대로 둔다(낡음은 데이터에서 다시 계산된다).")
print()
PY
;; esac
