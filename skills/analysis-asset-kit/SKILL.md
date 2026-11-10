---
name: analysis-asset-kit
description: 프로젝트·세션·대상이 바뀌어도 분석 산출물이 동일한 규격으로 나오게 할 때 사용. 도면 스타일·폰트 하한·레이아웃 린터·판정 임계·거부 사유 코드를 문서가 아니라 import 가능한 실행 자산으로 제공하고, 새 프로젝트 착수 의례와 세션 종료 시 지식 승격 의례를 규정. matplotlib 도면 제작, 검증 게이트 설계, 판정 표 작성에 선행해서 로드.
---

# 분석 실행 자산 키트

## 왜 이게 있는가

규범 문서만으로는 일관성이 나오지 않는다. 실제로 확인된 사례:

한 저장소 안에 스타일 모듈이 **4개** 공존했고 팔레트가 전부 달랐다. 그중 하나는 독스트링에
"ONE source of truth for color palette"라고 적혀 있었지만 실제로는 넷 중 하나였다. 같은
저장소에서 동일한 `_graduated_verdict(mean_abs, max_abs)`가 두 모듈에 각각 구현돼 있었고,
한쪽만 NaN을 `NO_DATA`로 막고 다른 쪽은 가드가 없어 NaN이 모든 비교를 통과해 **`PASS`**로
떨어졌다.

원인은 규범이 부실해서가 아니다. 규범이 **"…를 만들어라"로 끝나기** 때문이다. 새 프로젝트에는
만들 대상이 없으므로 매번 재구현하고, 재구현은 매번 다르다. 서술은 읽을 때마다 재해석되지만
**import는 재해석되지 않는다.**

그래서 이 스킬은 규범이 아니라 **구현체**를 배달한다. 판단 규범은 이웃 스킬에 있다 —
`analysis-plot-craft`(도면 설계) · `like-for-like-comparison`(대조 설계) ·
`technical-deliverable-craft`(산출물) · `analysis-project-operations`(운영) ·
`vessel-performance-analysis`(선박 각론). 이 스킬은 그 규범들이 **말한 것을 실제로 갖고 있다.**

## 배선

```python
import sys
sys.path.insert(0, "~/.claude/skills/analysis-asset-kit/assets")  # expanduser 필요

from analysis_kit import (
    tiers, configure, style_axis, ACCENT, SERIES, INK, MUTED, GRID, status_color,
    audit_figure, format_findings,
    Outcome, Reason, Rejected, Thresholds, graduated_verdict, check_support, check_range,
)
```

새 환경에서 처음 쓸 때 한 번:

```bash
python3 ~/.claude/skills/analysis-asset-kit/assets/test_analysis_kit.py   # 19/19
```

통과하지 않으면 쓰지 말 것. 테스트는 산수를 검사하는 게 아니라 **실제로 출고된 실수 하나씩**을
못 박고 있다.

**의존성은 절반만 있다.** 판정 계약(`Outcome`·`Reason`·`Thresholds`·`graduated_verdict`)은
순수 로직이라 항상 import된다. 도면 쪽(`style`·`layout`)만 matplotlib이 필요하며 **첫 사용
시점에 지연 로드**된다. 표만 검증하는 프로젝트나 matplotlib 없는 venv에서도 판정 계약은
그대로 쓸 수 있고, 도면 쪽을 부르면 그때 명시적 `ImportError`가 난다.

## 계약 1 — 폰트 하한은 상수가 아니라 삽입 배율의 함수

가장 자주 틀리는 지점이며, 한 저장소의 두 스타일 모듈이 갈라진 진짜 이유다. 하나는 도면이
곧 페이지였고(하한 10pt로 충분), 하나는 리포트에 0.72배로 삽입됐다(같은 10pt가 인쇄본에서
7.2pt). **둘 다 옳았고, 상수로 박았기 때문에 서로 틀렸다.**

```python
t = tiers(embed_scale=0.72)   # 리포트 본문 삽입용 → floor 12.5pt
t = tiers(embed_scale=1.0)    # 도면이 곧 페이지  → floor 9.0pt
configure(t); style_axis(ax, t)
```

`embed_scale`은 **가장 작게 들어갈 배율**을 넣는다. 도면은 최악의 배치만큼만 읽힌다.
어떤 티어도 `floor` 아래로 지정될 수 없다(테스트로 고정).

## 계약 2 — 렌더된 결과를 기계가 검사한다

```python
findings = audit_figure(fig, min_font_pt=t.floor, furniture_rules=(0.047, 0.955))
```

검사 7종: `empty_axes` · `text_overlap`(글자↔차트) · `text_collision`(글자↔글자) ·
`text_off_page` · `text_on_furniture` · `cell_clipped` · `font_below_floor`.

- `min_font_pt`에 **기본값이 없다.** 모듈 상수로 두면 리포트 본문용 도면이 조용히 통과한다.
- **결과는 반환하고 절대 raise하지 않는다.** 빌드를 중단시키는 린터는 꺼진다.
- `empty_axes`가 가장 조용한 실패다 — 선택자가 아무 행도 못 맞추면 빈 프레임이 남고 페이지는
  그대로 빌드되어 그대로 출고된다. 실제로 첫 전수 스윕이 **아무도 열어보지 않은 페이지**에서
  전 개체 부록 텍스트의 표 침범을 잡았다.
- 육안 확인은 린터 PASS 이후 최종 1회, 문제 영역만.

## 계약 3 — 거부는 수치로 세탁되지 않는다

분석은 답할 수 없는 지점에 정기적으로 도달한다(채널 사망·표본 부족·외삽·기준 불일치). 그걸
NaN이나 예외로 표현하면 표에 도달하기 전에 사라진다. NaN은 빈 칸으로 인쇄되고, 예외는 루프를
감싼 `try`가 삼킨다. 어느 쪽이든 **산출물이 갖지 않은 커버리지를 주장하게 된다.**

```python
reason = check_support(n_bins, n_min=8)
result = Outcome.rejected(reason) if reason else Outcome.ok(value)

f"{result:.2f}"     # → "12.35"  또는  "INSUFFICIENT_SUPPORT"
result.value        # 거부 상태면 Rejected 예외 — 조용히 못 쓴다
result.value_or(None)   # 계속 가려면 명시적으로. 이 호출부는 grep된다
```

사유 코드 4종: `NO_DATA` · `INSUFFICIENT_SUPPORT` · `OUT_OF_SUPPORT_RANGE` · `BASIS_MISMATCH`.

`Outcome.ok(nan)`은 거부한다. **NaN은 결과가 아니다.**

## 계약 4 — 임계는 산정 모집단과 함께 다닌다

공용 툴킷에서 일반화가 보장되지 않는 유일한 것이 임계값이다. 한 엔진군·계측기·계약에서
교정된 밴드는 다음 대상에 대해 아무것도 말해주지 않는다. 기본값을 숨기면 **아무도 확인하지
않은 모집단에서 자신 있는 PASS**가 나오고, 이건 크래시보다 나쁘다. 출고되기 때문이다.

```python
TH = Thresholds(warn=(5, 15), fail=(8, 30),
                source="<fleet> <ship type> M/E SFC, 15 hulls, 2026-07")   # source 필수
graduated_verdict(mean_abs, max_abs, thresholds=TH)   # NaN → "NO_DATA", 결코 PASS 아님
```

프로젝트별 임계는 그 프로젝트 `docs/knowledge/`에 근거와 함께 기록한다. 키트의 몫이 아니다.

## 무엇을 굳히고 무엇을 인자로 두는가

대상마다 여건은 반드시 다르다(채널 사망·계측기 포화·샘플링 상이·계약 상이). 공유 코드가
제공하는 것은 단일 정답이 아니라 **실패하는 방식의 계약**이다.

| 굳힐 것 (결정론) | 인자로 둘 것 (적응) |
|---|---|
| 색 · 폰트 하한 산식 · 린터 검사 항목 | 어떤 채널을 쓸지 |
| 적합 **수식** | 사전분포 · 경계 · 임계 **값** |
| 판정 **형식** (PASS/WARN/FAIL/NO_DATA) | 축 선택 |
| 거부 사유 코드 체계 | 폴백 발동 여부 |

새 대상에서 함수가 "지지 부족"으로 거부하면 그건 버그가 아니라 **그 대상의 데이터 상태를
알려준 것**이다. 자작 코드는 조용히 틀리고 공용 코드는 시끄럽게 멈춘다.

## 색

무채색이 데이터를 나르고, **단 하나의 강조색이 요점을 나른다.**

- `ACCENT` — 계약·기준선, 주목 개체, 초과분. 한 도면에서 두 용도로 쓰면 의미가 파괴된다.
  그럴 땐 패널을 나눈다.
- `SERIES` — 강조하지 않는 계열 4단(진→연). 5개를 넘으면 회색 분리가 실패하며, 그건 색을
  추가하라는 신호가 아니라 **컬러바 또는 패널 분할**로 가라는 신호다.
- `STATUS` — 판정 칩·표 셀 **전용**, 곡선에 쓰지 않는다. 색 옆에 판정 단어를 항상 함께 인쇄한다.

## 의례

- **착수** — 새 프로젝트 첫 30분: `references/bootstrap.md`
- **수확** — 세션 종료 시 승격 판정: `references/harvest.md`

수확 의례가 이 스킬의 존속 조건이다. 돌지 않으면 키트는 5번째 변종이 되고, 이 문서 맨
위의 실패가 그대로 재현된다.

## 쓰지 않는 경우

- **일회성 탐색 스크립트** — 납품 경로가 아니면 강제하지 않는다.
- **이미 자체 스타일 체계가 확립된 기존 저장소** — 그쪽 모듈을 쓴다. 키트를 끼워 넣으면
  변종이 하나 더 늘 뿐이다. 키트의 첫 고객은 **신규 작업**이다.
