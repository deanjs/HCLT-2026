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
    for p in ("/root/.fonts/NanumGothic.ttf",
              "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
        if Path(p).exists():
            fm.fontManager.addfont(p)
            return "NanumGothic"
    have = {f.name for f in fm.fontManager.ttflist}
    for name in ("NanumGothic", "Noto Sans CJK KR", "Malgun Gothic", "AppleGothic"):
        if name in have:
            return name
    raise RuntimeError(
        "한글 글꼴이 없다. 글자가 네모로 깨진 그림을 남기지 않으려고 여기서 멈춘다.\n"
        "  apt-get install -y fonts-nanum  또는 NanumGothic.ttf를 ~/.fonts에 둔다.")


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
    "axes.linewidth": 0.7,
    "axes.edgecolor": "#444444",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelcolor": "#222222",
    "text.color": "#222222",
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "grid.color": "#DDDDDD",
    "grid.linewidth": 0.5,
    "axes.axisbelow": True,
    "lines.linewidth": 1.3,
    "legend.frameon": False,
    "legend.handlelength": 1.4,
    "legend.columnspacing": 1.1,
    "legend.handletextpad": 0.5,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
})

# 채도를 낮춘 색 — 흑백 인쇄에서도 명도가 갈린다
C = {"qwen": "#3B6EA5", "deepseek": "#D08C3C",
     "stability": "#B04A4A", "llama": "#4E8A5B"}
ORDER = ["qwen", "deepseek", "stability", "llama"]   # 범용 모델을 맨 뒤로


def _tidy(ax, ygrid=True):
    if ygrid:
        ax.yaxis.grid(True)
    ax.xaxis.grid(False)


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
    """지침이 모델의 기본 선호와 부딪힐 때에만 무너진다 — 두 방향을 함께 그려야 보인다."""
    by = defaultdict(lambda: defaultdict(list))
    for r in load("step1_cliff"):
        c = r["condition"]
        n_viol = c["preceding"]["n_functions"] - c["preceding"]["n_compliant"]
        by[(c["model"]["family"], c["instruction"]["target_notation"])][n_viol].append(
            1.0 if r["metrics"]["extra"]["first_compliant"] else 0.0)

    fig, ax = plt.subplots(figsize=(3.3, 2.35))
    series = [("qwen", "camel", C["qwen"], "-", "o", 1.0),
              ("stability", "camel", C["stability"], "-", "s", 1.0),
              ("qwen", "snake", C["qwen"], "--", "o", 0.0),
              ("stability", "snake", C["stability"], "--", "s", 0.0)]
    for m, tgt, color, ls, mk, fill in series:
        k = (m, tgt)
        if k not in by:
            continue
        xs = sorted(by[k])
        ax.plot(xs, [st.mean(by[k][x]) for x in xs], color=color, linestyle=ls,
                linewidth=1.3, marker=mk, ms=3.2, markevery=2,
                markerfacecolor=color if fill else "white",
                markeredgecolor=color, markeredgewidth=1.0,
                label=f"{SHORT[m]} · {'camelCase' if tgt == 'camel' else 'snake_case'}")
    ax.set_xlabel("앞선 코드에 놓인 위반 이름의 수")
    ax.set_ylabel("지침 준수율")
    ax.set_ylim(-0.04, 1.06)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticks(range(0, 13, 3))
    ax.set_xlim(-0.4, 12.4)
    ax.legend(ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0),
              borderaxespad=0.0)
    _tidy(ax)
    fig.tight_layout(pad=0.25)
    _save(fig, out, "ko_cliff")


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


def _peak(cur):
    """Value 순효과가 가장 큰 층과 그 층에서의 값·신뢰구간."""
    i = max(range(len(cur["layers"])), key=lambda i: cur["value"][i])
    return (cur["layers"][i],
            {"value": (cur["value"][i], cur["value_ci"][i]),
             "key": (cur["key"][i], cur["key_ci"][i])})


def fig_key_vs_value(out: Path):
    """모델별 봉우리 층에서 Value와 Key를 나란히 세운다.

    색 = 무엇을 바꿨나(앞선 코드 / 지침), 채움 = 어느 경로를 치환했나(Value / Key).
    """
    code, instr = _step3_curves(), _step5_curves()
    CODE_C, INSTR_C = "#3B6EA5", "#B04A4A"

    fig, ax = plt.subplots(figsize=(3.3, 2.35))
    x = [i * 1.15 for i in range(len(ORDER))]
    w = 0.19
    bars = [(code, "value", -1.5, CODE_C, CODE_C, "앞선 코드 · Value"),
            (code, "key",   -0.5, "white", CODE_C, "앞선 코드 · Key"),
            (instr, "value", 0.5, INSTR_C, INSTR_C, "지침 · Value"),
            (instr, "key",   1.5, "white", INSTR_C, "지침 · Key")]
    layers = {}
    for src, k, off, face, edge, lab in bars:
        ys, es = [], []
        for m in ORDER:
            if m not in src:
                ys.append(float("nan")); es.append(0.0); continue
            L, pk = _peak(src[m])
            layers.setdefault(m, {})[id(src)] = L
            ys.append(pk[k][0]); es.append(pk[k][1])
        ax.bar([i + off * w for i in x], ys, w, yerr=es, capsize=1.4,
               color=face, edgecolor=edge, linewidth=0.9, label=lab,
               error_kw={"linewidth": 0.6, "ecolor": "#333333"})
    ax.axhline(0, color="#444444", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{SHORT[m]}\nL{layers[m][id(code)]} / L{layers[m][id(instr)]}"
                        for m in ORDER], fontsize=6.5)
    ax.set_xlim(-0.55, x[-1] + 0.55)
    ax.set_ylabel("표기를 되돌린 정도 (순효과)")
    ax.set_ylim(-0.05, 0.95)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.legend(ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0),
              borderaxespad=0.0)
    _tidy(ax)
    fig.tight_layout(pad=0.25)
    _save(fig, out, "ko_key_vs_value")


# ── 그림 3·4. step6 ──────────────────────────────────────────────────────
TASK_WORDS = ("remove", "duplicat", "dedup", "uniq", "distinct")


def _real(ex) -> float:
    n = ex["name"]
    return 1.0 if (ex["compliant"] and n and any(w in n.lower() for w in TASK_WORDS)) else 0.0


def fig_method(out: Path):
    """세 처방을 실제 생성한 이름으로 채점한다."""
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

    fig, ax = plt.subplots(figsize=(3.3, 2.4))
    x = list(range(len(MODELS)))
    for off, (name, color) in zip((-1, 0, 1),
                                  (("무개입", "0.78"), ("값 조향", C_VAL),
                                   ("어텐션 증폭", "#7a7a7a"))):
        ys, es = [], []
        for m in MODELS:
            a, c = ci95(best(m, name))
            ys.append(a); es.append(c)
        ax.bar([i + off * 0.26 for i in x], ys, 0.26, yerr=es, capsize=2,
               color=color, label=name, error_kw={"linewidth": 0.7})
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[m] for m in MODELS])
    ax.set_ylabel("실제 생성한 이름의 준수율")
    ax.set_ylim(0, 1.14)
    ax.legend(frameon=False, ncol=3, handlelength=1.3, columnspacing=1.0,
              loc="lower center", bbox_to_anchor=(0.5, 1.01), borderaxespad=0.0)
    ax.grid(axis="y", alpha=0.22, linewidth=0.4)
    fig.tight_layout(pad=0.3)
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

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.35, 1.95))
    x = list(range(len(S)))
    for m in ORDER:
        kw = dict(color=C[m], marker=MARK[m], ms=2.8, linewidth=1.1,
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


def _save(fig, out: Path, name: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(out / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  {out}/{name}.pdf")


def main() -> None:
    root = None
    if "--out" in sys.argv:
        root = Path(sys.argv[sys.argv.index("--out") + 1])
    jobs = [(fig_cliff, "docs/step1/figures"),
            (fig_key_vs_value, "docs/step3/figures"),
            (fig_method, "docs/step6/figures"),
            (fig_score_vs_real, "docs/step6/figures")]
    for fn, d in jobs:
        fn(root if root else Path(d))


if __name__ == "__main__":
    main()
