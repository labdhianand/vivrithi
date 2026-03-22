FINANCIALS_DEFAULT_SCHEMA = {
    "category": "Portfolio_Performance",
    "fields": [
        {"key": "reporting_period", "label": "Reporting Period", "type": "text", "required": True},
        {"key": "interest_income", "label": "Interest Income", "type": "number", "required": True},
        {"key": "finance_costs", "label": "Finance Costs", "type": "number", "required": False},
        {"key": "profit_before_tax", "label": "Profit Before Tax", "type": "number", "required": True},
        {"key": "profit_after_tax", "label": "Profit After Tax", "type": "number", "required": True},
        {"key": "gnpa_percent", "label": "Gross NPA (%)", "type": "percentage", "required": False},
        {"key": "nnpa_percent", "label": "Net NPA (%)", "type": "percentage", "required": False},
        {"key": "provision_coverage_ratio", "label": "Provision Coverage Ratio (%)", "type": "percentage", "required": False},
        {"key": "crar_percent", "label": "Capital Risk Adequacy Ratio (%)", "type": "percentage", "required": False},
        {"key": "lcr_percent", "label": "Liquidity Coverage Ratio (%)", "type": "percentage", "required": False},
        {"key": "aum_crore", "label": "Total AUM (Cr)", "type": "currency_crore", "required": False},
        {"key": "collection_efficiency_percent", "label": "Collection Efficiency %", "type": "percentage", "required": False},
        {"key": "cost_of_funds_percent", "label": "Cost of Funds %", "type": "percentage", "required": False},
        {"key": "yield_on_advances_percent", "label": "Yield on Advances %", "type": "percentage", "required": False},
        {"key": "aum_growth_yoy_percent", "label": "AUM Growth YoY %", "type": "percentage", "required": False},
    ],
}

