"""Tahliliy hisob-kitoblar (sof funksiyalar, DB'ga bog'liq emas).

Kirish: `rows` — har bir baho uchun lug'at:
  {student_id, student_name, group_name, course, topic, total_score, max_score,
   ai_total_score, rubric: [{name, max_score, score}], status, confirmed,
   plagiarism_score, ai_likelihood, similarity_score, created_at}
"""
from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any, Dict, Iterable, List, Optional

from . import config

GRADE_LABELS = {5: "a'lo", 4: "yaxshi", 3: "qoniqarli", 2: "qoniqarsiz"}


def percent(score: Optional[float], max_score: Optional[float]) -> float:
    if score is None:
        return 0.0
    max_score = max_score or 100.0
    if max_score <= 0:
        return 0.0
    return round(100.0 * float(score) / float(max_score), 2)


def score_to_grade5(score: Optional[float], max_score: float = 100.0, thresholds: Optional[Dict[int, float]] = None) -> int:
    """100 ballik natijani 5 ballik bahoga o'tkazadi."""
    th = thresholds or config.settings.grade_thresholds
    p = percent(score, max_score)
    if p >= th[5]:
        return 5
    if p >= th[4]:
        return 4
    if p >= th[3]:
        return 3
    return 2


def _avg(values: Iterable[float]) -> float:
    vals = [float(v) for v in values]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def _empty() -> Dict[str, Any]:
    return {
        "total_grades": 0,
        "total_students": 0,
        "confirmed_count": 0,
        "pending_count": 0,
        "average_score": 0.0,
        "median_score": 0.0,
        "min_score": 0.0,
        "max_score": 0.0,
        "pass_rate": 0.0,
        "quality_rate": 0.0,
        "distribution": {"5": 0, "4": 0, "3": 0, "2": 0},
        "histogram": [],
        "weak_topics": [],
        "criteria_stats": [],
        "group_stats": [],
        "student_stats": [],
        "at_risk_students": [],
        "top_students": [],
        "integrity": {"plagiarism_flags": 0, "ai_flags": 0, "similarity_flags": 0},
        "ai_teacher_agreement": {"edited_count": 0, "mean_abs_diff": 0.0, "within_5_points_pct": 0.0},
        "time_saved_hours": 0.0,
        "time_saved_minutes": 0.0,
        "thresholds": {"pass": config.settings.pass_threshold, "quality": config.settings.quality_threshold},
    }


def compute_analytics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    s = config.settings
    if not rows:
        return _empty()

    th = s.grade_thresholds
    pcts = [percent(r.get("total_score"), r.get("max_score") or 100.0) for r in rows]
    grades5 = [score_to_grade5(r.get("total_score"), r.get("max_score") or 100.0, th) for r in rows]
    n = len(rows)

    distribution = {"5": 0, "4": 0, "3": 0, "2": 0}
    for g in grades5:
        distribution[str(g)] += 1

    pass_rate = round(100.0 * sum(1 for p in pcts if p >= th[3]) / n, 2)
    quality_rate = round(100.0 * sum(1 for p in pcts if p >= th[4]) / n, 2)

    histogram = [
        {"bin": f"0–{int(th[3]) - 1}", "label": "2 (qoniqarsiz)", "count": distribution["2"]},
        {"bin": f"{int(th[3])}–{int(th[4]) - 1}", "label": "3 (qoniqarli)", "count": distribution["3"]},
        {"bin": f"{int(th[4])}–{int(th[5]) - 1}", "label": "4 (yaxshi)", "count": distribution["4"]},
        {"bin": f"{int(th[5])}–100", "label": "5 (a'lo)", "count": distribution["5"]},
    ]

    # --- Mezonlar bo'yicha ---
    crit = defaultdict(lambda: {"sum_pct": 0.0, "count": 0, "below_pass": 0})
    for r in rows:
        for item in r.get("rubric") or []:
            if not isinstance(item, dict) or item.get("score") is None or not item.get("name"):
                continue
            p = percent(item.get("score"), item.get("max_score") or 1)
            b = crit[item["name"]]
            b["sum_pct"] += p
            b["count"] += 1
            if p < th[3]:
                b["below_pass"] += 1
    criteria_stats = []
    for name, b in crit.items():
        avg = round(b["sum_pct"] / b["count"], 2)
        criteria_stats.append({
            "criterion": name,
            "average_percent": avg,
            "difficulty": round(100 - avg, 2),
            "count": b["count"],
            "below_pass_pct": round(100.0 * b["below_pass"] / b["count"], 2),
        })
    criteria_stats.sort(key=lambda x: x["difficulty"], reverse=True)

    # --- Mavzular bo'yicha ---
    topics = defaultdict(list)
    for r, p in zip(rows, pcts):
        topics[(r.get("topic") or r.get("course") or "Umumiy")].append(p)
    weak_topics = []
    for topic, vals in topics.items():
        avg = _avg(vals)
        weak_topics.append({
            "topic": topic,
            "average_score": avg,
            "pass_rate": round(100.0 * sum(1 for v in vals if v >= th[3]) / len(vals), 2),
            "count": len(vals),
            "difficulty": round(100 - avg, 2),
        })
    weak_topics.sort(key=lambda x: (x["difficulty"], -x["count"]), reverse=True)

    # --- Guruhlar bo'yicha ---
    groups = defaultdict(list)
    for r, p in zip(rows, pcts):
        groups[r.get("group_name") or "—"].append(p)
    group_stats = []
    for g, vals in groups.items():
        group_stats.append({
            "group": g,
            "count": len(vals),
            "average_score": _avg(vals),
            "pass_rate": round(100.0 * sum(1 for v in vals if v >= th[3]) / len(vals), 2),
            "quality_rate": round(100.0 * sum(1 for v in vals if v >= th[4]) / len(vals), 2),
        })
    group_stats.sort(key=lambda x: x["average_score"], reverse=True)

    # --- Talabalar bo'yicha ---
    per_student: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r, p in zip(rows, pcts):
        per_student[r.get("student_id") or "unknown"].append({"pct": p, "created_at": r.get("created_at") or "", "name": r.get("student_name"), "group": r.get("group_name")})
    student_stats = []
    for sid, items in per_student.items():
        items.sort(key=lambda x: x["created_at"])
        vals = [i["pct"] for i in items]
        avg = _avg(vals)
        trend = round(vals[-1] - vals[0], 2) if len(vals) > 1 else 0.0
        student_stats.append({
            "student_id": sid,
            "student_name": next((i["name"] for i in items if i["name"]), None),
            "group": next((i["group"] for i in items if i["group"]), None),
            "count": len(vals),
            "average_score": avg,
            "last_score": vals[-1],
            "trend": trend,
            "grade_5": score_to_grade5(avg, 100.0, th),
            "at_risk": avg < th[3] or vals[-1] < th[3],
        })
    student_stats.sort(key=lambda x: x["average_score"])
    at_risk = [x for x in student_stats if x["at_risk"]]
    top = sorted(student_stats, key=lambda x: x["average_score"], reverse=True)[:5]

    # --- Halollik ko'rsatkichlari ---
    integrity = {
        "plagiarism_flags": sum(1 for r in rows if (r.get("plagiarism_score") or 0) >= s.plagiarism_flag_threshold),
        "ai_flags": sum(1 for r in rows if (r.get("ai_likelihood") or 0) >= s.ai_flag_threshold),
        "similarity_flags": sum(1 for r in rows if (r.get("similarity_score") or 0) >= s.similarity_flag_threshold),
    }

    # --- AI va o'qituvchi mosligi (kalibratsiya) ---
    diffs = []
    for r in rows:
        if r.get("ai_total_score") is None or r.get("status") not in {"edited", "confirmed"}:
            continue
        diffs.append(abs(percent(r["total_score"], r.get("max_score") or 100) - percent(r["ai_total_score"], r.get("max_score") or 100)))
    agreement = {
        "edited_count": sum(1 for r in rows if r.get("status") == "edited"),
        "reviewed_count": len(diffs),
        "mean_abs_diff": round(sum(diffs) / len(diffs), 2) if diffs else 0.0,
        "within_5_points_pct": round(100.0 * sum(1 for d in diffs if d <= 5) / len(diffs), 2) if diffs else 0.0,
    }

    confirmed_count = sum(1 for r in rows if r.get("confirmed") or r.get("status") in {"confirmed", "edited"})
    minutes_saved = n * s.minutes_per_manual_check

    return {
        "total_grades": n,
        "total_students": len(per_student),
        "confirmed_count": confirmed_count,
        "pending_count": n - confirmed_count,
        "average_score": _avg(pcts),
        "median_score": round(float(median(pcts)), 2),
        "min_score": round(min(pcts), 2),
        "max_score": round(max(pcts), 2),
        "pass_rate": pass_rate,
        "quality_rate": quality_rate,
        "distribution": distribution,
        "histogram": histogram,
        "weak_topics": weak_topics[:10],
        "criteria_stats": criteria_stats,
        "group_stats": group_stats,
        "student_stats": student_stats,
        "at_risk_students": at_risk[:20],
        "top_students": top,
        "integrity": integrity,
        "ai_teacher_agreement": agreement,
        "time_saved_hours": round(minutes_saved / 60.0, 1),
        "time_saved_minutes": round(minutes_saved, 0),
        "thresholds": {"pass": th[3], "quality": th[4], "excellent": th[5]},
    }


def build_narrative(a: Dict[str, Any], course: Optional[str] = None, group: Optional[str] = None) -> str:
    """Kafedra mudiri / dekanat uchun o'zbekcha tahliliy xulosa (shablon asosida)."""
    scope = f"«{course}» fani" if course else "barcha fanlar"
    scope += f", {group} guruhi" if group else ", barcha guruhlar"
    if not a or not a.get("total_grades"):
        return f"{scope[0].upper() + scope[1:]} bo'yicha hali baholangan ishlar yo'q. Tahlil uchun avval talabalar ishlarini tekshiring."

    th = a.get("thresholds", {})
    paragraphs: List[str] = []
    paragraphs.append(
        f"{scope[0].upper() + scope[1:]} bo'yicha jami {a['total_grades']} ta ish ({a['total_students']} nafar talaba) tahlil qilindi. "
        f"O'rtacha ball — {a['average_score']}%, mediana — {a['median_score']}%. "
        f"O'zlashtirish ko'rsatkichi (≥{int(th.get('pass', 56))} ball) — {a['pass_rate']}%, "
        f"sifat ko'rsatkichi (≥{int(th.get('quality', 71))} ball) — {a['quality_rate']}%. "
        f"Baholar taqsimoti: «5» — {a['distribution']['5']}, «4» — {a['distribution']['4']}, «3» — {a['distribution']['3']}, «2» — {a['distribution']['2']}."
    )

    weak = a.get("weak_topics") or []
    if weak:
        hardest = weak[0]
        others = ", ".join(f"«{w['topic']}» ({w['average_score']}%)" for w in weak[1:3])
        text = f"Eng qiyin mavzu — «{hardest['topic']}»: o'rtacha {hardest['average_score']}%, o'zlashtirish {hardest['pass_rate']}%."
        if others:
            text += f" Keyingi o'rinlarda: {others}."
        crit = a.get("criteria_stats") or []
        if crit:
            text += f" Mezonlar kesimida talabalar eng ko'p «{crit[0]['criterion']}» bo'yicha qiynalmoqda (o'rtacha {crit[0]['average_percent']}%)."
        paragraphs.append(text)

    risk = a.get("at_risk_students") or []
    if risk:
        names = ", ".join((r.get("student_name") or r["student_id"]) for r in risk[:5])
        more = f" va yana {len(risk) - 5} nafar" if len(risk) > 5 else ""
        paragraphs.append(f"Xavf guruhida {len(risk)} nafar talaba bor (o'rtacha yoki oxirgi ball o'zlashtirish chegarasidan past): {names}{more}. Ular bilan qo'shimcha konsultatsiya va qayta topshirish imkoniyatini rejalashtirish tavsiya etiladi.")
    else:
        paragraphs.append("O'zlashtirish chegarasidan past natija ko'rsatgan talabalar yo'q.")

    integ = a.get("integrity") or {}
    flags = []
    if integ.get("plagiarism_flags"):
        flags.append(f"{integ['plagiarism_flags']} ta ishda plagiat belgilari")
    if integ.get("ai_flags"):
        flags.append(f"{integ['ai_flags']} ta ishda AI-matn ehtimoli yuqori")
    if integ.get("similarity_flags"):
        flags.append(f"{integ['similarity_flags']} ta ish bir-biriga juda o'xshash")
    if flags:
        paragraphs.append("Akademik halollik: " + "; ".join(flags) + ". Ushbu ishlar o'qituvchi tomonidan alohida ko'rib chiqilishi lozim.")

    agr = a.get("ai_teacher_agreement") or {}
    if agr.get("reviewed_count"):
        paragraphs.append(
            f"Inson nazorati: {a['confirmed_count']} ta baho o'qituvchi tomonidan tasdiqlangan, {agr.get('edited_count', 0)} tasi tuzatilgan. "
            f"AI va o'qituvchi baholari o'rtasidagi o'rtacha farq — {agr['mean_abs_diff']} ball, {agr['within_5_points_pct']}% hollarda farq 5 balldan oshmagan."
        )

    recs = []
    if weak:
        recs.append(f"«{weak[0]['topic']}» mavzusi bo'yicha qo'shimcha amaliy mashg'ulot yoki video-material tayyorlash")
    crit = a.get("criteria_stats") or []
    if crit and crit[0]["average_percent"] < 70:
        recs.append(f"«{crit[0]['criterion']}» mezoni bo'yicha talablarni talabalarga namuna bilan tushuntirish")
    if a["pass_rate"] < 70:
        recs.append("o'zlashtirish pastligi sababli guruh uchun qayta topshirish (retake) haftasini belgilash")
    if a["quality_rate"] >= 60:
        recs.append("yuqori natijali talabalarni olimpiada va ilmiy to'garaklarga jalb qilish")
    if recs:
        paragraphs.append("Tavsiyalar: " + "; ".join(recs) + ".")

    paragraphs.append(f"Avtomatlashtirilgan tekshiruv hisobiga o'qituvchining taxminan {a['time_saved_hours']} soat vaqti tejaldi.")
    return "\n\n".join(paragraphs)


def short_summary(a: Dict[str, Any], course: Optional[str] = None, group: Optional[str] = None) -> str:
    scope = f"{course or 'Barcha fanlar'} — {group or 'barcha guruhlar'}"
    if not a or not a.get("total_grades"):
        return f"{scope}: baholangan ishlar yo'q."
    text = f"{scope}: {a['total_grades']} ta ish, o'rtacha {a['average_score']}%, o'zlashtirish {a['pass_rate']}%, sifat {a['quality_rate']}%."
    weak = a.get("weak_topics") or []
    if weak:
        text += " Eng qiyin mavzular: " + ", ".join(f"{w['topic']} ({w['average_score']}%)" for w in weak[:3]) + "."
    return text
