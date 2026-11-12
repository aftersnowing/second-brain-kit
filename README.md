# second brain 이식 키트

개인 업무 메일 · 회의 메모 · 작업 산출물을 한곳에 모아 사람과 AI 세션이 같은 기억으로 일하게 하는 시스템을,
**다른 조직에서 다시 세우기 위한 문서 묶음**. 2026-11-10 운영 판에서 뽑았다.

- 코드는 들어 있지 않다 — 설계도 · 프롬프트 · 규칙으로 그 조직 메일 · 폴더에 맞춰 다시 짠다(AI 코딩 도구로).
- 조직 자료(메일 · 위키 · 카드 · 산출물 · 정답지) · 고유명 · 개인정보는 들어 있지 않다.

## 무엇이 들어 있나

| 파일 | 내용 | 쓰는 때 |
|---|---|---|
| [`blueprint.md`](blueprint.md) | 설계도 — 원칙 · 구조 · 수집 인터페이스 · DB 스키마 · 판정 로직 · 지식 층 · 루프 · 화면 · LLM 규칙 · 운영 · 채점 · 실패 교훈 · 이식 체크리스트 · 다시 세우는 순서 | 처음에 전부 · 단계마다 해당 절 |
| [`prompts.md`](prompts.md) | LLM 프롬프트 16개 원문(고유명만 자리 표시) + 공통 규칙 + 코드 쪽 검사 | 카드 · 질문 창 · 요약 · 관점 · 위키 제안을 만들 때 |
| [`rules.md`](rules.md) | 판정 규칙 — 요청 감지 · 중요도 · 종결 · 본문 정리의 정규식 원문, 기준값과 이유, 고치는 절차 | 미결 · 중요도 · 루프를 만들 때 |
| [`working_principles.md`](working_principles.md) | 사용자 피드백에서 추린 작업 원칙(AI 세션 · 분석 · 글 · 화면 · 보안 · 여러 세션) | 사용자 레벨 규칙 · 메모리의 씨앗 |
| [`schema.sql`](schema.sql) | DB 6개의 정확한 DDL(테이블 · 색인 · FTS 정의, 내용 없음) | 1단계 적재 · 색인을 만들 때 |
| [`data_formats.md`](data_formats.md) | 사람이 정하는 표 7종 · 채점 정답지 5종 · 자동 기록 파일의 형식(가짜 행 견본) | 설정 · 정답지를 만들 때 |
| [`requirements.txt`](requirements.txt) | 외부 패키지 16종과 확인한 버전 + 패키지 밖에서 필요한 것 | 설치 때 |
| [`skills/`](skills/) | 자체 스킬 7개(건 착수 · 분석 자산 키트 · 대조 · 도면 · 산출물 · 장기 운영 · 피드백 왕복) | `~/.claude/skills/` 에 복사 |
| [`templates/`](templates/) | 규칙 파일 견본 3종(사용자 레벨 · 작업 폴더 · 지식 시스템) · 작업 대장 · 작업 지시서 · 작업 이력 페이지 · 세션 훅 3개 + 훅 등록 견본 · systemd 단위 16개 + 실패 알림 설정 · 화면 기본 틀(CSS) · HTML 금지 표현 목록 | 설치 때 |

## 읽는 순서

1. `blueprint.md` 0~3절 — 무엇이고 왜 이렇게 생겼나.
2. `blueprint.md` 13절(겪은 실패 → 둔 장치) — 같은 실수를 처음부터 피하려면.
3. `blueprint.md` 14 · 15절 — 바꿔 끼울 곳과 순서.
4. 단계마다: 해당 절 + `prompts.md` / `rules.md` 의 해당 부분.

## 새 조직에서 세우는 법

1. **0단계 결정** — 메일 접근 경로(표준 API 가능 여부 타진 → `evidence/` 에 기록) · 로컬 전용 · LLM 사용 범위 · 발송 금지 · 원격 저장소 여부.
2. **작업 환경**
   - `pip install -r requirements.txt` · `playwright install chromium` · AI 코딩 도구 CLI 설치 · `loginctl enable-linger $USER`
   - `skills/*` → `~/.claude/skills/`, `templates/CLAUDE.user.md` → `~/.claude/CLAUDE.md`
   - `templates/CLAUDE.workspace.md` → 작업 폴더 루트 `CLAUDE.md`, `templates/LEDGER.md` → `LEDGER.md`
   - `templates/hooks/ledger_context.sh` · `harvest_enqueue.sh` → 작업 폴더 `.ops/`, `compact_reorient.sh` → `~/.claude/hooks_compact_reorient.sh`,
     `templates/settings.hooks.example.json` 의 `hooks` 를 `~/.claude/settings.json` 에 합침(경로만 고침)
   - `working_principles.md` 에서 맞는 것을 사용자 레벨 규칙 또는 메모리로
3. **지식 시스템 저장소** — 새 git 저장소 `second_brain/` + `templates/CLAUDE.second_brain.md` → `CLAUDE.md`(자리 표시 채움).
   DB 는 `schema.sql` 그대로, 설정 · 정답지는 `data_formats.md` 형식으로, 화면 틀은 `templates/ui_shell.css`, HTML 관문 금지 표현은 `templates/slop_terms.tsv`.
4. **단계별 구현** — `blueprint.md` 15절 순서로 AI 코딩 도구에 한 단계씩 맡긴다. 예:

   ```
   docs/portable/blueprint.md 의 4절(수집 층)과 5절(원자료 · 검색 층)을 읽고 15절 1단계를 구현해줘.
   메일 연결부는 <Microsoft Graph API / Gmail API / IMAP>로, 4.3 의 인터페이스를 지키고
   원자료는 input_files/raw/{meta,body}/*.jsonl 로 낸다. 5.2 스키마 그대로, FTS 2종까지.
   완료 기준: 첫 메일부터 결손 0 확인 + ask.py search · thread · stat 동작.
   ```

5. **단계마다 채점** — 정답지를 그 조직 메일로 **색인 · 규칙보다 먼저** 만든다(`blueprint.md` 12절). 숫자가 안 오르면 그 단계를 가볍게 두고 다음으로.
6. **자동 작업** — `templates/systemd/` 를 `~/.config/systemd/user/` 에 복사, `%h/second_brain` 경로 · 일정 · 알림 스크립트를 고친 뒤 `systemctl --user enable --now <타이머>`.

## 원 시스템과의 관계

- 원본: 원 시스템 저장소의 `docs/portable/`(이 폴더). 거기서 고치고 이 저장소로 내보낸다.
- `blueprint.md` 가 가리키는 `CLAUDE.md` · `docs/operations_reference.md` · `scripts/*.py` 는 원 시스템의 파일 이름이다 — 새로 짤 때 같은 이름을 쓰면 문서와 코드가 맞는다.
- 수치(채점 기준선 · 실측 시간)는 원 시스템 2026-11 기준. 새 조직에서는 새로 잰다.

## 내보낼 때마다

1. 원 시스템에서 `python3 scripts/kit_leakscan.py` — 고유명 사전(대상 · 거래처 · 사람 이름 · 도메인)과
   메일 포인터 · 주소 · 전화번호 꼴로 이 폴더 전체를 검사, 0건(rc 0)일 때만.
2. `rsync -a --delete --exclude .git --exclude .gitignore --exclude .omc docs/portable/ <이 저장소>/` → 커밋 → 올림.
