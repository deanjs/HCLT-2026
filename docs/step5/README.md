# step5 — 지침 인과 (RQ3 인과)

| 읽을 순서 | 문서 | 무엇 |
|---|---|---|
| 1 | [`방법론.md`](방법론.md) | **방법과 순서** — 왜 하나 · 지시어 치환 · 통제 공여 2종 · 순효과 |
| 2 | [`results.md`](results.md) | **결과와 해석** — 결과 JSON 읽는 법 · 층별 표·그림 · 다음 실험으로 |

```
방법론.md      방법 — 왜·무엇을·수식·데이터·한계
results.md     결과 — JSON 읽는 법 · 표 · 해석 · 그림 · 다음 실험으로
figures/       그림 (explain_* = 이해용 · 나머지 = 논문용, pdf+png)
```

| | |
|---|---|
| **묻는 것** | 지침을 덮어쓰면 행동이 바뀌는가, 바뀐다면 Key인가 Value인가, 어느 층인가 |
| **결과 원본** | `results/step5_instr-cause/` 336 · `step5_control_sweep_<모델>/` 672(전 층 통제) · `step5_instr-cause-control/` 2,016(옛 단일 층, 쓰지 않는다) — 불변(CLAUDE.md §6) |
| **논문** | 그림 2 세로 파선 · 그림 3 (나) · 표 |
| **다음** | 코드도 지침도 Value·단일 층으로 수렴했다. 그렇다면 거기를 밀면 되살아나야 한다 → [`../step6`](../step6) |

## 실행 순서 — 본실험 하나 + 보강 둘

| 순서 | 노트북 | 결과 | 왜 |
|---|---|---|---|
| ① | `step5_instr-cause.ipynb` | `step5_instr-cause/` 336 | 본실험 — 지시어를 반대 표기로 덮어 전 층 스윕 |
| ② | `step5_instr-cause-control.ipynb` | `step5_instr-cause-control/` 2,016 | 통제 — 같은 지시어로 덮어 **덮어쓰기 자체의 효과**를 잰다 |
| ③ | `step5_instr-cause-control-sweep.ipynb` | `step5_control_sweep_*/` 672 | ②를 전 층으로 확장 — 층별 순효과 곡선용 |

②를 봉우리 층 한 곳에서만 재던 때는 층별 곡선을 만들 수 없었다. ③으로 같은 조건을 전 층에서
다시 쟀고, **네 모델 모두 그 층이 실제 봉우리**로 확인됐다. 논문에 실린 지침 순효과는 **①−③**이다.

```bash
python scripts/step5_net_effect.py    # 전 층 스윕을 자동으로 찾는다 (논문 표)
python scripts/step5_figures.py       # net_<모델>.png(층별 지침 몫) 포함
```

두 폴더를 한 폴더처럼 섞어 읽으면 층 구성이 다른 실행분이 조용히 덮인다.
`step5_net_effect.py`는 그런 중복을 만나면 예외를 던진다.
