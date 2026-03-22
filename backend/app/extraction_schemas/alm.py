ALM_DEFAULT_SCHEMA = {
    "category": "ALM",
    "fields": [
        {"key": "reporting_date", "label": "Reporting Date", "type": "date", "required": True},
        {
            "key": "hqla_total_unweighted",
            "label": "HQLA Total (Unweighted)",
            "type": "number",
            "required": True,
        },
        {
            "key": "hqla_total_weighted",
            "label": "HQLA Total (Weighted)",
            "type": "number",
            "required": True,
        },
        {
            "key": "total_cash_outflows_unweighted",
            "label": "Total Cash Outflows (Unweighted)",
            "type": "number",
            "required": True,
        },
        {
            "key": "total_cash_outflows_weighted",
            "label": "Total Cash Outflows (Weighted)",
            "type": "number",
            "required": True,
        },
        {
            "key": "total_cash_inflows_unweighted",
            "label": "Total Cash Inflows (Unweighted)",
            "type": "number",
            "required": True,
        },
        {
            "key": "total_cash_inflows_weighted",
            "label": "Total Cash Inflows (Weighted)",
            "type": "number",
            "required": True,
        },
        {"key": "total_net_cash_outflows", "label": "Total Net Cash Outflows", "type": "number", "required": True},
        {"key": "lcr_ratio", "label": "Liquidity Coverage Ratio (%)", "type": "percentage", "required": True},
        {"key": "net_stable_funding_ratio", "label": "Net Stable Funding Ratio", "type": "number", "required": False},
        {"key": "total_assets_crore", "label": "Total Assets (Cr)", "type": "currency_crore", "required": False},
        {"key": "total_liabilities_crore", "label": "Total Liabilities (Cr)", "type": "currency_crore", "required": False},
        {
            "key": "zero_to_one_year_asset_bucket_crore",
            "label": "0-1yr Asset Bucket (Cr)",
            "type": "currency_crore",
            "required": False,
        },
        {
            "key": "zero_to_one_year_liability_bucket_crore",
            "label": "0-1yr Liability Bucket (Cr)",
            "type": "currency_crore",
            "required": False,
        },
        {"key": "one_to_three_year_gap_crore", "label": "1-3yr Gap (Cr)", "type": "currency_crore", "required": False},
        {"key": "three_to_five_year_gap_crore", "label": "3-5yr Gap (Cr)", "type": "currency_crore", "required": False},
    ],
}

