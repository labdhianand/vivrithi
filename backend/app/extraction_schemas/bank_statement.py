BANK_STATEMENT_DEFAULT_SCHEMA = {
    "category": "Bank_Statement",
    "fields": [
        {"key": "account_number", "label": "Account Number", "type": "string", "required": True},
        {"key": "bank_name", "label": "Bank Name", "type": "string", "required": True},
        {"key": "period", "label": "Statement Period", "type": "string", "required": True},
        {"key": "total_credits", "label": "Total Credits", "type": "currency_lakhs", "required": True},
        {"key": "total_debits", "label": "Total Debits", "type": "currency_lakhs", "required": True},
        {"key": "closing_balance", "label": "Closing Balance", "type": "currency_lakhs", "required": True},
        {"key": "average_balance", "label": "Average Monthly Balance", "type": "currency_lakhs", "required": False},
        {"key": "opening_balance", "label": "Opening Balance", "type": "currency_lakhs", "required": False},
    ],
}
