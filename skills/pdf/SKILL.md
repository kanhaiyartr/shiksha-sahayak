---
name: pdf
description: Render a Shiksha Sahayak worksheet draft to a printable PDF with reportlab. Use only after the structured worksheet JSON exists. Do not use for lesson plans or question banks.
---

# Worksheet PDF

Create a PDF from the validated worksheet object. Use reportlab (`SimpleDocTemplate`, `Paragraph`, `Spacer`). Embed `app/fonts/NotoSansDevanagari-Regular.ttf` so Hindi and English both print.

Include, in order:

1. A banner: draft until officer approval, or official after approval.
2. Title, class, subject, and chapter.
3. Sections and questions.
4. Answer key.
5. Teacher notes and source locators.

Do not call Claude to typeset the file. Do not invent questions that are not in the structured object. Do not mark the PDF approved unless the draft status is already approved.
