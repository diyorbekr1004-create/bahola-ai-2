# Taqdimot va xakaton strategiyasi (hakamlar uchun)

Bir kishi 7 daqiqada butun tizimni ko'rsatishi uchun **3 ta aniq natija** kifoya. Har bir natija uchun quyida tayyor ssenariy, gapiriladigan gaplar va zaxira variant berilgan.

## 0. Tayyorgarlik (namoyishdan 5 daqiqa oldin)

```bash
python scripts/seed.py --reset                 # 30 talaba, 110 baholangan ish, tasdiqlangan/tuzatilgan baholar
cd backend && uvicorn app.main:app             # 8000
streamlit run frontend/streamlit_app.py        # 8501
```

- Yon panelda «Backend: ok» yashil bo'lishi kerak.
- `samples/sample_submission.txt` (kuchli ish) va `samples/weak_submission.txt` (zaif ish) ochiq tursin.
- Internet bo'lmasa ham hammasi ishlaydi (oflayn evristika). OpenAI kaliti bo'lsa `.env` ga yozing — asoslar va xatolar yanada aniqroq bo'ladi.

## 1-natija — Real misol: Tekshirish (≈2 daqiqa)

**Ko'rsatish:** «Tekshirish» tabida guruh `AT-21-01`, talaba ro'yxatdan, fan `Pedagogika`, mavzu `Ta'lim va texnologiya`. `samples/sample_submission.txt` matnini joylang → **Baholash**.

**5 soniyada ekranda:** ball (masalan 84/100), 5 ballik baho, plagiat/AI/o'xshashlik indikatorlari, har bir mezon bo'yicha ball va **asos** (nima uchun shunday), kuchli tomonlar, **aniqlangan xatolar**, tavsiyalar.

**Gapiring:**
> «AI ballni bermaydi — taklif qiladi. O'qituvchi bir tugma bilan tasdiqlaydi yoki mezon bo'yicha tuzatadi, har bir tuzatish audit jurnaliga yoziladi. Tizim guruh ichida bir-biridan ko'chirilgan ishlarni ham topadi.»

**Keyin:** «✏️ Tuzatish» ni ochib bitta mezon ballini o'zgartiring → **Saqlash va tasdiqlash**. So'ng `weak_submission.txt` ni baholang — 2 baho va «ish juda qisqa», «xulosa yo'q» xatolari chiqadi.

**Zaxira:** «Fayl(lar) / ZIP» rejimida bir nechta DOCX tanlab batch baholashni ko'rsating (talaba ID fayl nomidan olinadi).

## 2-natija — Real misol: Hujjat (≈1.5 daqiqa)

**Ko'rsatish:** «Hujjatlar» tabida fan nomiga `Informatika` yozing → **Generatsiya qilish**.

**10 soniyada:** 15 haftalik silabus jadvali (mavzular, ma'ruza/amaliy/mustaqil soatlar, JN/ON/YN), dars rejasi (80 daqiqalik bosqichlar), 5 ta imtihon bileti, 10 ta test (javoblar kaliti bilan) va **bitta DOCX** yuklab olish tugmasi.

**Gapiring:**
> «Kafedra talab qiladigan hujjatlar to'plami — bitta so'zdan. O'qituvchi mavzular ro'yxatini o'zi ham kiritishi mumkin, tizim qolganini shakllantiradi.»

## 3-natija — Tejalgan vaqt va analitika (≈2 daqiqa)

**Ko'rsatish:** «Hisobotlar» tabida fan `Pedagogika` → **Hisobot yaratish**.

**Ekranda:** o'zlashtirish %, sifat ko'rsatkichi %, 5 ballik taqsimot grafigi, **eng qiyin mavzular** va **eng qiyin mezon** («Dalillar va tahlil»), xavf guruhidagi talabalar, AI ↔ o'qituvchi farqi (odatda 1–2 ball), **tejalgan vaqt**. Pastda kafedra mudiri uchun tayyor tahliliy xulosa.

**Bosing:** «🏛️ HEMIS jadvali (XLSX)» — HEMIS ustunlari (Talaba ID, F.I.Sh., Guruh, Fan, Nazorat turi, Ball, Baho 5) bilan tayyor fayl. «📝 Dekanat uchun DOCX» — imzo joylari bilan rasmiy hisobot.

**Gapiring (yakuniy gap):**
> «Bitta ishni qo'lda tekshirish o'rtacha 12 daqiqa. 30 talabalik guruhda 3 topshiriq — 18 soat. Bu tizim bilan o'qituvchi faqat tasdiqlaydi: 1–2 soat. Baholar HEMIS formatida tayyor — qayta qo'lda kiritilmaydi. Kafedra mudiri esa qaysi mavzuda talabalar qiynalayotganini birinchi marta raqamlarda ko'radi.»

## Hakamlarning ehtimoliy savollari va javoblar

| Savol | Javob |
|---|---|
| AI adolatli baholaydimi? | AI faqat taklif qiladi; o'qituvchi tasdiqlaydi/tuzatadi. Tizim AI va o'qituvchi baholari farqini o'lchab boradi (kalibratsiya ko'rsatkichi). |
| Internet/API bo'lmasa? | To'liq oflayn rejim bor (deterministik evristika), API kaliti qo'shilsa avtomatik kuchayadi, xato bo'lsa oflaynga qaytadi. |
| HEMIS bilan integratsiya? | HEMIS import jadvali formati `config/hemis_template.json` orqali oliygoh shabloniga 1 daqiqada moslanadi; API tayyor, to'g'ridan-to'g'ri integratsiya keyingi bosqich. |
| Shaxsiy ma'lumotlar? | Faqat talaba ID va F.I.Sh. saqlanadi, audit jurnali bor, PostgreSQL + HTTPS bilan ishlab chiqarishga tayyor (`PRIVACY.md`). |
| Plagiat? | Uch daraja: takroriy iboralar, AI-uslub belgilari, guruh ichida ishlar o'rtasidagi o'xshashlik (kimdan ko'chirilgani ko'rsatiladi). |
| Kengaytirish? | Rubrika shablonlari, topshiriqlar, etalon javoblar — hammasi o'qituvchi tomonidan UI orqali. |

## Vaqt taqsimoti (7 daqiqa)

1. Muammo (30 s): o'qituvchi haftasiga 15–20 soat tekshiradi va qog'oz to'ldiradi.
2. Tekshirish demosi (2 min).
3. Hujjat demosi (1.5 min).
4. Analitika + HEMIS eksport (2 min).
5. Raqamlar va keyingi qadamlar (1 min): HEMIS API integratsiyasi, OCR (qo'lyozma), mobil ilova.
