SHAREHOLDING_DEFAULT_SCHEMA = {
    "category": "Shareholding_Pattern",
    "fields": [
        {"key": "reporting_quarter", "label": "Reporting Quarter", "type": "text", "required": True},
        {"key": "promoter_holding_percent", "label": "Promoter Holding %", "type": "percentage", "required": True},
        {"key": "promoter_pledge_percent", "label": "Promoter Pledge %", "type": "percentage", "required": False},
        {"key": "fii_holding_percent", "label": "FII Holding %", "type": "percentage", "required": False},
        {"key": "dii_holding_percent", "label": "DII Holding %", "type": "percentage", "required": False},
        {"key": "public_holding_percent", "label": "Public Holding %", "type": "percentage", "required": True},
        {"key": "total_shares", "label": "Total Shares", "type": "number", "required": True},
        {"key": "promoter_name", "label": "Key Promoter Name", "type": "text", "required": False},
        {"key": "shares_pledged_percent", "label": "Shares Pledged (% of promoter)", "type": "percentage"},
        {
            "key": "foreign_ownership_limit_utilized",
            "label": "Foreign Ownership Limit Utilized (%)",
            "type": "percentage",
            "required": False,
        },
        {
            "key": "change_in_promoter_holding_qoq",
            "label": "Change in Promoter Holding QoQ",
            "type": "percentage",
            "required": False,
        },
        {"key": "esops_outstanding", "label": "ESOPs Outstanding", "type": "number", "required": False},
    ],
}

