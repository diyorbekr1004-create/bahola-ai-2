# Hakamlar mezonlari bo'yicha javoblar (har bir mezon 1–10 ball)

Loyiha: **AI O'qituvchi Hamkori (Bahola AI)** — talaba ishlarini AI bilan tekshirish, o'qituvchi tasdiqlashi (human-in-the-loop), HEMIS/Excel eksport, kafedra uchun analitika va o'quv hujjatlarini avtomatik yaratish.

Har bir mezon uchun: **Da'vo** (nima deymiz) → **Dalil** (nimani ko'rsatamiz) → **Kutilgan savol va javob**.

---

## 1. Texnik mentor

### 1.1 Texnik amalga oshirish
**Da'vo.** Tizim to'liq ishlaydi: FastAPI backend (30+ endpoint), Streamlit boshqaruv paneli (4 tab), yagona baza (SQLite → PostgreSQL bir qatorda), fayl tahlili (TXT/DOCX/PDF/ZIP), HEMIS/Excel/CSV/DOCX eksport.
**Dalil.** Jonli demo: ish yuklanadi → 5 soniyada ball, asoslar, xatolar; «Hisobot yaratish» → HEMIS jadvali yuklab olinadi. `/docs` (Swagger) ochib API ko'rsatiladi.
**Savol:** «LLM ishlamasa nima bo'ladi?» — **Javob:** oflayn deterministik baholash rejimi bor (matn tuzilmasi, argumentlar, dalillar, mavzuga moslik evristikasi); LLM xato bersa avtomatik shu rejimga qaytadi, tizim hech qachon to'xtamaydi.

### 1.2 Kod tayyorligi
**Da'vo.** Ishlab chiqarishga yaqin sifat: 39 ta avtomatik test, CI (Linux 3.11/3.12 + Windows), lint, Docker Compose (Postgres bilan), `.env` sozlamalari, yengil migratsiya (eski baza buzilmaydi), audit jurnali, xatolarni markazlashgan qayta ishlash.
**Dalil.** GitHub Actions yashil belgisi; `pytest -q` → `39 passed`; bir buyruqli o'rnatish (`scripts/setup.ps1` / `setup.sh`).
**Savol:** «Xavfsizlik?» — **Javob:** PBKDF2 parol xeshi, JWT, rollar (o'qituvchi/kafedra/dekanat), path-traversal himoyasi, fayl hajmi cheklovi, minimal PII.

### 1.3 Yechimning innovatsionligi
**Da'vo.** Bozorda «tekshirish + HEMIS + analitika» bitta oqimda mavjud emas. Yangi elementlar: (1) **Human-in-the-loop kalibratsiya** — AI va o'qituvchi baholari farqi o'lchanadi (odatda 1–2 ball), (2) **guruh ichidagi o'xshashlik** — kim kimdan ko'chirganini ko'rsatadi, (3) **mezon bo'yicha qiyinchilik xaritasi** — kafedra mudiri qaysi mavzu/mezonda talabalar qiynalayotganini raqamda ko'radi, (4) **shablon bilan boshqariladigan HEMIS eksport** — har bir OTM o'z ustunlarini 1 daqiqada moslaydi.
**Dalil.** Hisobotlar tabida «AI ↔ o'qituvchi farqi» va «Qiyin mavzular» grafigi; Tekshirish tabida «O'xshashlik 78% (talaba 300117)».

### 1.4 Jamoaning bilim darajasi
**Da'vo.** Arxitektura qarorlari ongli: rubrika asosidagi strukturalangan baholash (erkin matn emas), JSON-rejimli LLM chaqiruvi + fallback, provayderga bog'liq bo'lmagan adapter (OpenAI, Groq, Ollama — bitta sozlama), deterministik evristika (testlar barqaror), pure-function analitika (DB'siz test qilinadi).
**Dalil.** Savollarga kod ko'rsatib javob berish: `analytics.py` (o'zlashtirish/sifat formulasi), `llm_adapter.py` (mezon → xususiyat xaritasi), `exports.py` (HEMIS shabloni).
**Savol:** «AI baholashi adolatli ekanini qanday isbotlaysiz?» — **Javob:** har bir ball uchun matndan **asos** (evidence) ko'rsatiladi; o'qituvchi tuzatishi saqlanadi va kalibratsiya metrikasi hisoblanadi; vaqt o'tishi bilan bu ma'lumotlar rubrika va promptlarni yaxshilash uchun ishlatiladi.

### 1.5 Texnologiyalar to'plami
| Qatlam | Texnologiya | Nima uchun |
|---|---|---|
| API | Python 3.11–3.14, FastAPI, Pydantic v2 | tez, tiplangan, avtomatik hujjat (`/docs`) |
| Baza | SQLModel/SQLAlchemy, SQLite → PostgreSQL | pilotda nol sozlash, ishlab chiqarishda Postgres |
| AI | OpenAI-ga mos API (GPT-4o-mini / Groq / Ollama) + oflayn evristika | arzon, almashtiriladigan, oflayn ishlaydi |
| Hujjatlar | python-docx, openpyxl, pypdf | DOCX/XLSX/PDF |
| UI | Streamlit + Plotly | bir dasturchi uchun tez, professional grafiklar |
| Sifat | pytest (39), pyflakes, GitHub Actions, Docker Compose | ishonchli yetkazib berish |

---

## 2. Biznes mentor

### 2.1 G'oya va muammoning dolzarbligi
**Da'vo.** O'zbekistonda 200+ OTM, 1,3 mln+ talaba, 40 mingdan ortiq professor-o'qituvchi (stat.uz / edu.uz ma'lumotlari bo'yicha, taqdimotdan oldin aniqlashtiring). O'qituvchi haftasiga o'rtacha 15–20 soatni ishlarni tekshirish, hujjat to'ldirish va HEMIS'ga qo'lda kiritishga sarflaydi — bu dars sifati va ilmiy ishga ketishi kerak bo'lgan vaqt.
**Dalil.** 30 talabalik guruh × 3 topshiriq × 12 daqiqa = 18 soat. Tizim bilan: 1–2 soat (faqat tasdiqlash). Hisobotlar tabidagi «Tejalgan vaqt» hisoblagichi.

### 2.2 Biznes modeli va monetizatsiya
**Da'vo.** B2B SaaS, «o'qituvchi/oy» litsenziyasi + integratsiya xizmati (batafsil: `docs/BIZNES_MODEL.md`).
- **Universitet litsenziyasi:** 25 000 so'm / o'qituvchi / oy (kamida 50 o'qituvchi). 500 o'qituvchili OTM = 150 mln so'm/yil.
- **Pro (yakka o'qituvchi):** 59 000 so'm/oy — LLM, HEMIS eksport, cheksiz tekshirish. **Free:** 30 ish/oy, oflayn rejim.
- **Integratsiya (bir martalik):** HEMIS/LMS ulash, rubrikalarni sozlash, o'qitish — 20–50 mln so'm.
- **Dekanat analitika moduli:** fakultet/OTM darajasidagi dashboard — +30% litsenziya narxiga.
**Unit-ekonomika.** Bitta ishni LLM bilan tekshirish ≈ 10 so'm (GPT-4o-mini); o'qituvchi oyiga ~150 ish → 1 500 so'm xarajat, 25 000 so'm daromad → **yalpi marja ~94%**.

### 2.3 Raqobatdagi ustunlik
| | Bahola AI | Turnitin | Gradescope | ChatGPT (qo'lda) | HEMIS |
|---|---|---|---|---|---|
| O'zbek tilida rubrika bo'yicha baholash | ✅ | ❌ | qisman | qisman, strukturasiz | ❌ |
| HEMIS formatida eksport | ✅ | ❌ | ❌ | ❌ | (o'zi) |
| O'qituvchi tasdiqlashi + audit | ✅ | — | ✅ | ❌ | ❌ |
| Guruh ichida o'xshashlik | ✅ | ✅ | ❌ | ❌ | ❌ |
| Kafedra analitikasi (qiyin mavzular) | ✅ | ❌ | qisman | ❌ | ❌ |
| Oflayn / ma'lumot OTM ichida | ✅ | ❌ | ❌ | ❌ | ✅ |
| Narx (o'qituvchi/oy) | ~$2 | $$$ (talaba/yil) | $$$ | $20 | — |
**Himoya (moat):** o'zbek tili + HEMIS formati + rubrika/kalibratsiya ma'lumotlari (har bir tasdiqlash modelni OTM'ga moslaydi) + qonunchilikka mos lokal joylashtirish.

### 2.4 Moliyaviy barqarorlik
**Da'vo.** Past o'zgaruvchan xarajat (LLM ≈ 10 so'm/ish, oflayn rejimda 0), asosiy xarajat — jamoa. **Zararsizlik nuqtasi:** ~2 400 pullik o'qituvchi (≈ 6 o'rta OTM) — 2-yil boshida.
| | 1-yil (pilot) | 2-yil | 3-yil |
|---|---|---|---|
| OTM soni | 3–5 | 20 | 50 + maktab/kollej piloti |
| Pullik o'qituvchilar | 1 000 | 8 000 | 20 000 |
| Daromad (so'm) | ~0,45 mlrd | ~3,3 mlrd | ~9,6 mlrd |
| Xarajat (so'm) | ~0,6 mlrd | ~1,4 mlrd | ~3,5 mlrd |
| Natija | −0,15 mlrd (grant/seed) | +1,9 mlrd | +6,1 mlrd |
(Taxminlar `docs/BIZNES_MODEL.md` da; kurs ≈ 12 800 so'm/$.)

### 2.5 O'sish imkoniyati
**Da'vo.** Uch bosqichli o'sish: (1) OTMlar (45 ming o'qituvchi), (2) kasb-hunar kollejlari va maktablar (500 ming+ o'qituvchi, «Raqamli ta'lim» dasturi), (3) Markaziy Osiyo va MDH (rus tili qo'llab-quvvatlanadi, HEMIS-ga o'xshash tizimlar). Qo'shimcha mahsulotlar: og'zaki javoblarni baholash (STT), qo'lyozma OCR, talaba uchun «AI mentor» ilovasi.

---

## 3. Soha mentori

### 3.1 Muammoning dolzarbligi
O'qituvchi yuklamasi: 2023-yildan kredit-modul tizimi va HEMIS majburiy — har bir JN/ON/YN balli qo'lda kiritiladi, har bir ish qo'lda tekshiriladi. Kafedra mudiri «qaysi mavzuda talabalar qiynalayapti» savoliga faqat sessiya natijasidan keyin javob oladi — kech. Tizim buni haftalik kesimda ko'rsatadi.

### 3.2 Sohani chuqur tushunish
Tizim OTM jarayonlariga mos qurilgan: JN/ON/YN nazorat turlari, 100 → 5 ballik shkala (86/71/56 chegaralari, `.env` da o'zgartiriladi), o'zlashtirish (≥56) va sifat (≥71) ko'rsatkichlari, silabusdagi soatlar taqsimoti (ma'ruza/amaliy/mustaqil), imtihon bileti va test shakli, dekanat uchun imzo joyli DOCX hisobot. Rubrikalar o'qituvchi tomonidan tuziladi — AI mezonni o'zi o'ylab topmaydi.

### 3.3 Amaliy qo'llanish
- **O'qituvchi:** haftalik ishlarni ZIP bilan yuklaydi → 30 ta baho 1 daqiqada → tasdiqlaydi → HEMIS jadvalini yuklab oladi.
- **Kafedra mudiri:** fan/guruh bo'yicha o'zlashtirish, qiyin mavzular, xavf guruhi — tahliliy xulosa tayyor.
- **Dekanat:** fakultet kesimida Excel/DOCX hisobot, akademik halollik belgilari.
- **Talaba:** har bir ish uchun asosli fikr-mulohaza varaqasi (DOCX) — nimani yaxshilash kerakligini biladi.
Joriy etish: 1 kun (SQLite, mavjud kompyuter) yoki OTM serverida Docker (Postgres). O'qitish — 1 soatlik trening.

### 3.4 Qonunchilikka muvofiqlik
- **«Shaxsiy ma'lumotlar to'g'risida»gi Qonun (O'RQ-547, 2019) va lokalizatsiya talabi:** ma'lumotlar OTM serverida saqlanadi (on-premise), faqat talaba ID va F.I.Sh.; LLM'siz oflayn rejim — matn tashqariga chiqmaydi; LLM ishlatilganda ID/ism yuborilmaydi, faqat matn.
- **«Ta'lim to'g'risida»gi Qonun (O'RQ-637, 2020) va HEMIS nizomi:** yakuniy baho faqat o'qituvchi tomonidan tasdiqlanadi — AI maslahatchi, qaror inson tomonidan (audit jurnali buni isbotlaydi).
- **Sun'iy intellekt strategiyasi-2030 (Prezident qarori, 2024-yil oktabr) va «Raqamli O'zbekiston-2030»:** ta'limda AI'ni joriy etish ustuvor yo'nalish — loyiha davlat siyosatiga mos.
- Akademik halollik: plagiat/AI-matn belgilari **ayblov emas, signal** — yakuniy qaror o'qituvchida.
(Hujjat raqamlarini taqdimotdan oldin lex.uz orqali tekshirib chiqing.)

### 3.5 Ta'sir ko'lami
- **O'qituvchi:** haftasiga 13–18 soat tejaladi → dars sifati, ilmiy ish, kasbiy o'sish.
- **Talaba:** har bir ishga 24 soat ichida asosli fikr-mulohaza (hozir — haftalar); ko'chirish kamayadi.
- **OTM:** baholash shaffofligi, korrupsiya xavfi kamayadi (audit), akkreditatsiya uchun tayyor analitika.
- **Tizim darajasida:** 45 ming o'qituvchi × 15 soat/hafta = ~700 ming soat/hafta — bu 17 ming to'liq stavka o'qituvchi vaqtiga teng.
