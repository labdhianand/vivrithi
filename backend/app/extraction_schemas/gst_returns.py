GST_RETURNS_DEFAULT_SCHEMA = {
    "category": "GST_Returns",
    "fields": [
        {"key": "gstin", "label": "GSTIN", "type": "text", "required": True},
        {"key": "filing_period", "label": "Filing Period", "type": "text", "required": True},
        {"key": "gross_turnover", "label": "Gross Turnover", "type": "number", "required": True},
        {"key": "taxable_turnover", "label": "Taxable Turnover", "type": "number", "required": True},
        {"key": "cgst", "label": "CGST", "type": "number", "required": False},
        {"key": "sgst", "label": "SGST", "type": "number", "required": False},
        {"key": "igst", "label": "IGST", "type": "number", "required": False},
        {"key": "input_tax_credit_claimed", "label": "Input Tax Credit Claimed", "type": "number", "required": False},
        {"key": "net_tax_payable", "label": "Net Tax Payable", "type": "number", "required": False},
    ],
}
