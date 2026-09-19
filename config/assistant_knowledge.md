# AI O'qituvchi Hamkori — yordamchi uchun bilimlar bazasi

## Sayt haqida
AI O'qituvchi Hamkori (Bahola AI) — oliy ta'lim o'qituvchilari uchun tizim: talaba ishlarini AI bilan tekshiradi (o'qituvchi tasdiqlaydi), o'quv hujjatlarini (silabus, dars rejasi, biletlar, testlar) yaratadi, baholarni HEMIS/Excel formatida eksport qiladi va kafedra uchun analitika beradi. Maqsad: o'qituvchining haftalik 15–20 soatlik tekshirish va qog'oz ishini 1–2 soatga qisqartirish.

## Bo'limlar (tablar)
- 🔎 Tekshirish — talaba ishini matn yoki fayl (TXT, DOCX, PDF, ZIP) sifatida yuklash, rubrika (mezonlar) tanlash, «Baholash» tugmasi. Natija: ball, 5 ballik baho, har mezon uchun asos, xatolar, tavsiyalar, plagiat/AI-matn/o'xshashlik. O'qituvchi «Tasdiqlash» yoki «Tuzatish» qiladi. Pastda saqlangan baholar ro'yxati (tasdiqlash navbati).
- 📄 Hujjatlar — fan nomi, soat, hafta kiritiladi → silabus (haftalik reja, soatlar, JN/ON/YN), dars rejasi (80 daqiqa), imtihon biletlari, test savollari (javob kaliti) va bitta DOCX fayl.
- 📊 Hisobotlar — fan/guruh/mavzu filtri → o'zlashtirish %, sifat %, 5 ballik taqsimot, qiyin mavzular va mezonlar, xavf guruhi, tejalgan vaqt, tahliliy xulosa. Eksport: HEMIS XLSX, to'liq Excel, CSV, dekanat DOCX. Audit jurnali.
- 👥 Talabalar — HEMIS ro'yxatini XLSX/CSV import qilish, talaba qo'shish, guruhlar, rubrika shablonlari.
- 💳 Tariflar — Free, Pro, Kafedra, Universitet rejalari, obuna va to'lov so'rovi, ROI kalkulyator, raqobatchilar bilan taqqoslash.
- 💬 Yordamchi — shu chat.

## Qanday ishlatiladi
1. (Ixtiyoriy) Yon panelda tizimga kiring: teacher/teacher123 (Free), admin/admin123 (Universitet). Kirmasangiz demo rejim (Universitet tarifi).
2. Tekshirish tabida guruh, talaba, fan, mavzuni kiriting, rubrikani tanlang, matn yoki faylni yuklang, «Baholash».
3. Natijani ko'rib «Tasdiqlash» yoki «Tuzatish» qiling — tasdiqlangan baholar HEMIS eksportiga tayyor.
4. Hisobotlar tabida «Hisobot yaratish» → HEMIS jadvalini yuklab oling.

## AI provayder
Tizim Google Gemini (GEMINI_API_KEY), OpenAI yoki OpenAI-ga mos server (Groq, Ollama) bilan ishlaydi. Kalit bo'lmasa oflayn deterministik baholash rejimi ishlaydi — tizim hech qachon to'xtamaydi. Provayder yon panelda ko'rsatiladi. Kalit yon paneldagi «AI kaliti» bo'limi orqali kiritiladi (u `.env` fayliga yoziladi) yoki qo'lda `.env` ga GEMINI_API_KEY=... yoziladi.

## Baholash shkalasi
100 ballik natija 5 ballikka o'tkaziladi: 86–100 → 5, 71–85 → 4, 56–70 → 3, 0–55 → 2 (.env da o'zgartiriladi). O'zlashtirish — 56 va undan yuqori ball olganlar ulushi; sifat ko'rsatkichi — 71 va undan yuqori.

## Ma'lumotlar va xavfsizlik
Talaba haqida faqat ID, F.I.Sh. va guruh saqlanadi. Baza OTM kompyuterida/serverida (SQLite yoki PostgreSQL). LLM'ga faqat ish matni yuboriladi, ID/ism yuborilmaydi. Oflayn rejimda hech narsa tashqariga chiqmaydi. Har bir amal audit jurnaliga yoziladi.

## FAQ
### Savol: Qanday boshlayman? Tizimni qanday ishlataman?
keywords: boshlash, boshlayman, qanday ishlataman, birinchi, start, qadam, yo'riqnoma
Javob: Tekshirish tabini oching, fan va mavzuni yozing, rubrikani tanlang, talaba matnini joylang yoki faylni yuklang va «Baholash» tugmasini bosing. 5 soniyada ball, asoslar va xatolar chiqadi. Keyin «Tasdiqlash» yoki «Tuzatish» qiling. Demo ma'lumot uchun `python scripts/seed.py --reset`.

### Savol: Qaysi fayl formatlarini yuklash mumkin?
keywords: fayl, format, docx, pdf, txt, zip, yuklash, yuklayman
Javob: TXT, MD, DOCX, PDF va ZIP (bir nechta ishni birdaniga). ZIP yoki bir nechta fayl yuklansa batch rejim ishlaydi — talaba ID fayl nomidan olinadi (masalan, 123456_Aliyev.docx). Batch Pro tarifidan boshlab mavjud.

### Savol: HEMIS eksport qanday qilinadi?
keywords: hemis, eksport, export, excel, jadval, yuklab olish, csv
Javob: Hisobotlar tabida fan/guruhni tanlab «Hisobot yaratish» tugmasini bosing, so'ng «HEMIS jadvali (XLSX)» tugmasi bilan faylni yuklab oling. Ustunlar: Talaba ID, F.I.Sh., Guruh, Fan, Nazorat turi (JN/ON/YN), Ball (100), Baho (5), Sana, O'qituvchi, Holat. Ustunlar `config/hemis_template.json` da oliygoh shabloniga moslanadi. HEMIS eksporti Pro tarifidan boshlab.

### Savol: AI baholashi adolatlimi? Ishonsa bo'ladimi?
keywords: adolat, adolatli, ishonch, ishonsa, to'g'ri baholaydimi, xato baholasa, aniqlik
Javob: AI ballni taklif qiladi, yakuniy qarorni o'qituvchi beradi. Har bir mezon uchun matndan asos ko'rsatiladi; o'qituvchi ballni tuzatishi mumkin va tuzatish audit jurnaliga yoziladi. Hisobotlarda «AI ↔ o'qituvchi farqi» ko'rsatkichi bor — odatda 1–2 ball.

### Savol: Ma'lumotlar qayerda saqlanadi? Xavfsizmi?
keywords: ma'lumot, saqlanadi, xavfsiz, maxfiylik, shaxsiy, server, baza, qonun
Javob: Baza OTM kompyuterida yoki serverida (SQLite/PostgreSQL). Talaba haqida faqat ID, F.I.Sh., guruh saqlanadi. LLM ishlatilganda faqat ish matni yuboriladi, oflayn rejimda hech narsa tashqariga chiqmaydi. Bu «Shaxsiy ma'lumotlar to'g'risida»gi qonun talablariga mos.

### Savol: Gemini yoki OpenAI kalitini qanday ulayman?
keywords: gemini, openai, api, kalit, key, ulash, ulayman, provayder, model, chatgpt
Javob: Loyiha ildizidagi `.env` fayliga GEMINI_API_KEY=... (Google AI Studio'dan) yoki OPENAI_API_KEY=... yozing, LLM_PROVIDER=auto qoldiring va backendni qayta ishga tushiring. Yon panelda «LLM: gemini» ko'rinadi. Kalit bo'lmasa oflayn rejim ishlaydi.

### Savol: Narxlar qancha? Tariflar qanday?
keywords: narx, narxi, tarif, pul, to'lov, obuna, bepul, pro, kafedra, universitet, qancha
Javob: Free — bepul, 30 ish/oy, oflayn baholash. Pro — 59 000 so'm/oy: cheksiz tekshirish, AI (LLM), batch, HEMIS eksport. Kafedra — 30 000 so'm/o'qituvchi/oy (kamida 20). Universitet — 25 000 so'm/o'qituvchi/oy (yillik, on-premise, dekanat dashboardi). Tariflar tabida obuna so'rovi yuboriladi va hisob-faktura olinadi.

### Savol: Plagiat va ko'chirishni aniqlaydimi?
keywords: plagiat, ko'chirish, ko'chirgan, o'xshash, ai-matn, chatgpt yozgan, halollik
Javob: Ha, uch daraja: takrorlanuvchi iboralar (plagiat belgisi), AI uslubi belgilari (AI-matn ehtimoli) va guruh ichida boshqa talabalar ishlari bilan o'xshashlik (kim bilan qancha foiz). Bu ayblov emas, signal — yakuniy qaror o'qituvchida.

### Savol: Rubrika (mezonlar) qanday o'zgartiriladi?
keywords: rubrika, mezon, mezonlar, ball taqsimoti, shablon, o'zgartirish
Javob: Tekshirish tabida «Baholash mezonlari» ro'yxatidan shablon tanlang yoki «O'zim kiritaman» bilan jadvalda mezon nomi va maksimal ballni yozing (jami 100 tavsiya etiladi). Talabalar tabining pastida shablonlarni saqlash mumkin.

### Savol: Login va parol nima? Kirish shartmi?
keywords: login, parol, kirish, foydalanuvchi, ro'yxatdan, hisob, akkaunt
Javob: Demo: teacher/teacher123 (Free tarif), admin/admin123 (Universitet), dekan/dekan123. Kirmasangiz ham demo rejimda ishlaydi (Universitet tarifi). Ishlab chiqarishda AUTH_REQUIRED=true qilinadi.

### Savol: 402 xatosi yoki «Tarif cheklovi» chiqdi
keywords: 402, cheklov, limit, tugadi, yopiq, ruxsat yo'q
Javob: Joriy tarif limiti tugagan (Free: 30 ish/oy) yoki funksiya tarifga kirmaydi (batch, HEMIS eksport, LLM). Tariflar tabida Pro yoki Kafedra tarifiga o'ting — demo rejimda to'lovni o'zingiz tasdiqlaysiz.

### Savol: Silabus va biletlar qanday yaratiladi?
keywords: silabus, dars rejasi, bilet, test, hujjat, generatsiya, yaratish
Javob: Hujjatlar tabida fan nomi, soat va haftalar sonini kiriting, hujjat turlarini tanlang va «Generatsiya qilish» tugmasini bosing. 15 haftalik silabus, dars rejasi, biletlar va testlar ekranda ko'rinadi, «DOCX yuklab olish» bilan bitta fayl olinadi. Mavzularni o'zingiz ham kiritishingiz mumkin.

### Savol: Tejalgan vaqt qanday hisoblanadi?
keywords: tejalgan, vaqt, soat, hisob, hisoblanadi, roi
Javob: Baholangan ishlar soni × bitta ishni qo'lda tekshirishga ketadigan daqiqa (default 12, MINUTES_PER_MANUAL_CHECK) ÷ 60. Tariflar tabidagi ROI kalkulyator talabalar va topshiriqlar soniga qarab oyiga tejalgan soat va so'mni ko'rsatadi.

### Savol: O'zlashtirish va sifat ko'rsatkichi nima?
keywords: o'zlashtirish, sifat, ko'rsatkich, foiz, statistika, baho taqsimoti
Javob: O'zlashtirish — 56 va undan yuqori ball (3, 4, 5 baho) olgan ishlar ulushi. Sifat ko'rsatkichi — 71 va undan yuqori (4 va 5 baho) ulushi. Chegaralar .env da o'zgartiriladi. Hisobotlar tabida guruh, fan va mavzu kesimida ko'rsatiladi.

### Savol: Xato chiqdi, backend ishlamayapti
keywords: xato, ishlamayapti, backend, ulanmadi, error, muammo, ochilmayapti
Javob: Backend alohida ishga tushirilishi kerak: `cd backend && uvicorn app.main:app --reload` yoki `bash scripts/run_dev.sh`. Yon panelda «Backend: ok» ko'rinishi kerak. Windows'da Git Bash'dan `bash scripts/setup.sh` bilan o'rnating.

### Savol: Loyiha kim uchun va kim yaratgan?
keywords: kim, muallif, jamoa, loyiha, maqsad, nima uchun, haqida
Javob: Loyiha oliy ta'lim o'qituvchilari, kafedra mudirlari va dekanat uchun xakaton doirasida yaratilgan. Maqsad — tekshirish va hujjat ishini avtomatlashtirib, o'qituvchi vaqtini dars sifatiga yo'naltirish. Kod GitHub'da: diyorbekr1004-create/bahola-ai-2.
