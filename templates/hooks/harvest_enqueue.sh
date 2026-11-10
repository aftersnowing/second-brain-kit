#!/usr/bin/env bash
# SessionEnd hook — 이 세션이 claude_work 아래 실작업 파일을 고쳤으면 수확 큐에 적재한다.
# 적재만 하고 아무것도 요구하지 않는다. 다음 SessionStart가 이걸 꺼내 보여준다.
set -u
ROOT="$HOME/claude_work"
SBWT="$HOME/orca/workspaces/second_brain"
CWD="$(pwd -P)"
case "$CWD" in "$ROOT"|"$ROOT"/*|"$SBWT"/*) ;; *) exit 0 ;; esac

# 세션 인계 — 무엇을 논의 중이었나를 남긴다 (2026-10-08). 훅 stdin(transcript_path·cwd)을 그대로 넘긴다.
INPUT="$(cat 2>/dev/null || true)"
printf '%s' "$INPUT" | python3 "$ROOT/second_brain/scripts/session_handoff.py" end 2>/dev/null || true

Q="$ROOT/.ops/harvest_queue.jsonl"
mkdir -p "$ROOT/.ops"

# 최근 12시간 내 수정된 '실작업' 파일이 있는 최상위 디렉토리를 수집한다.
# 세션 상태·캐시·가상환경·산출 바이너리는 실작업이 아니다.
touched=$(find "$ROOT" -mindepth 2 -type f -mmin -720 \
    -not -path '*/.git/*'      -not -path '*/.venv/*' \
    -not -path '*/.omc/*'      -not -path '*/.omx/*' \
    -not -path '*/.idea/*'     -not -path '*/.ops/*' \
    -not -path '*/.claude/*'   -not -path '*/.openspace/*' \
    -not -path '*/node_modules/*' -not -path '*/__pycache__/*' \
    -not -path '*/.pytest_cache/*' -not -path '*/.playwright-mcp/*' \
    -not -name '*.pyc' -not -name '*.lock' -not -name '*.log' \
    -printf '%P\n' 2>/dev/null \
  | cut -d/ -f1 | sort -u | head -8 | paste -sd, -)

[ -z "$touched" ] && exit 0

ts=$(date -u '+%Y-%m-%dT%H:%MZ')
printf '{"ended":"%s","cwd":"%s","touched":"%s"}\n' "$ts" "${CWD#$ROOT/}" "$touched" >> "$Q"

# 큐가 무한정 자라지 않게 최근 20건만 유지
tail -20 "$Q" > "$Q.tmp" && mv "$Q.tmp" "$Q"
exit 0
