"""Rang palitrasi va Plotly yordamchilari (dataviz qoidalari: bitta seriya = bitta rang, ingichka ustunlar, ochiq to'r)."""
from __future__ import annotations

from typing import Iterable, List, Optional

import pandas as pd
import plotly.graph_objects as go

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
ORDINAL_BLUE = ["#86b6ef", "#5598e7", "#2a78d6", "#184f95"]  # 2 -> 5 baho
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}
GRID = "#e1e0d9"
MUTED = "#898781"
INK = "#52514e"

LAYOUT = dict(
    template="simple_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=MUTED),
    margin=dict(l=10, r=10, t=40, b=10),
    hoverlabel=dict(bgcolor="white", font=dict(color="#0b0b0b")),
    bargap=0.35,
)


def _base(fig: go.Figure, title: str, height: int = 320) -> go.Figure:
    fig.update_layout(**LAYOUT, title=dict(text=title, font=dict(size=15, color=INK), x=0), height=height, showlegend=False)
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED), title=None)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, gridwidth=1, linecolor=GRID, zeroline=False, tickfont=dict(color=MUTED), title=None)
    return fig


def bar(categories: Iterable, values: Iterable, title: str, *, colors: Optional[List[str]] = None, horizontal: bool = False,
        value_suffix: str = "", height: int = 320, hover_label: str = "Qiymat") -> go.Figure:
    cats, vals = list(categories), list(values)
    color = colors if colors else SERIES[0]
    if horizontal:
        trace = go.Bar(x=vals, y=cats, orientation="h", marker=dict(color=color, line=dict(width=0)), width=0.55,
                       hovertemplate=f"%{{y}}<br>{hover_label}: %{{x}}{value_suffix}<extra></extra>")
    else:
        trace = go.Bar(x=cats, y=vals, marker=dict(color=color, line=dict(width=0)), width=0.55,
                       hovertemplate=f"%{{x}}<br>{hover_label}: %{{y}}{value_suffix}<extra></extra>")
    fig = go.Figure(trace)
    fig = _base(fig, title, height)
    if horizontal:
        fig.update_yaxes(showgrid=False, autorange="reversed")
        fig.update_xaxes(showgrid=True, gridcolor=GRID)
    return fig


def score_bar(rubric: List[dict], title: str = "Mezonlar bo'yicha ball") -> go.Figure:
    """Har bir mezon: olingan ball (ko'k) va maksimal (och kulrang fon)."""
    names = [r["name"] for r in rubric]
    scores = [float(r.get("score") or 0) for r in rubric]
    maxes = [float(r.get("max_score") or 0) for r in rubric]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=maxes, y=names, orientation="h", marker=dict(color="#eeede8", line=dict(width=0)), width=0.55, hoverinfo="skip"))
    fig.add_trace(go.Bar(x=scores, y=names, orientation="h", marker=dict(color=SERIES[0], line=dict(width=0)), width=0.55,
                         text=[f"{s:g}/{m:g}" for s, m in zip(scores, maxes)], textposition="outside", textfont=dict(color=INK),
                         hovertemplate="%{y}<br>Ball: %{x}<extra></extra>"))
    fig.update_layout(barmode="overlay")
    fig = _base(fig, title, height=max(220, 60 * len(names) + 60))
    fig.update_yaxes(showgrid=False, autorange="reversed")
    fig.update_xaxes(showgrid=True, gridcolor=GRID, range=[0, max(maxes + [1]) * 1.2])
    return fig


def status_for_ratio(value: Optional[float], warn: float, bad: float) -> tuple[str, str]:
    """(icon, label) — rang hech qachon yolg'iz ma'no tashimaydi."""
    if value is None:
        return "▫️", "ma'lumot yo'q"
    if value >= bad:
        return "🔴", "yuqori"
    if value >= warn:
        return "🟠", "o'rtacha"
    return "🟢", "past"


def grade_badge(grade_5: Optional[int]) -> str:
    return {5: "🟢 5 (a'lo)", 4: "🔵 4 (yaxshi)", 3: "🟠 3 (qoniqarli)", 2: "🔴 2 (qoniqarsiz)"}.get(grade_5 or 0, "—")


def df(rows: List[dict], columns: Optional[List[str]] = None, rename: Optional[dict] = None) -> pd.DataFrame:
    d = pd.DataFrame(rows)
    if columns:
        d = d[[c for c in columns if c in d.columns]]
    if rename:
        d = d.rename(columns=rename)
    return d
