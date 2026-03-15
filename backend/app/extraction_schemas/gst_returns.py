GST_RETURNS_DEFAULT_SCHEMA = {
    "category": "GST_Returns",
    "fields": [
        {"key": "gstin", "label": "GSTIN", "type": "string", "required": True},
        {"key": "filing_period", "label": "Filing Period", "type": "string", "required": True},
        {"key": "turnover_reported", "label": "Turnover Reported", "type": "currency_crore", "required": True},
        {"key": "tax_liability", "label": "Tax Liability", "type": "currency_lakhs", "required": False},
        {"key": "itc_claimed", "label": "Input Tax Credit Claimed", "type": "currency_lakhs", "required": False},
        {"key": "gst_status", "label": "GST Compliance Status", "type": "string", "required": True},
        {"key": "filing_date", "label": "Date of Filing", "type": "date", "required": False},
        {"key": "return_type", "label": "Return Type (GSTR-1/3B/2A)", "type": "string", "required": False},
    ],
}
