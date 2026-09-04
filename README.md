# 코드 생성 모델은 왜 표기 규약 지침을 어기는가

`camelCase`로 써 달라고 분명히 지시해도, 코드 생성 모델은 자주 `snake_case`로 답한다.
이 저장소는 **그 실패가 어디서 오는지**를 모델 내부를 열어 확인한 실험 기록 전체다.

HCLT 2026 투고 논문의 재현 자료다. 결과 원본 JSON, 실행 노트북, 집계·작도 스크립트,
스텝별 방법론 문서가 모두 들어 있다.

## 한 문단 요약

지침을 어기는 이유는 모델이 지침을 **덜 봐서가 아니다.** 모델은 지침 지시어를
제대로 주목하고 있다(step4). 문제는 **무엇을 보느냐(어텐션)가 아니라 무엇을
받아오느냐(Value)** 에 있고, 그것도 **후반의 특정 층 한 곳**에 몰려 있다
(step3·step5). 그래서 어텐션을 키우는 기존 처방(Spotlight)은 듣지 않고,
Value를 직접 조향하면 준수가 회복된다(step6).

## 연구 질문

| | 질문 | 답한 스텝 |
|---|---|---|
| **RQ1** | 앞선 코드의 규약 위반이 준수율을 떨어뜨리는가 | step1 |
| **RQ2** | 코드 신호는 형태(어텐션)인가 내용(Value)인가, 어느 층인가 | step2(관측) · step3(인과) |
| **RQ3** | 지침의 영향력도 같은 통로를 지나는가 | step4(관측) · step5(인과) |
| **처방** | 그렇다면 무엇을 고쳐야 하는가 | step6 |

## 실험 스텝

각 폴더에 `방법론.md`(왜·무엇을·수식·한계) · `code.md`(개념↔코드) ·
`results.md`(결과·해석·그림) · `figures/`가 있다. **`docs/<스텝>/README.md`부터 읽으면 된다.**

| 스텝 | 무엇을 했나 | 문서 | 결과 원본 |
|---|---|---|---|
| **step1** | 앞선 코드에 위반 이름을 늘려 가며 준수율을 잰다 | [`docs/step1`](docs/step1) | `results/step1_cliff/` 4,368개 |
| **step2** | 코드 신호를 어텐션·Value로 나눠 관측한다 | [`docs/step2`](docs/step2) | `results/step2_code-observe/` 334개 |
| **step3** | 층별로 Key/Value를 바꿔치기해 인과를 확인한다 | [`docs/step3`](docs/step3) | `results/step3_code-cause/` 504개 |
| **step4** | 모델이 지침 지시어를 실제로 보는지 관측한다 | [`docs/step4`](docs/step4) | `results/step4_instr-observe/` 336개 |
| **step5** | 지침 신호를 덮어써 인과를 확인한다 | [`docs/step5`](docs/step5) | `results/step5_instr-cause/` 336개 · `-control/` 2,016개 · `control_sweep_*/` 672개 |
| **step6** | 값 조향과 Spotlight를 같은 자 위에서 겨룬다 | [`docs/step6`](docs/step6) | `results/step6_steer/` 2,184개 · `-generate/` 756개 · `-crosslayer/` 336개 |
| **진단 A** | 측정 장치 자체를 검사한다 (실험 아님) | [`docs/diag`](docs/diag) | `results/diag_kv-phase/` 72개 |

### 읽기 전에 알아 둘 것

- **step2의 주요 결론은 철회했다.** "모델이 문맥의 위반 이름을 더 참조한다"는 관측은
  표기 배치가 시드로 고정된 데서 온 **자리 효과**였다. 배치를 뒤집어 다시 재자 부호가
  뒤집혔다. 폐기하지 않고 [`docs/step2/results.md`](docs/step2/results.md) §3-6에 경위를
  그대로 남겼다. 인과 스텝(step3·5·6)은 처치와 통제가 같은 자리를 건드려 이 교란을 받지 않는다.
- 스텝마다 `구조적_결함.md`가 있다. 그 시점에 발견한 방법론적 약점을 적어 둔 감사 기록이다.

## 고정 설정

| 축 | 값 |
|---|---|
| 모델 4개 | Qwen2.5-Coder-3B(기준) · deepseek-coder-6.7b · Llama-3.2-3B · stable-code-3b |
| 데이터 | 함수 이름 504개 (동사 50 × 명사 50), 12개씩 42묶음 |
| 무작위 고정값 | 42 |
| 내부 값 치환 | 평균 덮어쓰기(mean-pool) — 토크나이저 무관, 코드·지침 동일 |
| 언어 | **전 스텝 파이썬.** 하네스는 자바스크립트도 지원하나 JS 결과는 0개다 |

`transformers` 버전을 **고정한다.** KV 캐시 레이아웃이 버전마다 갈리는데 이 실험은 그
자료구조를 직접 편집하므로, 버전이 바뀌면 개입 대상 자체가 달라진다. 실제로 쓴 버전은
결과 JSON의 `meta`에 자동 기록된다.

## 저장소 구조

```
src/harness/     실험 엔진 — 모든 스텝이 조건값만 바꿔 이 단일 진입점을 부른다
  conditions.py    조건 스키마 (단일 진실 공급원)
  runner.py        run() — 조건을 받아 실행하고 결과를 저장
  intervention.py  KV 치환 · 조향
  attention_probe.py  어텐션 · Value 관측
notebooks/       Colab 실행 노트북 — 스텝당 하나, 모델 하나씩, 끊기면 이어서
scripts/         집계·작도 (결과 JSON → 표·그림). 결과를 고쳐 쓰지 않는다
results/         결과 원본 JSON 11,914개 — 불변
docs/            스텝별 방법론·코드·결과 문서와 그림
tests/           엔진 테스트
```

**`results/`는 불변이다.** 한 번 저장한 결과 JSON은 덮어쓰지 않는다. 값이 바뀌어야 하면
다시 실행해 새 폴더에 쓴다. 집계와 작도는 `scripts/`의 스크립트로만 한다.

## 재현

```bash
pip install -r requirements.txt      # 버전 고정 — 반드시 이 목록대로
pytest                               # 엔진 테스트
```

결과 JSON에서 논문의 표와 그림을 다시 만들려면 (모델 없이, CPU로 돈다):

```bash
python scripts/step1_reaggregate.py results/step1_cliff
python scripts/step3_net_effect.py  results/step3_code-cause  --figs docs/step3/figures
python scripts/observe_per_token.py results/step4_instr-observe
python scripts/step5_reaggregate.py results/step5_instr-cause --figs docs/step5/figures
python scripts/step6_summary.py --figs docs/step6/figures
```

결과 JSON을 처음부터 다시 만들려면 GPU가 필요하다. `notebooks/`의 노트북을 쓴다.
무료 티어(T4) 기준으로 설계했고, 노트북 하나가 모델 하나만 다루므로 런타임이 끊겨도
그 모델만 다시 돌리면 된다. 이미 저장된 조건은 건너뛴다.

## 파일 이름 읽는 법

결과 파일 이름 하나로 조건이 복원된다.

```
qwen2-5-coder-3b-instruct__pre-c0of12-pool-syn-b0__ins-pos-camel-w__int-none__s42.json
└─ 모델 ─────────────────┘  └─ 앞선 코드 ────┘  └─ 지침 ──┘  └ 개입 ┘ └시드┘
```

`pre-c0of12` = 앞선 12개 중 위반 0개 · `ins-pos-camel` = camelCase를 쓰라는 지침 ·
`int-none` = 개입 없음 · `s42` = 시드 42. 자세한 정의는 [`docs/코드_하네스공통.md`](docs/코드_하네스공통.md).

## 브랜치

논문 자료는 전부 `main`에 있다. 나머지 브랜치는 실험을 돌리던 당시의 기록이며,
그 시점의 코드와 중간 결과를 보존하기 위해 남겨 두었다.
