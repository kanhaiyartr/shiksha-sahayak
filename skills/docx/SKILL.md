---
name: docx
description: Render a Shiksha Sahayak lesson plan or question bank to a DOCX file with python-docx. Use only after the structured JSON exists. Do not use for worksheets.
---

# Lesson plan and question bank DOCX

Create a Word file from the validated object. Use python-docx. Set the Normal style font to Noto Sans Devanagari so Hindi text is readable.

Include, in order:

1. A banner: draft until officer approval, or official after approval.
2. Title, class, subject, and chapter.
3. Sections in the order returned by the model.
4. Questions for a question bank.
5. Answer key for a question bank only. Leave the answer key out of a lesson plan.
6. Teacher notes and source locators.

Do not call Claude to typeset the file. Do not invent content that is not in the structured object. Do not mark the DOCX approved unless the draft status is already approved.
