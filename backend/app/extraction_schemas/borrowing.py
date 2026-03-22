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
        {"key": "key_rating_strengths", "label": "Key Rating Strengths", "type": "text"},
        {"key": "key_rating_concerns", "label": "Key Rating Concerns", "type": "text"},
        {"key": "total_outstanding_debt_crore", "label": "Total Outstanding Debt (Cr)", "type": "currency_crore"},
        {"key": "number_of_lenders", "label": "Number of Lenders", "type": "number"},
        {
            "key": "average_cost_of_borrowing_percent",
            "label": "Average Cost of Borrowing %",
            "type": "percentage",
        },
        {"key": "nearest_repayment_date", "label": "Nearest Repayment Date", "type": "date"},
    ],
}

