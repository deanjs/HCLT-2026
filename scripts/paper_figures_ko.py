"""논문 본문용 그림 — 한국어 라벨, 전부 단일 패널.

HCLT 템플릿(A4·2단·10pt) 기준.
  · 단 폭 그림 : 폭 3.3in → LaTeX에서 width=\\linewidth
  · 모델별로 패널을 옆에 이어 붙이지 않는다. 그림 한 장은 판 하나다
  · 제목은 그림에 넣지 않는다 — 캡션은 LaTeX에서 단다
  · 글꼴은 NanumGothic. 없으면 예외를 던진다(글자가 네모로 깨진 그림을 남기지 않기 위함)

만드는 그림
  step1/figures/ko_cliff              문맥의 위반이 준수율을 무너뜨린다        (RQ1)
  step3/figures/ko_key_vs_value       Key와 Value 중 어느 쪽이 표기를 나르나   (RQ2)
  step6/figures/ko_method             값 조향 vs 어텐션 증폭                   (RQ3)
  step6/figures/ko_score_vs_real      세기를 올리면 두 채점이 갈라진다         (RQ3)

쓰는 법:
    python scripts/paper_figures_ko.py [--out <미리보기 폴더>]
"""

from __future__ import annotations

import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt


def _install_korean_font() -> str:
    """본문(LaTeX)이 명조 계열이므로 그림도 세리프로 맞춘다.

    고딕으로 뽑으면 발표 자료처럼 보이고 본문과 따로 논다.
    """
    for path, name in (("/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf", "NanumMyeongjo"),
                       ("/root/.fonts/NanumMyeongjo.ttf", "NanumMyeongjo"),
                       ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "NanumGothic"),
                       ("/root/.fonts/NanumGothic.ttf", "NanumGothic")):
        if Path(path).exists():
            fm.fontManager.addfont(path)
            return name
    have = {f.name for f in fm.fontManager.ttflist}
    for name in ("NanumMyeongjo", "Noto Serif CJK KR", "NanumGothic"):
        if name in have:
            return name
    raise RuntimeError(
        "한글 글꼴이 없다. 글자가 네모로 깨진 그림을 남기지 않으려고 여기서 멈춘다.\n"
        "  apt-get install -y fonts-nanum fonts-nanum-extra")


KO = _install_korean_font()
matplotlib.rcParams.update({
    "font.family": KO,
    "axes.unicode_minus": False,
    "font.size": 8,
    "axes.labelsize": 8.5,
    "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7,
    # 논문 그림 — 얇은 축, 위·오른쪽 테두리 없음, 가로선만 옅게
    "axes.linewidth": 0.6,
    "axes.edgecolor": "black",
    "axes.labelcolor": "black",
    "text.color": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 2.2,
    "ytick.major.size": 2.2,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "grid.color": "#CCCCCC",
    "grid.linewidth": 0.4,
    "grid.alpha": 0.6,
    "axes.axisbelow": True,
    "lines.linewidth": 1.3,
    "legend.frameon": False,
    "legend.handlelength": 1.4,
    "legend.columnspacing": 1.1,
    "legend.handletextpad": 0.5,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
    # 로그 눈금의 지수·음수 기호는 한글 글꼴에 없다. 수식 글꼴을 따로 준다
    "mathtext.fontset": "dejavuserif",
})

# 색은 둘만 쓴다. 모델은 판을 나눠 구분하므로 색으로 가를 필요가 없다.
RED, GRAY = "#B03A3A", "#8C8C8C"
C = {m: RED for m in ("qwen", "deepseek", "stability", "llama")}
ORDER = ["qwen", "deepseek", "stability", "llama"]   # 범용 모델을 맨 뒤로


def _tidy(ax, ygrid=True):
    if ygrid:
        ax.yaxis.grid(True)
    ax.xaxis.grid(False)
    ax.tick_params(labelcolor="black")


MODELS = ["qwen", "deepseek", "llama", "stability"]
SHORT = {"qwen": "Qwen2.5", "deepseek": "DeepSeek",
         "llama": "Llama", "stability": "StableCode"}
C_VAL, C_KEY = "#2e6fbf", "#b0b0b0"
STEP5_PEAK = {"qwen": 27, "deepseek": 17, "llama": 24, "stability": 19}


def load(step: str):
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(Path("results").rglob(f"{step}/*.json"))]


def ci95(xs):
    if not xs:
        return float("nan"), 0.0
    if len(xs) < 2:
        return xs[0], 0.0
    return st.mean(xs), 1.96 * st.stdev(xs) / math.sqrt(len(xs))


# ── 그림 1. 문맥의 위반이 준수율을 무너뜨린다 (step1) ────────────────────
def fig_cliff(out: Path):
    """지침이 모델의 기본 선호와 부딪힐 때에만 무너진다 — 모델당 판 하나.

    판을 모델로 가르면 두 지침 방향이 **한 판 안에서** 갈라지는 것이 보인다. 이 스텝의
    주장이 곧 그 갈라짐이므로 비교가 판 사이를 건너뛰지 않는다. 세 판은 빨강만 무너지고
    회색은 평탄한데, Llama 판만 둘 다 무너진다 — 판 하나가 통째로 달라 보인다.

    판당 선이 둘뿐이라 색은 모델이 아니라 **지침 방향**을 뜻한다(그림 2~4와 같은
    빨강·회색 대비). 그림 2와 판 배치도 같다.
    """
    by = defaultdict(lambda: defaultdict(list))
    for r in load("step1_cliff"):
        c = r["condition"]
        n_viol = c["preceding"]["n_functions"] - c["preceding"]["n_compliant"]
        by[(c["model"]["family"], c["instruction"]["target_notation"])][n_viol].append(
            1.0 if r["metrics"]["extra"]["first_compliant"] else 0.0)

    # 그림 2(fig_attention)와 **완전히 같은 구조**로 그린다: 같은 figsize, 같은 여백,
    # 같은 잘라내기, 범례도 판 안. 하나라도 다르면 상자나 판 크기가 어긋난다.
    # 범례를 판 밖으로 빼면 그만큼 격자가 눌리므로 판 크기를 맞출 수 없다.
    fig, axes = plt.subplots(2, 2, figsize=(3.3, 2.65))
    for ax, m in zip(axes.ravel(), ORDER):
        for tgt, color, mk, lab in (("camel", RED, "o", "camelCase 지침"),
                                    ("snake", GRAY, "s", "snake_case 지침")):
            k = (m, tgt)
            if k not in by:
                continue
            xs = sorted(by[k])
            ax.plot(xs, [st.mean(by[k][x]) for x in xs], color=color, linewidth=1.2,
                    marker=mk, ms=2.6, markevery=2, markerfacecolor=color,
                    markeredgecolor=color, label=lab)
        ax.set_title(SHORT[m], fontsize=7.5, pad=2.5)
        ax.set_ylim(-0.05, 1.07)
        ax.set_yticks([0, 0.5, 1.0])
        ax.set_xticks(range(0, 13, 4))
        ax.set_xlim(-0.4, 12.4)
        ax.tick_params(labelsize=6.2)
        _tidy(ax)
    for ax in axes[1]:
        ax.set_xlabel("위반 이름의 수", fontsize=7.5)
    for ax in axes[:, 0]:
        ax.set_ylabel("지침 준수율", fontsize=7)
    # 범례는 판 안이어야 격자 크기가 그림 2와 같다. 네 판 중 StableCode가 가장 넓게
    # 비어 있다 — 빨강이 위반 3개부터 0에, 회색이 1.0에 붙어 가운데가 통째로 열린다.
    # (Qwen 판은 빨강이 그 자리를 가로질러 내려간다.)
    axes[1][0].legend(fontsize=6.0, loc="center right", handlelength=1.1,
                      borderaxespad=0.5, labelspacing=0.35, framealpha=1.0)
    fig.tight_layout(pad=0.3, h_pad=0.7, w_pad=0.9)
    _save(fig, out, "ko_cliff", box_pt=(247.07, 200.38))   # 그림 2와 같은 상자


# ── 그림 2. Key와 Value 중 어느 쪽이 표기를 나르나 (step3 + step5) ───────
def _step3_net():
    """선행 코드 쪽 순효과 = (camel을 덮었을 때) − (snake를 덮었을 때). 봉우리 층에서."""
    cube = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
    for r in load("step3_code-cause"):
        m = r["condition"]["model"]["family"]
        b = r["condition"]["preceding"]["pool_block"]
        d = r["metrics"]["extra"]["donor"]
        for L, v in r["metrics"]["per_layer"].items():
            for k in ("key", "value"):
                x = v.get(f"{k}__recovery")
                if x is not None:
                    cube[m][d][int(L)][k][b] = x

    def net(m, L, k):
        a, b = cube[m]["unrelated_camel"][L][k], cube[m]["unrelated_snake"][L][k]
        return [a[i] - b[i] for i in sorted(set(a) & set(b))]

    out = {}
    for m in MODELS:
        layers = sorted(cube[m]["unrelated_camel"])
        L = max(layers, key=lambda L: st.mean(net(m, L, "value")))
        out[m] = {"layer": L, "value": ci95(net(m, L, "value")), "key": ci95(net(m, L, "key"))}
    return out


def _step5_net():
    """지침 쪽 순효과 = (반대 표기를 덮었을 때) − (같은 지시어를 덮었을 때). 봉우리 층에서."""
    treat = defaultdict(lambda: defaultdict(list))
    for r in load("step5_instr-cause"):
        m = r["condition"]["model"]["family"]
        if r["metrics"]["extra"].get("undecidable"):
            continue
        v = r["metrics"]["per_layer"].get(str(STEP5_PEAK[m]), {})
        for k in ("value", "key"):
            if v.get(f"{k}__recovery") is not None:
                treat[m][k].append(v[f"{k}__recovery"])
    ctrl = defaultdict(lambda: defaultdict(list))
    for r in load("step5_instr-cause-control"):
        ex = r["metrics"]["extra"]
        if ex.get("mode") != "intervene_sweep" or ex.get("undecidable") \
                or ex.get("donor") != "control_self":
            continue
        m = r["condition"]["model"]["family"]
        v = r["metrics"]["per_layer"].get(str(STEP5_PEAK[m])) or {}
        for k in ("value", "key"):
            if v.get(f"{k}__recovery") is not None:
                ctrl[m][k].append(v[f"{k}__recovery"])
    return {m: {"layer": STEP5_PEAK[m],
                **{k: (st.mean(treat[m][k]) - st.mean(ctrl[m][k]),
                       ci95(treat[m][k])[1] + ci95(ctrl[m][k])[1])
                   for k in ("value", "key")}}
            for m in MODELS if treat[m] and ctrl[m]}


def _step3_curves():
    """선행 코드 쪽 층별 순효과 = (camel을 덮었을 때) − (snake를 덮었을 때)."""
    cube = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))
    for r in load("step3_code-cause"):
        m = r["condition"]["model"]["family"]
        b = r["condition"]["preceding"]["pool_block"]
        d = r["metrics"]["extra"]["donor"]
        for L, v in r["metrics"]["per_layer"].items():
            for k in ("key", "value"):
                x = v.get(f"{k}__recovery")
                if x is not None:
                    cube[m][d][int(L)][k][b] = x
    out = {}
    for m in MODELS:
        layers = sorted(cube[m]["unrelated_camel"])
        cur = {"layers": layers}
        for k in ("value", "key"):
            ys, cs = [], []
            for L in layers:
                a_, b_ = cube[m]["unrelated_camel"][L][k], cube[m]["unrelated_snake"][L][k]
                d = [a_[i] - b_[i] for i in sorted(set(a_) & set(b_))]
                mu, c = ci95(d); ys.append(mu); cs.append(c)
            cur[k], cur[k + "_ci"] = ys, cs
        out[m] = cur
    return out


def _step5_curves():
    """지침 쪽 층별 순효과 = (반대 표기를 덮었을 때) − (같은 지시어를 덮었을 때)."""
    def gather(steps, donor=None):
        acc = defaultdict(lambda: defaultdict(list))
        rows = [r for st_ in steps for r in load(st_)]
        for r in rows:
            ex = r["metrics"]["extra"]
            if ex.get("undecidable") or (donor and ex.get("donor") != donor):
                continue
            m = r["condition"]["model"]["family"]
            for L, v in r["metrics"]["per_layer"].items():
                for k in ("value", "key"):
                    x = v.get(f"{k}__recovery")
                    if x is not None:
                        acc[m][(int(L), k)].append(x)
        return acc

    treat = gather(["step5_instr-cause"])
    ctrl = gather([f"step5_control_sweep_{m}" for m in MODELS], "control_self")
    out = {}
    for m in MODELS:
        layers = sorted({L for L, _ in treat[m]} & {L for L, _ in ctrl[m]})
        if not layers:
            continue
        cur = {"layers": layers}
        for k in ("value", "key"):
            cur[k] = [st.mean(treat[m][(L, k)]) - st.mean(ctrl[m][(L, k)]) for L in layers]
            # 두 실행분의 구간을 보수적으로 더한다
            cur[k + "_ci"] = [ci95(treat[m][(L, k)])[1] + ci95(ctrl[m][(L, k)])[1]
                              for L in layers]
        out[m] = cur
    return out


PEAK_MIN = 0.05      # 이 아래면 봉우리라 부르지 않는다


def _peak(cur):
    """Value 순효과가 가장 큰 층. 효과 자체가 없으면 None.

    곡선이 통째로 0 근처인 모델(지침이 행동을 좌우하지 않는 경우)에서 argmax를
    그대로 쓰면 잡음 중 최댓값이 봉우리로 둔갑한다. 그런 경우는 층을 특정하지 않는다.
    """
    i = max(range(len(cur["layers"])), key=lambda i: cur["value"][i])
    return i if cur["value"][i] >= PEAK_MIN else None


def _attention_curves():
    """지침 지시어와 앞선 코드 이름이 층마다 받는 토큰당 어텐션."""
    obs = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in load("step4_instr-observe"):
        m = r["condition"]["model"]["family"]
        cnt = r["metrics"]["extra"].get("span_token_counts", {})
        for L, v in r["metrics"]["per_layer"].items():
            x, n = v.get("instr_rule_word__attention_weight"), cnt.get("instr_rule_word")
            if x is not None and n:
                obs[m][int(L)]["instr"].append(x / n)
            # 코드 쪽은 camel과 snake 12개를 전부 합친다. 한쪽만 쓰면 비가 부풀려진다.
            xs = [(v.get(f"{sp}__attention_weight"), cnt.get(sp))
                  for sp in ("code_camel", "code_snake")]
            if all(a_ is not None and b_ for a_, b_ in xs):
                obs[m][int(L)]["code"].append(sum(a_ for a_, _ in xs) / sum(b_ for _, b_ in xs))
    return obs


def fig_attention(out: Path):
    """관측 — 지침과 앞선 코드를 층마다 얼마나 보는가. 모델당 판 하나."""
    obs = _attention_curves()
    c5 = _step5_curves()

    fig, axes = plt.subplots(2, 2, figsize=(3.3, 2.65))
    for ax, m in zip(axes.ravel(), ORDER):
        L = sorted(obs[m])
        ins = [st.mean(obs[m][i]["instr"]) for i in L]
        cod = [st.mean(obs[m][i]["code"]) for i in L]
        ax.plot(L, cod, color=GRAY, linewidth=1.0, label="앞선 코드")
        ax.plot(L, ins, color=RED, linewidth=1.2, label="지침")
        k = _peak(c5[m]) if m in c5 else None
        if k is not None:
            ax.axvline(c5[m]["layers"][k], color="black", linewidth=0.6,
                       linestyle="--", alpha=0.5, zorder=0)
        ax.set_title(SHORT[m], fontsize=7.5, pad=2.5)
        ax.tick_params(labelsize=6.2)
        ax.margins(y=0.20)
        _tidy(ax)
    h, l = axes[0][0].get_legend_handles_labels()
    axes[0][0].legend(h[::-1], l[::-1], fontsize=6.2, loc="upper left",
                      handlelength=1.2, borderaxespad=0.25)
    for ax in axes[1]:
        ax.set_xlabel("층", fontsize=7.5)
    for ax in axes[:, 0]:
        ax.set_ylabel("토큰당 어텐션", fontsize=7)
    fig.tight_layout(pad=0.3, h_pad=0.7, w_pad=0.9)
    _save(fig, out, "ko_attention")


def fig_intervene(out: Path):
    """개입 — 봉우리 층에서 Value와 Key를 각각 치환했을 때의 순효과."""
    code, instr = _step3_curves(), _step5_curves()

    fig, axes = plt.subplots(1, 2, figsize=(3.3, 2.0))
    for ax, (src, title) in zip(axes, ((code, "(가) 앞선 코드를 바꿈"),
                                       (instr, "(나) 지침을 바꿈"))):
        x = list(range(len(ORDER)))
        for off, key, face, lab in ((-0.5, "value", RED, "Value"),
                                    (0.5, "key", GRAY, "Key")):
            ys, es, cols = [], [], []
            for m in ORDER:
                if m not in src:
                    ys.append(float("nan")); es.append(0.0); cols.append(GRAY); continue
                k = max(range(len(src[m]["layers"])), key=lambda i: src[m]["value"][i])
                ys.append(src[m][key][k]); es.append(src[m][key + "_ci"][k])
                cols.append(face)
            ax.bar([i + off * 0.38 for i in x], ys, 0.38, yerr=es, capsize=1.4,
                   color=cols, linewidth=0, label=lab,
                   error_kw={"linewidth": 0.6, "ecolor": "black"})
        ax.axhline(0, color="black", linewidth=0.6)
        ax.set_xticks(x)
        TIGHT = {"qwen": "Qwen", "deepseek": "DeepSeek",
                 "stability": "Stable", "llama": "Llama"}
        ax.set_xticklabels([f"{TIGHT[m]}\nL{src[m]['layers'][max(range(len(src[m]['layers'])), key=lambda i: src[m]['value'][i])]}"
                            if m in src else TIGHT[m] for m in ORDER], fontsize=6.0)
        ax.set_title(title, fontsize=7.5, pad=3)
        ax.tick_params(axis="y", labelsize=6.5)
        ax.margins(y=0.16)
        _tidy(ax)
    axes[0].set_ylabel("순효과", fontsize=7.5)
    axes[0].legend(fontsize=6.4, loc="upper left", handlelength=1.1, borderaxespad=0.25)
    fig.tight_layout(pad=0.3, w_pad=1.0)
    _save(fig, out, "ko_intervene")


# ── 그림 3·4. step6 ──────────────────────────────────────────────────────
TASK_WORDS = ("remove", "duplicat", "dedup", "uniq", "distinct")


def _real(ex) -> float:
    n = ex["name"]
    return 1.0 if (ex["compliant"] and n and any(w in n.lower() for w in TASK_WORDS)) else 0.0


def fig_method(out: Path):
    """처방 — 조향을 건 채로 실제 생성한 이름의 준수율.

    무개입은 네 모델 모두 0.000이라 막대를 세우지 않고 캡션에서 밝힌다.
    """
    g = defaultdict(lambda: defaultdict(list))
    for r in load("step6_steer-generate"):
        ex = r["metrics"]["extra"]
        m = r["condition"]["model"]["family"]
        if ex["method"] == "value_add":
            key = ("값 조향", float(ex["strength"]))
        elif ex["method"] == "attn_amplify":
            key = ("어텐션 증폭", (float(ex["psi_target"]), ex.get("span") or ""))
        else:
            key = ("무개입", 0)
        g[m][key].append(_real(ex))

    def best(m, name):
        c = [v for k, v in g[m].items() if k[0] == name]
        return max(c, key=st.mean) if c else []

    TIGHT = {"qwen": "Qwen", "deepseek": "DeepSeek",
             "stability": "Stable", "llama": "Llama"}
    fig, ax = plt.subplots(figsize=(3.3, 1.95))
    x = list(range(len(ORDER)))
    for off, (name, col) in zip((-0.5, 0.5), (("값 조향", RED), ("어텐션 증폭", GRAY))):
        ys, es = zip(*[ci95(best(m, name)) for m in ORDER])
        ax.bar([i + off * 0.38 for i in x], ys, 0.38, yerr=es, capsize=1.4,
               color=col, linewidth=0, label=name,
               error_kw={"linewidth": 0.6, "ecolor": "black"})
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([TIGHT[m] for m in ORDER], fontsize=7)
    ax.set_ylabel("실제 준수율", fontsize=7.5)
    ax.set_ylim(0, 1.10); ax.set_yticks([0, 0.5, 1.0])
    ax.set_xlim(-0.6, len(ORDER) - 0.4)
    ax.legend(ncol=2, fontsize=6.6, loc="lower center", bbox_to_anchor=(0.5, 1.0),
              borderaxespad=0.0, handlelength=1.1)
    _tidy(ax)
    fig.tight_layout(pad=0.25)
    _save(fig, out, "ko_method")


def fig_score_vs_real(out: Path):
    """같은 개입을 두 자로 잰다 — 세기를 올릴수록 두 자가 갈라진다.

    왼쪽은 세기 1~2에서 봉우리를 만들고 8에서 무너지는데, 오른쪽은 그동안 계속 오른다.
    """
    ste = load("step6_steer")
    peak = {}
    for r in ste:
        ex = r["metrics"]["extra"]
        if ex["method"] == "value_add":
            m = r["condition"]["model"]["family"]
            peak[m] = max(peak.get(m, -1), ex["layer"])
    rc = defaultdict(lambda: defaultdict(list))
    for r in ste:
        ex = r["metrics"]["extra"]
        m = r["condition"]["model"]["family"]
        if ex["method"] == "value_add" and ex["layer"] == peak[m]:
            rc[m][float(ex["strength"])].append(ex["recovery"])
    for m in MODELS:
        rc[m][0.0] = [0.0]                    # 개입하지 않으면 되돌릴 것도 없다
    gn = defaultdict(lambda: defaultdict(list))
    for r in load("step6_steer-generate"):
        ex = r["metrics"]["extra"]
        if ex["method"] == "value_add":
            gn[r["condition"]["model"]["family"]][float(ex["strength"])].append(_real(ex))

    S = [0.0, 1.0, 2.0, 4.0, 8.0]
    MARK = {"qwen": "o", "deepseek": "s", "stability": "D", "llama": "^"}
    STYLE = {"qwen": (RED, "-"), "deepseek": (GRAY, "-"),
             "stability": (RED, "--"), "llama": (GRAY, "--")}

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.35, 1.95))
    x = list(range(len(S)))
    for m in ORDER:
        col, ls = STYLE[m]
        kw = dict(color=col, linestyle=ls, marker=MARK[m], ms=2.8, linewidth=1.1,
                  markeredgewidth=0)
        a1.plot(x, [st.mean(gn[m][v]) if gn[m].get(v) else 0.0 for v in S],
                label=SHORT[m], **kw)
        a2.plot(x, [st.mean(rc[m][v]) if rc[m].get(v) else 0.0 for v in S], **kw)
    a1.set_ylabel("실제 준수율", fontsize=7.5)
    a1.set_ylim(-0.04, 1.06); a1.set_yticks([0, 0.5, 1.0])
    a1.set_title("(가) 생성한 이름", fontsize=7.5, pad=3)
    a2.set_ylabel("되돌림률", fontsize=7.5)
    a2.set_ylim(-0.15, 4.7); a2.set_yticks([0, 2, 4])
    a2.set_title("(나) 선호 점수", fontsize=7.5, pad=3)
    for ax in (a1, a2):
        ax.set_xticks(x)
        ax.set_xticklabels([f"{v:g}" for v in S], fontsize=6.8)
        ax.tick_params(axis="y", labelsize=6.8)
        _tidy(ax)
    fig.supxlabel("값을 미는 세기  (0 = 개입하지 않음)", fontsize=7.5, y=0.02)
    fig.legend(ncol=4, fontsize=6.6, handlelength=1.2, columnspacing=0.9,
               loc="lower center", bbox_to_anchor=(0.5, 0.985))
    fig.tight_layout(pad=0.25, rect=(0, 0.04, 1, 1))
    _save(fig, out, "ko_score_vs_real")


def _save(fig, out: Path, name: str, tight: bool = True,
          box_pt: tuple[float, float] | None = None) -> None:
    """tight=False면 여백을 잘라내지 않고 figsize를 **그대로** 상자 크기로 쓴다.

    bbox_inches="tight"는 내용에 맞춰 여백을 깎으므로, 축 라벨 길이가 다른 두 그림은
    같은 figsize를 줘도 저장 크기가 달라진다. 논문에서 나란히 놓일 그림끼리 높이를
    정확히 맞춰야 할 때는 잘라내기를 끄고 figsize로 상자를 못 박는다.
    """
    out.mkdir(parents=True, exist_ok=True)
    if box_pt is not None:
        # 잘라내기 위치는 눈금 글자 폭에 좌우되어 그림마다 0.2pt쯤 어긋난다. 나란히 놓을
        # 그림끼리는 그 차이도 보이므로, 잘라낸 상자를 목표 크기(pt)로 늘려 못 박는다.
        from matplotlib.transforms import Bbox
        tb = fig.get_tightbbox(fig.canvas.get_renderer())
        cx, cy = (tb.x0 + tb.x1) / 2, (tb.y0 + tb.y1) / 2
        w, h = box_pt[0] / 72 / 2, box_pt[1] / 72 / 2
        bb = Bbox([[cx - w, cy - h], [cx + w, cy + h]])
    else:
        bb = "tight" if tight else None
    fig.savefig(out / f"{name}.pdf", bbox_inches=bb)
    fig.savefig(out / f"{name}.png", bbox_inches=bb)
    plt.close(fig)
    print(f"  {out}/{name}.pdf")


def main() -> None:
    root = None
    if "--out" in sys.argv:
        root = Path(sys.argv[sys.argv.index("--out") + 1])
    jobs = [(fig_cliff, "docs/step1/figures"),
            (fig_attention, "docs/step4/figures"),
            (fig_intervene, "docs/step3/figures"),
            (fig_method, "docs/step6/figures"),
            (fig_score_vs_real, "docs/step6/figures")]
    for fn, d in jobs:
        fn(root if root else Path(d))


if __name__ == "__main__":
    main()
