# API qo'llanmasi

Interaktiv hujjat: `http://localhost:8000/docs` (Swagger) yoki `/redoc`.
Auth: `AUTH_REQUIRED=false` (default) — token shart emas. `true` bo'lsa `Authorization: Bearer <token>`; token `POST /auth/token` (form: username, password) orqali.

## Baholash

```bash
# Matn
curl -X POST http://localhost:8000/api/grade \
  -F "text=$(cat samples/sample_submission.txt)" -F student_id=300101 -F student_name="Karimov Aziz" \
  -F group_name=AT-21-01 -F course=Pedagogika -F topic="Ta'lim va texnologiya"

# Fayl + o'z rubrikasi + etalon javob
curl -X POST http://localhost:8000/api/grade -F file=@ish.docx -F course=Fizika \
  -F 'rubric=[{"name":"Mavzuga moslik","max_score":50},{"name":"Xulosa","max_score":50}]' \
  -F reference_answer="Tezlik, tezlanish, yo'l formulasi"

# Batch: bir nechta fayl yoki ZIP (talaba ID fayl nomidan)
curl -X POST http://localhost:8000/api/grade/batch -F files=@ishlar.zip -F course=Pedagogika -F group_name=AT-21-01
```

Javob (`GradeResponse`): `grade_id, total_score, max_score, grade_5, rubric[{name,max_score,score,evidence}], feedback{summary,strengths,errors,suggestions}, integrity{plagiarism_score, ai_likelihood, similarity_score, similar_to_student, reasons, flags}, status, provider, processing_ms`.

Boshqa endpointlar:
- `GET /api/grades?course=&group_name=&topic=&student_id=&status=pending|confirmed|edited&only_confirmed=&limit=&offset=`
- `GET /api/grade/{id}` · `DELETE /api/grade/{id}`
- `POST /api/grade/{id}/confirm` — `{"teacher_id": "...", "comment": "..."}`
- `POST /api/grade/{id}/edit` — `{"corrected_rubric":[{"name":..,"max_score":..,"score":..}], "corrected_total": 80, "comment": "...", "confirm": true}`
- `GET /api/grade/{id}/feedback.docx` — talaba uchun fikr-mulohaza varaqasi
- `POST /api/detect` — `{"text": "...", "compare_with": ["..."]}`

## Hujjatlar

```bash
curl -X POST http://localhost:8000/api/generate-docs -H 'Content-Type: application/json' \
  -d '{"course_name":"Informatika","hours":60,"weeks":15,"level":"Bakalavriat","n_tickets":5,"n_questions":10,
       "doc_types":["syllabus","lesson_plan","exam_tickets","test_questions"],"topics":null,"export_format":"docx"}'
```

Javob: matnli `syllabus/lesson_plan/exam_ticket/test_questions`, `structured` (JSON), `download_url` (`/api/exports/<fayl>.docx`), `document_id`.
`GET /api/documents`, `GET /api/documents/{id}`, `GET /api/documents/{id}/download`.

## Hisobotlar va eksport

```bash
curl -X POST http://localhost:8000/api/reports -H 'Content-Type: application/json' \
  -d '{"course_name":"Pedagogika","group_name":"AT-21-01","only_confirmed":false,"export_format":"all","control_type":"JN","use_llm_summary":false}'
```

`analytics` maydonlari: `total_grades, total_students, average_score, median_score, pass_rate, quality_rate, distribution{5,4,3,2}, histogram, weak_topics, criteria_stats, group_stats, student_stats, at_risk_students, top_students, integrity, ai_teacher_agreement, time_saved_hours, thresholds`.
Havolalar: `download_url` (Excel), `hemis_download_url`, `csv_download_url`, `dean_report_url`.

To'g'ridan-to'g'ri fayl: `GET /api/reports/export?format=hemis|excel|csv|dean&course=&group_name=&topic=&only_confirmed=&control_type=`.

## Ma'lumotnomalar

- `GET/POST /api/students`, `POST /api/students/import` (XLSX/CSV; ustunlar: Talaba ID / HEMIS ID / student_id, F.I.Sh. / full_name, Guruh / group), `DELETE /api/students/{pk}`
- `GET/POST /api/groups`
- `GET /api/rubrics/default`, `GET/POST /api/rubrics`, `DELETE /api/rubrics/{id}`
- `GET/POST /api/assignments`, `DELETE /api/assignments/{id}` — topshiriq (fan, mavzu, guruh, rubrika, etalon javob); `assignment_id` bilan baholaganda metadata avtomatik to'ldiriladi

## Tizim

`GET /api/health`, `GET /api/config`, `GET /api/stats`, `GET /api/audit?limit=&action=`, `GET /api/exports` (fayllar ro'yxati), `GET /api/exports/{filename}`.
Auth: `POST /auth/token`, `POST /auth/signup`, `GET /auth/me`.
