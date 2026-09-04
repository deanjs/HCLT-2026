# 스텝별 하네스 스냅샷 (읽기 전용)

각 실험을 **그 당시 돌렸던 하네스**의 `src/`를 그대로 떠 놓은 것이다.
`scripts/verify_harness_equivalence.sh`가 이것과 현재 `src/`를 비교해,
통합 하네스가 같은 실험 입력을 만드는지 검증한다.

## 왜 파일로 두는가

스텝마다 하네스가 갈라져 있었고(9~10개 파일 전부 다름), 그것들을 합친 것이
지금 `src/`다. "코드를 고쳤으니 결과가 달라지는 것 아니냐"에 답하려면 그때
코드가 있어야 한다.

예전에는 스텝 브랜치를 `git archive`로 꺼내 썼으나, **브랜치를 `main` 하나로
정리하면서 파일로 박제**했다. 이제 저장소 하나로 검증이 끝나며 네트워크도
브랜치도 필요 없다.

## 출처

| 폴더 | 원래 브랜치 | 커밋 |
|---|---|---|
| `step1_cliff/` | `step1/cliff` | `COMMIT` 파일 참조 |
| `step2_code-observe/` | `step2/code-observe` | 〃 |
| `step3_code-cause/` | `step3/code-cause` | 〃 |
| `step4_instr-observe/` | `step4/instr-observe` | 〃 |
| `step5_instr-cause/` | `step5/instr-cause` | 〃 |

각 폴더의 `COMMIT`에 원본 커밋 SHA가 들어 있다. 브랜치는 삭제됐으므로 이
파일들이 유일한 사본이다. **수정하지 않는다.**
