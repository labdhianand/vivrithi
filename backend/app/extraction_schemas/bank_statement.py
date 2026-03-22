BANK_STATEMENT_DEFAULT_SCHEMA = {
    "category": "Bank_Statement",
    "fields": [
        {"key": "account_number", "label": "Account Number", "type": "text", "required": True},
        {"key": "bank_name", "label": "Bank Name", "type": "text", "required": True},
        {"key": "account_holder", "label": "Account Holder", "type": "text", "required": True},
        {"key": "period_from", "label": "Period From", "type": "date", "required": False},
        {"key": "period_to", "label": "Period To", "type": "date", "required": False},
        {"key": "opening_balance", "label": "Opening Balance", "type": "number", "required": False},
        {"key": "closing_balance", "label": "Closing Balance", "type": "number", "required": True},
        {"key": "total_credits", "label": "Total Credits", "type": "number", "required": True},
        {"key": "total_debits", "label": "Total Debits", "type": "number", "required": True},
        {"key": "average_monthly_balance", "label": "Average Monthly Balance", "type": "number", "required": False},
    ],
}
