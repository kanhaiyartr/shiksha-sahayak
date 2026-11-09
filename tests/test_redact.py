from app.redact import prepare_text, redact_text


def test_leaves_ordinary_classroom_text_alone():
    text = "Class 5, Chapter 4, year 2024. Teach fractions on Monday."
    cleaned, counts = redact_text(text)
    assert cleaned == text
    assert counts == {}


def test_redacts_email_phone_aadhaar_school_id_and_names():
    text = (
        "Student name: PriyaZZ SharmaZZ, phone 9876543210, "
        "email priya.zz@example.com, aadhaar 1111 2222 3333, school 12345678901. "
        "Also +91 9876543210 and 111122223333."
    )
    cleaned, counts = redact_text(text)
    for secret in ("PriyaZZ", "SharmaZZ", "9876543210", "priya.zz@example.com", "1111 2222 3333", "111122223333", "12345678901"):
        assert secret not in cleaned
    assert counts["email"] == 1
    assert counts["phone"] == 2
    assert counts["aadhaar"] == 2
    assert counts["school_id"] == 1
    assert counts["name"] == 1


def test_keeps_synthetic_school_codes_and_redacts_hindi_labels():
    text = "विद्यार्थी का नाम: मीरा शर्मा. Synthetic code 99000000001."
    cleaned, counts = redact_text(text)
    assert "मीरा" not in cleaned
    assert "99000000001" in cleaned
    assert counts["name"] == 1


def test_my_student_pattern():
    cleaned, counts = redact_text("Please help my student Anika Sharma with fractions.")
    assert "Anika" not in cleaned
    assert counts["name"] == 1
