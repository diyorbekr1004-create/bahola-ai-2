# Biznes model — AI O'qituvchi Hamkori (Bahola AI)

> Barcha raqamlar taxminiy va tekshirish uchun manba ko'rsatilgan. Valyuta kursi: ≈ 12 800 so'm / 1 USD.

## 1. Muammo va imkoniyat

| Ko'rsatkich | Qiymat | Manba / izoh |
|---|---|---|
| OTMlar soni | 200+ (davlat, xususiy, xorijiy filiallar) | edu.uz, stat.uz — aniqlashtiring |
| Talabalar | 1,3 mln+ | stat.uz |
| Professor-o'qituvchilar | ~40–45 ming | stat.uz |
| Tekshirish va hujjatga ketadigan vaqt | 15–20 soat/hafta/o'qituvchi | o'qituvchilar so'rovi (pilotda o'lchanadi) |
| Bitta ishni qo'lda tekshirish | ~12 daqiqa | kuzatuv; `.env` da sozlanadi |

**Og'riq nuqtalari:** (1) qo'lda tekshirish sekin va sub'ektiv, (2) baholar HEMIS'ga qayta qo'lda kiritiladi, (3) silabus/bilet/test har semestr qo'lda tuziladi, (4) kafedra qaysi mavzuda muammo borligini kech biladi, (5) ko'chirilgan ishlar aniqlanmaydi.

## 2. Mijoz segmentlari va qiymat taklifi

| Segment | Og'riq | Qiymat taklifi | Qaror qabul qiluvchi |
|---|---|---|---|
| O'qituvchi | vaqt, monotonlik | 15 soat → 1–2 soat; HEMIS'ga tayyor jadval | o'zi (Pro) / kafedra |
| Kafedra mudiri | sifat nazorati, hisobotlar | mavzu/mezon kesimida analitika, tayyor xulosa | kafedra |
| Dekanat / prorektor | akkreditatsiya, shaffoflik | audit, fakultet dashboardi, korrupsiya xavfi kamayadi | OTM rahbariyati |
| Xususiy OTM | raqobat, xarajat | tez joriy etish (1 kun), past narx | rektor/moliya |
| Vazirlik / HEMIS | tizimli ma'lumot | respublika kesimida o'zlashtirish analitikasi | davlat buyurtmasi |

**Birinchi mijoz (beachhead):** xususiy OTMlar va xorijiy filiallar — qaror tez, byudjet bor, raqobat kuchli. Keyin davlat OTMlari (vazirlik tavsiyasi bilan).

## 3. Daromad oqimlari va tariflar

| Tarif | Kimga | Narx | Nima kiradi |
|---|---|---|---|
| **Free** | yakka o'qituvchi | 0 | 30 ish/oy, oflayn baholash, hujjat generatori (3 ta/oy) |
| **Pro** | yakka o'qituvchi | 59 000 so'm/oy | cheksiz tekshirish, LLM, HEMIS eksport, batch |
| **Kafedra** | 20–99 o'qituvchi | 30 000 so'm/o'qituvchi/oy | Pro + umumiy rubrikalar, kafedra analitikasi |
| **Universitet** | 100+ o'qituvchi | 25 000 so'm/o'qituvchi/oy (yillik shartnoma) | + dekanat dashboardi, on-premise, SLA, o'qitish |
| **Integratsiya** | OTM | 20–50 mln so'm (bir martalik) | HEMIS/LMS ulash, rubrikalar, ma'lumot ko'chirish |
| **Analitika (vazirlik)** | davlat | kelishuv asosida | respublika/hudud kesimida agregat hisobotlar |

Qo'shimcha: o'qituvchilar uchun sertifikatli trening (500 ming so'm/kishi), API (edtech hamkorlar uchun, so'rov asosida).

## 4. Unit-ekonomika (bitta o'qituvchi, Universitet tarifi)

| Modda | Oyiga |
|---|---|
| Daromad | 25 000 so'm |
| LLM xarajati (150 ish × ~10 so'm, GPT-4o-mini: ~2 500 kirish + 700 chiqish token) | 1 500 so'm |
| Hosting/saqlash (ulushi) | 500 so'm |
| Qo'llab-quvvatlash (ulushi) | 1 000 so'm |
| **Yalpi foyda** | **22 000 so'm (≈ 88–94%)** |

Oflayn rejimda LLM xarajati 0. Mijozni jalb qilish xarajati (CAC) — OTM uchun ~5 mln so'm (2 uchrashuv + pilot); 500 o'qituvchili OTM yiliga 150 mln so'm → CAC 12 kunda qoplanadi.

## 5. Bozor hajmi

| | Hisob | So'm/yil | USD/yil |
|---|---|---|---|
| **TAM** (OTM + kollej + maktab o'qituvchilari, ~550 ming × 120 ming so'm) | | ~66 mlrd | ~$5,2 mln |
| **SAM** (OTM o'qituvchilari, 45 ming × 300 ming so'm) | | ~13,5 mlrd | ~$1,05 mln |
| **SOM** (3 yilda 20 ming o'qituvchi) | | ~6 mlrd | ~$470 ming |

Markaziy Osiyo (Qozog'iston, Qirg'iziston, Tojikiston) — rus tili qo'llab-quvvatlanadi, o'xshash boshqaruv tizimlari → 3-yildan keyin TAM 3–4 barobar.

## 6. Raqobat

| Raqib | Kuchli tomoni | Zaif tomoni | Bizning ustunlik |
|---|---|---|---|
| Turnitin | plagiat bazasi, brend | qimmat (talaba/yil), inglizcha, baholamaydi | o'zbekcha rubrika, HEMIS, narx |
| Gradescope | STEM baholash | AQSh bozori, HEMIS yo'q, o'zbek yo'q | lokal format, tahliliy xulosa |
| ChatGPT/Gemini qo'lda | universal | strukturasiz, audit yo'q, PII tashqariga | HITL + audit + on-premise |
| HEMIS | majburiy, hamma joyda | baholamaydi, tahlil qilmaydi | HEMIS'ni to'ldiradi, raqobat qilmaydi |
| Google Classroom / Moodle | tarqatish | AI baholash yo'q | ular bilan integratsiya (LMS eksport) |

**Himoya:** (1) o'zbek tilidagi rubrika/prompt bazasi, (2) HEMIS shablonlari, (3) kalibratsiya ma'lumotlari — har bir tasdiqlash tizimni OTM'ga moslaydi (switching cost), (4) qonunchilikka mos lokal joylashtirish.

## 7. Moliyaviy prognoz (3 yil, so'm)

| | 1-yil (2026/27) | 2-yil | 3-yil |
|---|---|---|---|
| OTMlar | 3–5 (pilot, chegirma) | 20 | 50 + 200 maktab/kollej |
| Pullik o'qituvchilar | 1 000 | 8 000 | 20 000 |
| Litsenziya daromadi | 240 mln | 2 400 mln | 6 000 mln |
| Pro (yakka) | 100 × 708 ming = 70 mln | 1 000 × 708 ming = 700 mln | 3 000 × 708 ming = 2 100 mln |
| Integratsiya | 3 × 25 mln = 75 mln | 10 × 25 mln = 250 mln | 20 × 25 mln = 500 mln |
| Vazirlik analitikasi | 0 | 0 | 1 000 mln |
| **Jami daromad** | **~450 mln** | **~3 300 mln** | **~9 600 mln** |
| Jamoa (3 → 6 → 12 kishi) | 360 mln | 900 mln | 2 200 mln |
| LLM + hosting | 40 mln | 150 mln | 400 mln |
| Marketing/sotuv | 100 mln | 250 mln | 600 mln |
| Boshqa (yuridik, ofis) | 100 mln | 100 mln | 300 mln |
| **Jami xarajat** | **~600 mln** | **~1 400 mln** | **~3 500 mln** |
| **Natija** | **−150 mln** | **+1 900 mln** | **+6 100 mln** |

**Zararsizlik:** oylik doimiy xarajat ~60 mln so'm (6 kishi) ÷ 25 000 so'm = ~2 400 pullik o'qituvchi ≈ 6 o'rta OTM — 2-yil 1-choragi.
**Kerakli mablag':** 250–300 mln so'm (≈ $20–25 ming) — 1-yil pilotlari uchun (grant: IT Park, Yoshlar ishlari agentligi, Startup Garage; yoki pre-seed).

## 8. O'sish strategiyasi (roadmap)

| Bosqich | Muddat | Maqsad | Asosiy ish |
|---|---|---|---|
| Pilot | 0–6 oy | 3 OTM, 1 000 o'qituvchi, NPS ≥ 40 | HEMIS shablonlari, o'qitish, kalibratsiya |
| Mahsulot-bozor mosligi | 6–12 oy | 10 OTM, retention ≥ 80% | LMS integratsiya, mobil ko'rinish, OCR (qo'lyozma) |
| Masshtab | 12–24 oy | 20+ OTM, vazirlik hamkorligi | HEMIS API integratsiyasi, og'zaki javob (STT), fakultet dashboardi |
| Kengayish | 24–36 oy | maktab/kollej, Markaziy Osiyo | rus/qozoq tili, talaba «AI mentor» ilovasi |

Sotuv kanallari: (1) to'g'ridan-to'g'ri (rektor/prorektor uchrashuvlari, konferensiyalar), (2) vazirlik va HEMIS operatori orqali tavsiya, (3) o'qituvchilar hamjamiyati (Free → Pro → kafedra), (4) IT Park rezidentligi (soliq imtiyozlari, eksport).

## 9. Asosiy KPI

- Haftalik faol o'qituvchilar (WAU), bir o'qituvchiga tekshirilgan ishlar soni
- Tasdiqlash ulushi (AI bahosi o'zgartirilmasdan qabul qilingan %) va AI ↔ o'qituvchi farqi (ball)
- Tejalgan soat (o'qituvchi/hafta), HEMIS'ga eksport qilingan baholar ulushi
- Retention (OTM, 12 oy), NPS, CAC / LTV (maqsad: LTV ≥ 5 × CAC)

## 10. Risklar va javoblar

| Risk | Ehtimol | Javob |
|---|---|---|
| O'qituvchilar AI'ga ishonmaydi | o'rta | HITL: AI faqat taklif qiladi; asoslar ko'rsatiladi; kalibratsiya metrikasi ochiq |
| Shaxsiy ma'lumotlar / lokalizatsiya | o'rta | on-premise, oflayn rejim, minimal PII, audit |
| HEMIS formati o'zgaradi | yuqori | shablon (`hemis_template.json`) 1 daqiqada moslanadi; API integratsiya rejada |
| LLM narxi / mavjudligi | past | provayderga bog'liq emas (OpenAI/Groq/Ollama), oflayn evristika |
| Davlat OTMlarida sekin sotib olish | yuqori | avval xususiy OTMlar, vazirlik tavsiyasi, grant orqali bepul pilot |
| Raqobatchi (xalqaro) kirib keladi | past | lokal format + narx + ma'lumot; hamkorlik imkoniyati |

## 11. Qonunchilik va etika

- «Shaxsiy ma'lumotlar to'g'risida»gi Qonun (O'RQ-547) va lokalizatsiya talabi — OTM serverida saqlash, PII minimal, LLM'ga ID yuborilmaydi.
- «Ta'lim to'g'risida»gi Qonun (O'RQ-637), HEMIS nizomi — yakuniy bahoni faqat o'qituvchi tasdiqlaydi, audit jurnali.
- Sun'iy intellekt strategiyasi-2030 va «Raqamli O'zbekiston-2030» — ta'limda AI ustuvor.
- Etika: plagiat/AI-matn belgilari ayblov emas, signal; talabaga fikr-mulohaza tushunarli tilda; algoritm shaffof (asoslar).
(Hujjat raqamlari lex.uz orqali tekshiriladi.)
