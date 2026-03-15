ITR_DEFAULT_SCHEMA = {
    "category": "ITR",
    "fields": [
        {"key": "pan", "label": "PAN", "type": "string", "required": True},
        {"key": "assessment_year", "label": "Assessment Year", "type": "string", "required": True},
        {"key": "financial_year", "label": "Financial Year", "type": "string", "required": True},
        {"key": "return_type", "label": "Return Type", "type": "string", "required": False},
        {"key": "gross_total_income", "label": "Gross Total Income", "type": "currency_crore", "required": True},
        {"key": "total_income", "label": "Total Income", "type": "currency_crore", "required": True},
        {"key": "tax_payable", "label": "Tax Payable", "type": "currency_lakhs", "required": False},
        {"key": "tax_paid", "label": "Tax Paid", "type": "currency_lakhs", "required": False},
        {"key": "refund_claimed", "label": "Refund Claimed", "type": "currency_lakhs", "required": False},
        {"key": "filing_date", "label": "Filing Date", "type": "date", "required": False},
        {"key": "auditor_name", "label": "Auditor Name", "type": "string", "required": False},
    ],
}
