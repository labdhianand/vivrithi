BORROWING_DEFAULT_SCHEMA = {
    "category": "Borrowing_Profile",
    "fields": [
        {"key": "rating_agency", "label": "Rating Agency", "type": "text", "required": True},
        {"key": "rating_date", "label": "Rating Date", "type": "date"},
        {"key": "long_term_rating", "label": "Long-Term Rating", "type": "text", "required": True},
        {"key": "long_term_outlook", "label": "Outlook", "type": "text", "required": True},
        {"key": "rating_action", "label": "Rating Action", "type": "text", "required": True},
        {"key": "short_term_rating", "label": "Short-Term Rating", "type": "text"},
        {
            "key": "total_rated_facilities_crore",
            "label": "Total Rated Facilities (Rs. crore)",
            "type": "currency_crore",
            "required": True,
        },
        {"key": "term_loan_total_crore", "label": "Term Loan Total (Rs. crore)", "type": "currency_crore"},
        {"key": "ncd_total_crore", "label": "NCD Total (Rs. crore)", "type": "currency_crore"},
        {"key": "cp_total_crore", "label": "Commercial Paper Total (Rs. crore)", "type": "currency_crore"},
        {"key": "fund_based_limits_crore", "label": "Fund-Based Limits (Rs. crore)", "type": "currency_crore"},
        {
            "key": "lender_wise_breakdown",
            "label": "Lender-Wise Breakdown",
            "type": "json",
            "description": "Array of {lender_name, facility_type, amount_crore}",
        },
        {
            "key": "ncd_instruments",
            "label": "NCD Instrument Details",
            "type": "json",
            "description": "Array of {isin, coupon_rate, maturity_date, amount_crore}",
        },
        {"key": "key_rating_strengths", "label": "Key Rating Strengths", "type": "text"},
        {"key": "key_rating_concerns", "label": "Key Rating Concerns", "type": "text"},
    ],
}

