from app.analytics import build_narrative, compute_analytics, score_to_grade5


def _row(sid, score, topic="T1", group="G1", rubric=None, status="pending", ai=None, created="2026-01-01T00:00:00"):
    return {"student_id": sid, "student_name": None, "group_name": group, "course": "C", "topic": topic, "total_score": score, "max_score": 100,
            "ai_total_score": ai if ai is not None else score, "rubric": rubric or [], "status": status, "confirmed": status != "pending",
            "plagiarism_score": 0.1, "ai_likelihood": 0.1, "similarity_score": 0.0, "created_at": created}


def test_score_to_grade5_thresholds():
    assert score_to_grade5(100) == 5 and score_to_grade5(86) == 5
    assert score_to_grade5(85) == 4 and score_to_grade5(71) == 4
    assert score_to_grade5(70) == 3 and score_to_grade5(56) == 3
    assert score_to_grade5(55) == 2 and score_to_grade5(0) == 2
    assert score_to_grade5(43, max_score=50) == 5  # 86%


def test_pass_and_quality_rates():
    rows = [_row("a", 90), _row("b", 75), _row("c", 60), _row("d", 40)]
    a = compute_analytics(rows)
    assert a["total_grades"] == 4
    assert a["pass_rate"] == 75.0     # 3 of 4 >= 56
    assert a["quality_rate"] == 50.0  # 2 of 4 >= 71
    assert a["distribution"] == {"5": 1, "4": 1, "3": 1, "2": 1}
    assert a["average_score"] == 66.25
    assert a["at_risk_students"][0]["student_id"] == "d"
    assert a["top_students"][0]["student_id"] == "a"


def test_weak_topics_and_criteria():
    rows = [
        _row("a", 90, topic="Oson", rubric=[{"name": "Xulosa", "max_score": 20, "score": 20}, {"name": "Dalillar", "max_score": 30, "score": 10}]),
        _row("b", 40, topic="Qiyin", rubric=[{"name": "Xulosa", "max_score": 20, "score": 18}, {"name": "Dalillar", "max_score": 30, "score": 5}]),
    ]
    a = compute_analytics(rows)
    assert a["weak_topics"][0]["topic"] == "Qiyin"
    assert a["criteria_stats"][0]["criterion"] == "Dalillar"
    assert a["criteria_stats"][0]["difficulty"] > a["criteria_stats"][1]["difficulty"]


def test_student_trend_and_agreement():
    rows = [
        _row("s", 50, created="2026-01-01T00:00:00", status="confirmed"),
        _row("s", 80, created="2026-02-01T00:00:00", status="edited", ai=70),
    ]
    a = compute_analytics(rows)
    st = a["student_stats"][0]
    assert st["count"] == 2 and st["trend"] == 30.0 and st["last_score"] == 80.0
    assert a["ai_teacher_agreement"]["edited_count"] == 1
    assert a["ai_teacher_agreement"]["mean_abs_diff"] == 5.0
    assert a["ai_teacher_agreement"]["within_5_points_pct"] == 50.0  # 0 va 10 ball farq


def test_empty_and_narrative():
    a = compute_analytics([])
    assert a["total_grades"] == 0 and a["pass_rate"] == 0.0
    assert "yo'q" in build_narrative(a, course="X").lower()
    b = compute_analytics([_row("a", 30), _row("b", 95, topic="T2")])
    text = build_narrative(b, course="Fizika", group="G1")
    assert "Fizika" in text and "Xavf guruhida" in text and "Tavsiyalar" in text
