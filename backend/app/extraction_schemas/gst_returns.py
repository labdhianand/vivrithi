GST_RETURNS_DEFAULT_SCHEMA = {
    "category": "GST_Returns",
    "fields": [
        {"key": "gstin", "label": "GSTIN", "type": "text", "required": True},
        {"key": "filing_period", "label": "Filing Period", "type": "text", "required": True},
        {"key": "gross_turnover_crore", "label": "Gross Turnover (Cr)", "type": "currency_crore", "required": True},
        {"key": "taxable_turnover_crore", "label": "Taxable Turnover (Cr)", "type": "currency_crore", "required": True},
        {"key": "cgst_paid", "label": "CGST Paid", "type": "number", "required": False},
        {"key": "sgst_paid", "label": "SGST Paid", "type": "number", "required": False},
        {"key": "igst_paid", "label": "IGST Paid", "type": "number", "required": False},
        {"key": "total_tax_paid", "label": "Total Tax Paid", "type": "number", "required": False},
        {"key": "input_tax_credit_claimed", "label": "Input Tax Credit Claimed", "type": "number", "required": False},
    ],
}
