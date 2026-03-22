BANK_STATEMENT_DEFAULT_SCHEMA = {
    "category": "Bank_Statement",
    "fields": [
        {"key": "bank_name", "label": "Bank Name", "type": "text", "required": True},
        {"key": "account_holder_name", "label": "Account Holder Name", "type": "text", "required": True},
        {"key": "account_number", "label": "Account Number", "type": "text", "required": True},
        {"key": "period_from", "label": "Period From", "type": "date", "required": False},
        {"key": "period_to", "label": "Period To", "type": "date", "required": False},
        {"key": "opening_balance_crore", "label": "Opening Balance (Cr)", "type": "currency_crore", "required": False},
        {"key": "closing_balance_crore", "label": "Closing Balance (Cr)", "type": "currency_crore", "required": True},
        {"key": "total_credits_crore", "label": "Total Credits (Cr)", "type": "currency_crore", "required": True},
        {"key": "total_debits_crore", "label": "Total Debits (Cr)", "type": "currency_crore", "required": True},
        {
            "key": "average_monthly_balance_crore",
            "label": "Average Monthly Balance (Cr)",
            "type": "currency_crore",
            "required": False,
        },
    ],
}
