ITR_DEFAULT_SCHEMA = {
    "category": "ITR",
    "fields": [
        {"key": "pan", "label": "PAN", "type": "text", "required": True},
        {"key": "assessment_year", "label": "Assessment Year", "type": "text", "required": True},
        {"key": "gross_total_income", "label": "Gross Total Income", "type": "number", "required": True},
        {"key": "total_deductions", "label": "Total Deductions", "type": "number", "required": False},
        {"key": "taxable_income", "label": "Taxable Income", "type": "number", "required": True},
        {"key": "tax_payable", "label": "Tax Payable", "type": "number", "required": False},
        {"key": "tax_paid", "label": "Tax Paid", "type": "number", "required": False},
        {"key": "refund_due", "label": "Refund Due", "type": "number", "required": False},
        {"key": "filing_date", "label": "Filing Date", "type": "date", "required": False},
    ],
}
