<h1 align="center">🐫 vs 🐍 Instruction-Following Failures in Code Generation Language Models:<br>Separating Attention Allocation from the Value Path</h1>

<p align="center">
  Jeongseok Han<sup>°</sup> · Jaehyung Seo<sup>*</sup><br>
  Department of Computer Science and Engineering, Konkuk University<br>
  <code>{king8470, seojae777}@konkuk.ac.kr</code>
</p>

<p align="center">
  <b>HCLT 2026</b> · 제38회 한글 및 한국어 정보처리 학술대회<br>
  코드 생성 언어모델의 지침 준수 실패: 어텐션 배분과 Value 경로의 분리
</p>

<p align="center">
  <a href="paper.pdf">📄 Paper</a> ·
  <a href="results/">📦 Results</a> ·
  <a href="#citation">📝 BibTeX</a>
</p>

---

## Abstract

최근 코드 생성 언어모델은 다양한 프로그래밍 과제에서 우수한 성능을 보이고 있다. 하지만 함수명 형식과 같은 프롬프트에 명시된 간단한 지침마저 안정적으로 따르지 못하는 경우가 있다. 기존 연구는 이러한 모델의 지침 준수 실패 현상을 지침 참조 부족으로 보고, 또 다른 연구는 어텐션 출력에 대한 각 입력 위치의 기여가 Value 벡터의 크기에도 좌우된다고 밝혔다. 본 논문은 함수명의 표기 규약을 사례 삼아 기존 연구들의 구분을 Key와 Value를 분리·치환하는 개입으로 확장함으로써 함수명 표기 신호가 전달되는 경로를 추적한다. 선행 문맥에 지침을 위반하는 함수가 일정 수 이상 포함되면 지침 준수율이 급락하였으며, 코드 특화 모델에서는 이러한 급락이 지침이 모델의 기본 선호와 충돌할 때에만 나타났다. 경로별 개입에서는 Key 치환의 효과가 모든 조건에서 미미했던 반면 선행 코드의 Value 치환이 함수명 표기 신호를 일관되게 바꾸었으며, 그 효과는 모델 중후반부의 단일 층에 국소화되었다. 지침 구간의 어텐션 비중을 높여도 모델의 지침 준수율은 대부분 회복되지 않았으나, 해당 층의 잔차에 방향 벡터를 더한 결과 네 모델 중 세 모델에서 지침 준수율이 회복되었다. 이는 지침 준수 실패를 이해하려면 어텐션 배분만이 아니라 실제로 전달되는 표현의 내용을 함께 고려해야 함을 보인다.

<p align="center">
  <kbd>코드 생성 언어모델</kbd>
  <kbd>지침 준수</kbd>
  <kbd>어텐션 배분</kbd>
  <kbd>Key와 Value 경로</kbd>
  <kbd>활성 개입</kbd>
</p>

## Research Questions

- **RQ1.** 선행 코드에 지침을 위반한 함수명이 포함되면 모델의 지침 준수율이 낮아지는가?
- **RQ2.** 지침 토큰과 선행 코드 토큰에 대한 어텐션 배분은 어떻게 나타나며, 함수명 표기 정보는 Key, Value 중 어느 경로를 통해 전달되는가?
- **RQ3.** 지침 구간의 어텐션 비중을 높이는 개입으로 모델의 지침 준수율을 회복할 수 있는가?

## Findings

- **A1.** 선행 코드의 지침 위반 사례는 모델의 지침 준수율을 감소시켰다.
- **A2.** 코드 특화 모델은 지침 토큰에 더 많은 어텐션을 할당하면서도 지침을 위반하였으며, 표기 신호는 Value 경로를 통해 전달되었다.
- **A3.** 지침 구간의 어텐션 비중을 높이는 개입으로는 모델의 지침 준수율을 높이지 못한 반면, 잔차 조향은 네 모델 중 세 모델에서 지침 준수율을 높였다.
