ALM_DEFAULT_SCHEMA = {
    "category": "ALM",
    "fields": [
        {"key": "reporting_date", "label": "Reporting Date", "type": "date", "required": True},
        {
            "key": "hqla_total_unweighted",
            "label": "HQLA Total (Unweighted)",
            "type": "currency_lakhs",
            "required": True,
        },
        {
            "key": "hqla_total_weighted",
            "label": "HQLA Total (Weighted)",
            "type": "currency_lakhs",
            "required": True,
        },
        {"key": "cash_outflow_deposits", "label": "Cash Outflow - Deposits", "type": "currency_lakhs"},
        {
            "key": "cash_outflow_unsecured_wholesale",
            "label": "Cash Outflow - Unsecured Wholesale",
            "type": "currency_lakhs",
        },
        {
            "key": "cash_outflow_secured_wholesale",
            "label": "Cash Outflow - Secured Wholesale",
            "type": "currency_lakhs",
        },
        {
            "key": "cash_outflow_credit_facilities",
            "label": "Cash Outflow - Credit & Liquidity Facilities",
            "type": "currency_lakhs",
        },
        {
            "key": "cash_outflow_other_contractual",
            "label": "Cash Outflow - Other Contractual",
            "type": "currency_lakhs",
        },
        {
            "key": "cash_outflow_other_contingent",
            "label": "Cash Outflow - Other Contingent",
            "type": "currency_lakhs",
        },
        {
            "key": "total_cash_outflows_unweighted",
            "label": "Total Cash Outflows (Unweighted)",
            "type": "currency_lakhs",
            "required": True,
        },
        {
            "key": "total_cash_outflows_weighted",
            "label": "Total Cash Outflows (Weighted)",
            "type": "currency_lakhs",
            "required": True,
        },
        {"key": "cash_inflow_secured_lending", "label": "Cash Inflow - Secured Lending", "type": "currency_lakhs"},
        {
            "key": "cash_inflow_performing_exposures",
            "label": "Cash Inflow - Performing Exposures",
            "type": "currency_lakhs",
        },
        {"key": "cash_inflow_other", "label": "Cash Inflow - Other", "type": "currency_lakhs"},
        {
            "key": "total_cash_inflows_unweighted",
            "label": "Total Cash Inflows (Unweighted)",
            "type": "currency_lakhs",
            "required": True,
        },
        {
            "key": "total_cash_inflows_weighted",
            "label": "Total Cash Inflows (Weighted)",
            "type": "currency_lakhs",
            "required": True,
        },
        {"key": "total_net_cash_outflows", "label": "Total Net Cash Outflows", "type": "currency_lakhs"},
        {"key": "lcr_ratio", "label": "Liquidity Coverage Ratio (%)", "type": "percentage", "required": True},
        {"key": "lcr_qualitative_notes", "label": "Qualitative Disclosure Notes", "type": "text"},
    ],
}

