from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    for cccd in ("012345678901", "079203001234"):
        out = scrub_text(f"CCCD: {cccd}.")
        assert cccd not in out
        assert out == "CCCD: [REDACTED_CCCD]."


def test_scrub_credit_card_formats() -> None:
    for card in ("4111111111111111", "4111 1111 1111 1111", "4111-1111-1111-1111"):
        out = scrub_text(f"Card {card} expired")
        assert card not in out
        assert out == "Card [REDACTED_CREDIT_CARD] expired"


def test_scrub_vietnamese_passport() -> None:
    out = scrub_text("Passport C1234567 issued in Hanoi")
    assert "C1234567" not in out
    assert "REDACTED_PASSPORT_VN" in out


def test_scrub_keeps_non_pii_observability_fields() -> None:
    text = "req-7601dc00 user dde2e75b20cf latency 2653ms cost 0.001395 order 123456"
    assert scrub_text(text) == text
