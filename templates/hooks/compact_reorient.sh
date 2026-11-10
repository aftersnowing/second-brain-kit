#!/usr/bin/env bash
# compact 직후 역할 재정렬 (2026-10-05) — 요약이 빠뜨린 것을 파일에서 되찾게 한다.
case "$PWD" in
  "$HOME/second_brain") echo "[compact 직후] 규칙 파일(CLAUDE.md)과 자기 작업의 인계 문서를 다시 읽고 이어서 하라.";;
  "$HOME"/worktrees/*) echo "[compact 직후] 상시 규칙 문서와 자기 진행 기록의 「이어받기」 절을 다시 읽고 이어서 하라.";;
esac
