# Shaxsiy ma'lumotlar va xavfsizlik

- **Minimal ma'lumot:** talaba haqida faqat HEMIS ID, F.I.Sh. (ixtiyoriy) va guruh saqlanadi. Pasport, telefon, manzil kabi ma'lumotlar so'ralmaydi.
- **Ishlar matni** baholash asoslari va guruh ichidagi o'xshashlik tekshiruvi uchun bazada saqlanadi; o'qituvchi bahoni o'chirsa (`DELETE /api/grade/{id}`) ish matni ham o'chiriladi.
- **LLM provayder:** `OPENAI_API_KEY` berilganda ish matni tashqi API'ga yuboriladi. Talabalar rozi bo'lmasa `LLM_PROVIDER=mock` (to'liq oflayn) rejimidan foydalaning yoki o'z serveringizdagi modelni `OPENAI_BASE_URL` orqali ulang.
- **Audit jurnali** kim, qachon, qaysi bahoni yaratgani/tasdiqlagani/tuzatganini saqlaydi; jurnalga ish matni yozilmaydi.
- **Eksport fayllari** `exports/` papkasida; ishlab chiqarishda muddatli tozalash va faqat autentifikatsiyalangan yuklab olishni yoqing (`AUTH_REQUIRED=true`).
- **Parollar** PBKDF2-SHA256 (200 000 iteratsiya) bilan xeshlanadi; tokenlar JWT (HS256), muddati 24 soat.
- **Tavsiya:** HTTPS, PostgreSQL diskini shifrlash, `SECRET_KEY` ni maxfiy saqlash, `DEMO_USERS=false`.
