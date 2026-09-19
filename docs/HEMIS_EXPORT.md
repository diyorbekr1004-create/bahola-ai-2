# HEMIS eksport formati

HEMIS (Oliy ta'lim boshqaruvi axborot tizimi) ga baholarni import qilish jadvali oliygohdan oliygohga farq qilishi mumkin. Shuning uchun ustunlar **`config/hemis_template.json`** orqali boshqariladi — kodni o'zgartirmasdan moslashtiring.

## Default ustunlar

| № | Ustun | Maydon (`field`) | Izoh |
|---|---|---|---|
| 1 | № | `row_number` | tartib raqami |
| 2 | Talaba ID (HEMIS) | `student_id` | HEMIS talaba ID (import ro'yxatidan) |
| 3 | F.I.Sh. | `student_name` | |
| 4 | Guruh | `group_name` | |
| 5 | Fan | `course` | |
| 6 | Mavzu / Topshiriq | `topic` | |
| 7 | Nazorat turi | `control_type` | JN / ON / YN (hisobot yaratishda tanlanadi) |
| 8 | Ball (100) | `score` | butun son, 0–100 |
| 9 | Baho (5) | `grade_5` | 86–100→5, 71–85→4, 56–70→3, <56→2 (`.env` da o'zgartiriladi) |
| 10 | Sana | `date` | `%d.%m.%Y` |
| 11 | O'qituvchi | `teacher` | tasdiqlagan foydalanuvchi |
| 12 | Holat | `status` | Tasdiqlangan / Tuzatilgan / Tasdiqlanmagan |

Qo'shimcha mavjud maydon: `grade_id`.

## Moslashtirish

`config/hemis_template.json` faylida ustunlarni o'chiring, tartibini o'zgartiring yoki sarlavhasini oliygoh shabloniga moslang:

```json
{
  "sheet_name": "Baholar",
  "date_format": "%d.%m.%Y",
  "columns": [
    {"field": "student_id", "header": "ID"},
    {"field": "student_name", "header": "Talaba"},
    {"field": "score", "header": "Ball"},
    {"field": "grade_5", "header": "Baho"}
  ]
}
```

Fayl yo'li `HEMIS_TEMPLATE_PATH` muhit o'zgaruvchisi bilan o'zgartiriladi.

## Qanday olinadi

- UI: «Hisobotlar» → filtrlar → «Hisobot yaratish» → «🏛️ HEMIS jadvali (XLSX)» yoki «CSV».
- API: `GET /api/reports/export?format=hemis&course=Pedagogika&group_name=AT-21-01&only_confirmed=true&control_type=ON`
- Faqat o'qituvchi tasdiqlagan baholarni yuborish uchun `only_confirmed=true` dan foydalaning.

CSV `;` ajratuvchi va UTF-8 BOM bilan yoziladi — Excel'da to'g'ridan-to'g'ri ochiladi.

## To'liq Excel hisobot (`format=excel`)

5 varaq: **Baholar** (har bir mezon alohida ustun, eng zaif mezon, fikr-mulohaza), **Statistika**, **Mavzular**, **Mezonlar**, **Talabalar** (dinamika, xavf guruhi). O'zlashtirish chegarasidan past ballar qizil, a'lo ballar yashil fon bilan belgilanadi.
