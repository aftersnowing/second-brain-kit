# 설정 · 정답지 파일 형식 — 가짜 행 견본

> 2026-11-10 운영 판의 파일 구조를 옮기고 값은 전부 지어낸 것으로 채웠다(「선박 A」 · 「거래처 X」 · `mail:1/100` 등).
> 사람이 고치는 표는 **근거 열(`source`)을 둔다** — 틀린 행을 고칠 때 무엇을 믿었는지 남긴다. 메일 서술은 표에 넣지 않는다.

## 1. 사람이 정하는 표

### 1.1 담당 범위 `docs/my_scope.yaml` — 요약 · 깊게 읽기의 「관련도」 재료

```yaml
# 근거: 담당 분장 메일 mail:<폴더>/<번호> (YYYY-MM-DD). 틀리거나 빠진 대상은 여기서 고친다 — 다음 갱신부터 반영
owner: "○○팀 ○○○ 매니저(○○ 담당)"
groups:                      # 거래처 → 담당 대상 목록
  거래처 X: ["선박 A", "선박 B"]
  거래처 Y: ["선박 C"]
topics: ["연료 소모 분석", "성능 보증", "규제 배출 계산"]
```

### 1.2 용어집 `docs/glossary.yaml` — 한국어 서술 → 메일의 영문 용어 (검색 재작성)

```yaml
- en: "Speed-FOC Curve"                        # 메일에 실제로 적힌 표기(재작성에 쓰임)
  alias: ["speed consumption curve", "FOC curve"]
  ko: "속력별 연료소모 곡선"                    # 사람이 쓰는 말(검색어에는 넣지 않음 — rules · blueprint 5.5)
- en: "Hull Fouling"
  alias: ["fouling", "hull condition"]
  ko: "선체 오손"
```

### 1.3 업무 성격 목록 `docs/segments/topics.json` — 닫힌 목록(LLM 은 이 key 만 고름)

```json
[
  {"key": "perf_claim", "label": "성능 · 연료 클레임", "sub": ["보증 초과", "정산"], "areas": ["성능", "계약"]},
  {"key": "regulation", "label": "규제 · 배출", "sub": ["배출 보고", "검증"], "areas": ["규제"]},
  {"key": "admin", "label": "행정", "sub": ["교육", "총무"], "areas": ["행정"]},
  {"key": "etc", "label": "기타", "sub": [], "areas": []}
]
```

### 1.4 대상 → 거래처 대응표 `docs/segments/charter_map.csv`

```csv
imo,vessel,charterer,start,end,source
1000001,선박 A,거래처 X,2024-03-25,,계약 위키 거래처 X 페이지
1000002,선박 B,거래처 X,2024-03-25,2026-06-30,mail:1/100
,선박 C,?,2024-03-25,,후보: 거래처 Y(근거 1개)
```
KST 양끝 포함 · 빈 종료일 = 현재 · 겹치면 늦은 시작 우선 · 근거 없으면 `?`.

### 1.5 외부 도메인 → 거래처 `docs/segments/org_domains.csv` · 유형 `vessel_types.csv` · 역할 `roles.csv`

```csv
domain,charterer
example-charterer.com,거래처 X
```
```csv
vessel,ship_type,source
선박 D,유형 1,자산 목록 파일
```
```csv
addr,name,role,source
boss@example.com,○○○,팀장,mail:1/101
notice@example.com,사내 공지,공지,mail:1/102
```
역할: `팀장` · `실장`(요청이면 1단) · `공지`(공지 판정). 개인 발신자의 공지 역할은 근거 없이 넣지 않는다.

### 1.6 조치 · 관점 목록 `docs/perspective/levers.json` — 관점 정리

```json
{
  "version": "YYYY-MM-DD",
  "views": [
    {"key": "fuel", "name": "연료 · 성능", "words": ["FOC", "연료 소모", "overconsumption"]},
    {"key": "maint", "name": "정비", "words": ["maintenance", "정비", "dry dock"]},
    {"key": "cost", "name": "운영비", "words": ["OPEX", "비용"]}
  ],
  "directions": ["좋음", "나쁨", "조건부"],
  "conditions": ["기간", "적재 상태", "기상"],
  "levers": [
    {"key": "cleaning", "kind": "single", "name": "수중 청소", "decision": "청소를 할 것인가",
     "baseline": "청소하지 않음", "words": ["hull cleaning", "수중 청소"],
     "situations": ["장기 정박 뒤"], "views": ["fuel", "maint", "cost"]}
  ]
}
```
`kind`: `single`(할까 말까) · 선택지형(`options` 목록 중 from → to).

### 1.7 샌드박스 분류 `docs/sandbox/topics.csv`

```csv
경로,업무 성격,용선주,이름,찾는 말
cases/260101_선박A_성능검토,성능 · 연료 클레임,거래처 X,선박 A 성능 검토,
main_code/old_notebook/분석1,성능 · 연료 클레임,거래처 X,,
ops/dashboard,운영 서비스,,,
second_brain/research,미분류,,,
```
가장 긴 경로가 이긴다 · 업무 성격 「운영 서비스」 행은 진열하지 않음 · 그 아래 건은 더 긴 경로 행으로 살린다.

## 2. 채점 정답지

### 2.1 검색 회상 `evidence/search_benchmark.json` — 고유명사 없는 사람 말투 질의

```json
[
  {"set": "dev", "query": "발전기 연료 계통에 저유황유 넣는 문제 논의했던 메일",
   "thread_id": "<스레드 키>", "n_msgs": 6, "subject": "<제목>", "first_utc": 1726000000}
]
```
`set`: `dev` · `heldout` · `blind`(한 번 보면 heldout 으로 강등하고 새로 뽑음).

### 2.2 요청 감지 `docs/open_loop_eval*.json`

```json
{
  "_doc": "모집단 · 창 · 라벨 정의를 여기에 — 다음 판과 비교할 수 있게",
  "built": "YYYY-MM-DD", "window": ["YYYY-MM-DD", "YYYY-MM-DD"], "window_days": 30, "frame": 1,
  "counts": {"request": 1, "meeting": 1, "other": 1},
  "items": [
    {"ptr": "mail:1/100", "date": "YYYY-MM-DD", "who": "거래처 X 담당", "subject": "<제목>", "label": "request", "why": "보고서 검토 회신(≤40자)"},
    {"ptr": "mail:1/101", "date": "YYYY-MM-DD", "who": "사내", "subject": "<제목>", "label": "meeting"},
    {"ptr": "mail:1/102", "date": "YYYY-MM-DD", "who": "뉴스레터", "subject": "<제목>", "label": "other"}
  ]
}
```
모집단: 내가 받는사람(to)인 수신 메일이 있는 정규화 제목마다 창 안 최근 한 통 — 전수. 라벨: `request` 내 할 일이 생기는 요청 · `meeting` 일정 참석 요청 · `other` 나머지.

### 2.3 건 라우팅 `docs/work_routing_eval.json`

```json
{"_doc": "메일 → 붙일 작업 건 정답",
 "positive": [{"mail": "1/100", "topic": "성능 검토 요청", "accept": ["cases/260101_선박A_성능검토"], "evidence": "회신 초안이 그 건 산출물을 인용"}],
 "negative": [{"mail": "1/103", "topic": "사내 행사"}]}
```

### 2.4 질문 창 `docs/ask_eval.json` · `docs/ask_eval_graph.json`

```json
{"version": 1, "as_of": "YYYY-MM-DD",
 "items": [{"id": "S1-01", "q": "선박 A 성능 검토는 지금 누구 차례인가?", "expected": "거래처 X 회신 대기(MM-DD 우리 송부)",
            "ptrs": ["mail:1/100"], "page": "vessels/선박-a", "has_card": true}]}
```
그래프판은 `cards`(근거 카드 키) · `hub`(중심 개체)를 더한다. `as_of` 뒤에 입장이 바뀐 문항은 정답지를 고친다(낡은 정답지가 점수를 깎은 사례).

### 2.5 중요도 · 칸 `docs/tier_eval.json`

```json
{"version": 1, "created": "YYYY-MM-DD", "window": {"since_utc": 1760000000, "until_utc": 1762000000},
 "items": [{"ptr": "mail:1/100", "tier": 1, "cells": [["거래처 X", "선박 A"]], "judged_by": "user"}]}
```

## 3. 결과 기록 (자동으로 쌓이는 것 — 형식만)

| 파일 | 한 줄 형식 |
|---|---|
| `results/feedback.jsonl` | `{"ts": …, "kind": "relevance|research|card|hide", "tid": …, "value": …, "note": …}` |
| `results/draft_saves.jsonl` | `{"ts": …, "file": …, "subject": …, "to": […], "reader": …, "model_ptr": …, "body": …}` |
| `results/session_handoff.jsonl` | `{"ended": …, "cwd": …, "title": …, "first": …, "last": …, "mails": […], "outputs": […]}` |
| `results/attachments_pruned.jsonl` | `{"ts": …, "msg_id": …, "filename": …, "reason": …}` |
| `notes/YYYY-MM.md` | `- note:YYYY-MM-DD-NN · <kind> · <who> · [req] [due YYYY-MM-DD] — 본문` (닫으면 `done YYYY-MM-DD — 이유`) |
