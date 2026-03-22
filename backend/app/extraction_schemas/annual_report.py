ANNUAL_REPORT_DEFAULT_SCHEMA = {
    "category": "Annual_Report",
    "fields": [
        {"key": "revenue_fy24_crore", "label": "Revenue FY24 (Cr)", "type": "currency_crore", "required": True},
        {"key": "revenue_fy23_crore", "label": "Revenue FY23 (Cr)", "type": "currency_crore", "required": False},
        {"key": "net_profit_fy24_crore", "label": "Net Profit FY24 (Cr)", "type": "currency_crore", "required": True},
        {"key": "ebitda_fy24_crore", "label": "EBITDA FY24 (Cr)", "type": "currency_crore", "required": False},
        {"key": "total_debt_crore", "label": "Total Debt (Cr)", "type": "currency_crore", "required": False},
        {"key": "net_worth_crore", "label": "Net Worth (Cr)", "type": "currency_crore", "required": True},
        {"key": "debt_equity_ratio", "label": "Debt/Equity Ratio", "type": "number", "required": False},
        {"key": "interest_coverage_ratio", "label": "Interest Coverage Ratio", "type": "number", "required": False},
        {"key": "auditor_name", "label": "Auditor Name", "type": "text", "required": True},
        {"key": "auditor_opinion", "label": "Auditor Opinion", "type": "text", "required": False},
        {"key": "going_concern_flag", "label": "Going Concern Flag", "type": "text", "required": False},
        {"key": "roe_percent", "label": "Return on Equity (%)", "type": "percentage", "required": False},
        {"key": "roa_percent", "label": "Return on Assets (%)", "type": "percentage", "required": False},
        {"key": "nim_percent", "label": "Net Interest Margin (%)", "type": "percentage", "required": False},
        {"key": "branch_count", "label": "Number of Branches", "type": "number", "required": False},
        {"key": "employee_count", "label": "Number of Employees", "type": "number", "required": False},
    ],
}

