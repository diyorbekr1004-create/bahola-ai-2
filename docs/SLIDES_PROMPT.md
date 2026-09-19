# Slayd uchun prompt (Gamma / Canva AI / ChatGPT / Copilot)

Quyidagi promptni to'liq nusxalab slayd generatoriga bering. Skrinshotlar: `docs/` dagi taqdimot uchun `frontend` dan olingan 3 ta rasm (Tekshirish, Hisobotlar, Hujjatlar) — ularni 4, 5, 6-slaydlarga qo'ying.

---

```
Sen professional pitch-deck dizaynerisan. O'zbek tilida (lotin yozuvi), xakaton hakamlari uchun 14 slaydli taqdimot tayyorla.
Mavzu: «AI O'qituvchi Hamkori (Bahola AI)» — oliy ta'lim o'qituvchilari uchun talaba ishlarini AI bilan tekshirish, o'qituvchi tasdiqlashi (human-in-the-loop), HEMIS/Excel eksport, kafedra uchun analitika va o'quv hujjatlarini (silabus, dars rejasi, biletlar, testlar) avtomatik yaratish tizimi.

Uslub: minimalistik, ko'p bo'sh joy, asosiy rang #2a78d6 (ko'k), urg'u #eb6834 (to'q sariq), matn #0b0b0b, fon oq/och kulrang. Har slaydda bitta asosiy fikr, 3–5 ta qisqa punkt, katta raqamlar. Shrift: zamonaviy sans-serif. Har slayd uchun 2–3 jumlalik "speaker notes" ham yoz.
Hakamlar 3 mentor bo'yicha baholaydi: Texnik (amalga oshirish, kod tayyorligi, innovatsiya, bilim, texnologiyalar), Biznes (dolzarblik, biznes model, raqobat, moliya, o'sish), Soha (dolzarblik, sohani tushunish, amaliy qo'llanish, qonunchilik, ta'sir ko'lami). Har bir mezon kamida bitta slaydda aniq javob topsin.

1. Titul: «AI O'qituvchi Hamkori» — "O'qituvchining haftalik 15–20 soatlik tekshirish vaqti 1–2 soatga". Jamoa nomi, xakaton nomi, sana. Vizual: kichik dashboard skrinshoti.
2. Muammo: 3 ta katta raqam — «15–20 soat/hafta tekshirish va hujjat», «200+ OTM, 1,3 mln talaba, 40 ming+ o'qituvchi», «har bir baho HEMIS'ga qo'lda kiritiladi». Punktlar: sub'ektiv baholash, kech fikr-mulohaza, kafedra qiyin mavzuni sessiyadan keyin biladi, ko'chirish aniqlanmaydi.
3. Yechim (bir qarashda): 3 ustun — «Tekshirish» (yuklash → 5 soniyada ball, asoslar, xatolar → o'qituvchi tasdiqlaydi), «Hujjatlar» (fan nomi → 10 soniyada silabus, dars rejasi, biletlar, testlar, DOCX), «Hisobotlar» (o'zlashtirish, sifat, qiyin mavzular, HEMIS eksport). Pastda: "AI taklif qiladi — o'qituvchi qaror qiladi".
4. Demo 1 — Tekshirish: skrinshot (tekshirish tabi). Yon tomonda oqim: fayl/ZIP → rubrika → ball + asos har mezon uchun → xatolar va tavsiyalar → plagiat / AI-matn / guruh ichidagi o'xshashlik → Tasdiqlash yoki Tuzatish → audit.
5. Demo 2 — Hujjatlar: skrinshot (hujjatlar tabi). Punktlar: 15 haftalik silabus (soatlar, JN/ON/YN), 80 daqiqalik dars rejasi, N ta bilet, testlar javob kaliti bilan, hammasi bitta DOCX.
6. Demo 3 — Hisobotlar va HEMIS: skrinshot (hisobotlar tabi). KPI: o'zlashtirish %, sifat %, 5 ballik taqsimot, eng qiyin mavzu va mezon, xavf guruhi, tejalgan vaqt. Tugmalar: HEMIS XLSX, Excel, CSV, dekanat DOCX. "O'qituvchi baholarni qayta qo'lda kiritmaydi".
7. Qanday ishlaydi (arxitektura): oddiy diagramma — Streamlit panel → FastAPI → [Rubrika + LLM (OpenAI/Groq/Ollama) yoki oflayn evristika] → yagona baza (SQLite/PostgreSQL) → eksportlar (HEMIS/Excel/DOCX). Belgilar: 39 avtomatik test, CI (Linux+Windows), Docker, 1 buyruqli o'rnatish.
8. Innovatsiya va texnik ustunlik: 4 ta karta — (1) Human-in-the-loop kalibratsiya: AI ↔ o'qituvchi farqi o'lchanadi (odatda 1–2 ball); (2) guruh ichida o'xshashlik — kim kimdan ko'chirgani; (3) mezon/mavzu kesimida qiyinchilik xaritasi; (4) shablon bilan boshqariladigan HEMIS eksport + oflayn rejim (ma'lumot OTM ichida qoladi).
9. Sohani tushunish va qonunchilik: JN/ON/YN, 100→5 ballik shkala (86/71/56), o'zlashtirish/sifat formulalari, silabus soatlari (ma'ruza/amaliy/mustaqil). Qonunchilik: «Shaxsiy ma'lumotlar to'g'risida»gi qonun (lokal saqlash, minimal PII), «Ta'lim to'g'risida»gi qonun (yakuniy baho — o'qituvchi), AI strategiyasi-2030 va Raqamli O'zbekiston-2030 ga mos.
10. Bozor: TAM/SAM/SOM uchta doira — TAM ~66 mlrd so'm/yil (OTM+kollej+maktab), SAM ~13,5 mlrd (OTM), SOM ~6 mlrd (3 yilda 20 ming o'qituvchi). Kengayish: Markaziy Osiyo (rus tili).
11. Biznes model: tariflar jadvali — Free (30 ish/oy), Pro 59 000 so'm/oy, Kafedra 30 000 so'm/o'qituvchi/oy, Universitet 25 000 so'm/o'qituvchi/oy (yillik), Integratsiya 20–50 mln so'm, Vazirlik analitikasi. Unit-ekonomika: bitta ish ≈ 10 so'm LLM xarajati, yalpi marja ~90%.
12. Raqobat: jadval — Bahola AI vs Turnitin vs Gradescope vs ChatGPT (qo'lda) vs HEMIS. Qatorlar: o'zbekcha rubrika, HEMIS eksport, o'qituvchi tasdiqlashi + audit, guruh ichida o'xshashlik, kafedra analitikasi, oflayn/on-premise, narx. Pastda "moat": o'zbek tili + HEMIS + kalibratsiya ma'lumotlari.
13. Moliya va o'sish: 3 yillik jadval (daromad ~0,45 → 3,3 → 9,6 mlrd so'm; natija −0,15 → +1,9 → +6,1 mlrd), zararsizlik ~2 400 pullik o'qituvchi (≈6 OTM), kerakli mablag' 250–300 mln so'm pilot uchun. Roadmap: pilot (3 OTM) → 10 OTM → vazirlik hamkorligi/HEMIS API → maktab/kollej va Markaziy Osiyo.
14. Ta'sir ko'lami va yakun: raqamlar — o'qituvchiga haftasiga 13–18 soat; talabaga 24 soat ichida asosli fikr-mulohaza; OTM'ga shaffoflik va akkreditatsiya analitikasi; tizim darajasida ~700 ming soat/hafta tejaladi (45 ming o'qituvchi × 15 soat). Chaqiriq: "3 OTM bilan pilotga tayyormiz — bugun boshlaymiz". Kontakt va QR (GitHub repo).

Har slayd sarlavhasi 6 so'zdan oshmasin; matn punktlari 12 so'zdan oshmasin. Speaker notes'da hakamning ehtimoliy savoliga qisqa javob ham bo'lsin (masalan: "LLM ishlamasa?" — oflayn rejim; "AI adolatlimi?" — asoslar + o'qituvchi tasdiqlashi + kalibratsiya metrikasi; "Ma'lumotlar qayerda?" — OTM serverida, LLM'ga ID yuborilmaydi).
```

---

## Qisqa variant (agar generator uzun promptni qabul qilmasa)

```
O'zbek tilida 10 slaydli minimalistik pitch-deck (asosiy rang #2a78d6): «AI O'qituvchi Hamkori» — talaba ishlarini AI bilan tekshirish (o'qituvchi tasdiqlaydi), HEMIS/Excel eksport, kafedra analitikasi, silabus/bilet/test generatori. Slaydlar: muammo (15–20 soat/hafta, 40 ming+ o'qituvchi, HEMIS'ga qo'lda kiritish) → yechim (3 tab) → 3 demo skrinshot → arxitektura (FastAPI, Streamlit, LLM yoki oflayn, 39 test) → innovatsiya (HITL kalibratsiya, o'xshashlik, qiyinchilik xaritasi) → bozor (TAM 66 mlrd so'm, SAM 13,5 mlrd) → biznes model (25 000 so'm/o'qituvchi/oy, marja ~90%) → raqobat (Turnitin, Gradescope, ChatGPT, HEMIS) → moliya 3 yil (0,45 → 3,3 → 9,6 mlrd so'm) → ta'sir va chaqiriq. Har slaydga speaker notes.
```

## Skrinshotlar

Taqdimot uchun rasmlar `docs/img/` papkasida: `01_tekshirish.png`, `02_hisobotlar.png`, `03_hujjatlar.png` (yangilash: `bash scripts/run_dev.sh`, so'ng brauzerdan skrinshot).
