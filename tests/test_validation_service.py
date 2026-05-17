from japan.services.validation_service import validate_row


def test_column_c_is_informational_only():
    status, remarks = validate_row(
        {
            "C": "Excel ingredient",
            "H": "BrandAlpha",
            "I": "Company A",
            "M": "10",
        },
        {
            "ingredient": "Completely different ingredient",
            "brand": "BrandAlpha",
            "company": "Company A",
            "price": "10",
        },
    )

    assert status == "Found"
    assert remarks == "All Match"


def test_h_i_m_still_drive_mismatches():
    status, remarks = validate_row(
        {
            "H": "BrandAlpha",
            "I": "Company A",
            "M": "10",
        },
        {
            "brand": "BrandBeta",
            "company": "Company B",
            "price": "12",
        },
    )

    assert status == "Found"
    assert "Column H mismatch" in remarks
    assert "Column I mismatch" in remarks
    assert "Column M mismatch" in remarks
    assert "Column C mismatch" not in remarks
