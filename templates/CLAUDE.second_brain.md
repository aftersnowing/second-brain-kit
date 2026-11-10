# second_brain — 운영 규율 (견본)

<!-- 지식 시스템 저장소 루트의 CLAUDE.md 견본. <…> 는 새 조직 값으로 채운다.
     이 파일은 규칙과 위치만 둔다. 경위 · 실측 · 수치는 docs/operations_reference.md(같은 절 이름).
     규칙을 바꾸면 여기 한 줄을, 이유 · 수치는 그 문서의 절을 고친다. 가볍게 둔다. -->

개인 업무메일(<메일 시스템> `<내 주소>`) 지식베이스, <시작일>~현재. 규모는 `python3 scripts/ask.py stat`.
**분류 `platform`** — 여러 건이 계속 조회하는 자산. 건별 작업은 여기에 쓰지 않는다.

## 3층 구조
`input_files/raw/` 불변 원자료(수정 금지, 재파싱은 여기서) → `results/brain.sqlite` 검색 층 → `wiki/` 컴파일 층.

## 격리 규율 — 이것부터
- 메일 본문은 조직 자산. 이 디렉토리 밖으로 서술을 내보내지 않는다. 위키에는 요약 · 판정 + 근거 `mail:<폴더>/<번호>` 만.
- 개인정보(전화 · 주소 · 서명 블록) 금지. 서버는 127.0.0.1 에만.
- 예외(사용자가 정한 것만 여기에): 작업 지시서로 넘길 때 요청자 · 요구 항목 · 기한 · `mail:` 까지.

## 오케스트레이션 — 메일 ↔ 작업 루프
메일 수신 → ①감지 → ②라우팅 → ③작업 → ④초안 → 사람 발송 → ⑤종결.
- 제안만, 실행은 승인 후: 새 건 착수 · 대장 등재는 사용자 승인 뒤.
- 메일은 보내지 않는다 — 마지막 단계는 임시보관함 저장(`save_draft.py`, 발송 경로 없음).
- 산출물 md 에는 「요청: `mail:…`」 줄과 「**제목**:」 줄을 반드시 둔다.
- 작업 폴더 산출물은 읽기만. 수치는 위키로 옮기지 않고 건 · 판본과 함께 인용.
- 시스템 초안은 메일 코퍼스가 아니다: 새 소비처도 `AND m.id NOT IN (SELECT msg_id FROM unsent)`.
- 갱신은 한 번에 하나(`results/refresh.lock`). 수집 · 색인은 바뀐 것만.
- 밀어내기는 변화만 · 하루 1회 · 회차당 토스트 1개.

## 메일 밖 입력
`python3 scripts/note.py add "…" --kind 지시 --who 이름 [--req] [--due YYYY-MM-DD]` — `note:` 는 `mail:` 과 같은 자격의 근거. 끝나면 `done --why`.

## 판정 채점표 — 규칙을 고치면 숫자를 다시 잰다
| 무엇 | 채점 | 현재 |
|---|---|---|
| 검색(회상) | `scripts/eval_search.py --all` | <기준선> |
| 요청 감지 | `scripts/eval_open_loops.py` | <정밀도/재현율> |
| 건 라우팅 | `scripts/work_index.py --eval` | <상위3 · 상위1> |
| 질문 창 | `scripts/eval_ask.py` | <n/30> |
| 초안 변경률 | `scripts/eval_drafts.py` | <첫 판 → 발송 %> |

## 자가발전 장치
- 워크트리에서도 같은 뇌(`sbpaths.py`) · 쓰기(수집 · 색인 · 카드 · 그래프)는 main 에서만.
- 세션 인계 `results/session_handoff.jsonl` — 「하던 얘기」는 여기부터. 메모리 위생 `lint_memory.py`(보고만, 정리는 승인 뒤).
- 초안 md: 본문 = 머리 블록 뒤 첫 `---` 다음. 저장 관문: 본문 200자 이상이면 `독자` · `본보기` · `점검` 세 줄.
  쓰기 전에 `ask.py draft --to "<이름>" --about "<주제>"`. 고친 판을 저장하면 이전 판은 바로 휴지통.
- 위키 쓰기 문체: 맨 위 `## 한눈에` 5불릿 이내 · 통계 해설 · 경위 · 중복 · 기본 용어 풀이 금지.
- 위키 갱신은 세션에서 — 갱신 회차는 후보 목록만. 자동 장치가 wiki 를 고치면 그 경로만 바로 커밋.
- 대시보드(<포트>): 판단 요구는 최소 · 처음부터 분류된 상태 · 펼치면 바로 내용 · 판정 배지 없음.
- 기능별 모델: Opus = 깊게 읽기 · 긴 카드 · 회신 · 관점, Sonnet = 짧은 카드 · 질문 창 · 요약 · 분류, Haiku = 공지 거르기. 못 부르면 실패로 남기고 낮은 모델로 넘어가지 않는다.
- 스레드 카드: 있는 카드를 처음부터 다시 만들지 않는다 — 새 메일만 이어 고친다.

## 버전 관리 · 백업
- git 은 로컬 전용(반출 결정은 사용자). 대상 scripts · docs · wiki · outputs · evidence · notes · CLAUDE.md, 커밋은 경로 명시.
  `input_files/raw` · `attachments` · `results/` · `wiki/stale|inbox|loop.md` 는 `.gitignore`.
- 백업 매일 <시각> → <백업 위치>. 첨부 · 첨부 본문 · 자격증명은 백업하지 않는다.

## 위키 운영규칙 (load-bearing schema)
- type: `vessel`(대상) / `org` / `person` / `case` / `work` / `index` / `log`. frontmatter 필수 `name, type, title, description, updated, sources, relations`.
  `name` = 파일명. `sources` 는 `mail:` · `note:` 만(works 는 `work:` · `session:` 도). LINT 가 실존을 검사한다.
- 관계어휘 10종 고정: `INVOLVES`, `COUNTERPART`, `RAISED-BY`, `PENDING-ON`, `RESOLVED-BY`, `RELATES-TO-CASE`, `CONTRASTS-WITH`, `SUPERSEDES`, `DERIVED-FROM`, `EVIDENCE`.
- 근거 권위: 메일 원문 > 스레드 요약. 추론은 `(추정)`. 모순은 지우지 말고 `SUPERSEDES`, 나중 메일 우선. `## 미결` 은 `open_loops` 에서.
- LINT(`scripts/lint_wiki.py`) — ISSUE 가 하나라도 있으면 인용 불가. 끊긴 `[[링크]]` 는 결함이 아니라 WANTED.
- 세션 시작: 메일 질의는 먼저 `wiki/index.md` 와 해당 페이지, 개체가 걸리면 `ask.py ctx <이름>`. 한꺼번에 만들지 않는다.

## 갱신이 저절로 되지 않는다는 것
`wiki/stale.md` 는 매 LINT 마다 재계산되는 파생물이다. 비우는 길은 페이지 갱신 + `updated:` 올리기뿐. 남은 페이지는 작성 시점의 사실.
