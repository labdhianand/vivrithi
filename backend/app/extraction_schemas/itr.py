ITR_DEFAULT_SCHEMA = {
    "category": "ITR",
    "fields": [
        {"key": "pan", "label": "PAN", "type": "text", "required": True},
        {"key": "assessment_year", "label": "Assessment Year", "type": "text", "required": True},
        {"key": "gross_total_income_crore", "label": "Gross Total Income (Cr)", "type": "currency_crore", "required": True},
        {"key": "total_deductions_crore", "label": "Total Deductions (Cr)", "type": "currency_crore", "required": False},
        {"key": "taxable_income_crore", "label": "Taxable Income (Cr)", "type": "currency_crore", "required": True},
        {"key": "tax_payable", "label": "Tax Payable", "type": "number", "required": False},
        {"key": "tax_paid", "label": "Tax Paid", "type": "number", "required": False},
        {"key": "refund_due", "label": "Refund Due", "type": "number", "required": False},
        {"key": "filing_date", "label": "Filing Date", "type": "date", "required": False},
    ],
}
