[14/03/26, 12:50:59 PM] arsh: ackathon Problem Statement: The "Intelli-Credit" Challenge
Theme: Next-Gen Corporate Credit Appraisal: Bridging the Intelligence Gap
Context
In the Indian corporate lending landscape, credit managers are overwhelmed by a "Data Paradox"—there is more information than ever, yet it takes weeks to process a single loan application. Assessing the creditworthiness of a mid-sized Indian corporate requires stitching together disparate data points:
•⁠  ⁠Structured Data: GST filings, ITRs, and Bank Statements.
•⁠  ⁠Unstructured Data: Annual Reports, Financial Statements, Board meeting minutes, Rating agency Reports, Shareholding pattern, etc
•⁠  ⁠External Intelligence: News reports on sector trends, MCA (Ministry of Corporate Affairs) filings, and legal disputes on the e-Courts portal.
•⁠  ⁠Primary Insights: Observations from factory site visits or management interviews (Due Diligence).
The current manual process is slow, prone to human bias, and often misses "early warning signals" buried in unstructured text.
Problem Statement
Develop an AI-powered Credit Decisioning Engine that automates the end-to-end preparation of a Comprehensive Credit Appraisal Memo (CAM). The solution must ingest multi-source data (Databricks), perform deep "web-scale" secondary research, and synthesize primary due diligence into a final recommendation (ML based) on whether to lend, what the limit should be, and at what risk premium.
Key Deliverables
Participants must build a prototype that handles the following three pillars:
1.⁠ ⁠The Data Ingestor (Multi-Format Support) - High latency pipelines
•⁠  ⁠Unstructured Parsing: Extract key financial commitments and risks from PDF annual reports, legal notices, and sanction letters from other banks.
•⁠  ⁠Structured Synthesis: Automatically cross-leverage GST returns against bank statements to identify "circular trading" or revenue inflation.
2.⁠ ⁠The Research Agent (The "Digital Credit Manager")
•⁠  ⁠Secondary Research: Automatically crawl the web for news related to the company’s promoters, sector-specific headwinds (e.g., "new RBI regulations on NBFCs"), and litigation history.
•⁠  ⁠Primary Insight Integration: Provide a portal for the user (Credit Officer) to input qualitative notes (e.g., "Factory found operating at 40% capacity"). The AI must adjust the final risk score based on these nuances.
3.⁠ ⁠The Recommendation Engine
•⁠  ⁠The CAM Generator: Produce a professional, structured Credit Appraisal Memo (Word/PDF) summarizing the Five Cs of Credit (Character, Capacity, Capital, Collateral, and Conditions).
•⁠  ⁠Decision Logic: Suggest a specific loan amount and interest rate using a transparent, explainable scoring model.
  > Note: The model must explain why it recommended a rejection or a specific limit (e.g., "Rejected due to high litigation risk found in secondary research despite strong GST flows").
  >
Evaluation Criteria
•⁠  ⁠Extraction Accuracy: How well does the tool extract data from messy, scanned Indian-context PDFs?
•⁠  ⁠Research Depth: Does the engine find relevant local news or regulatory filings that aren't in the provided files?
•⁠  ⁠Explainability: Can the AI "walk the judge through" its logic, or is it a black box?
•⁠  ⁠Indian Context Sensitivity: Does it understand India-specific nuances like GSTR-2A vs 3B or CIBIL Commercial reports?
[14/03/26, 12:50:59 PM] arsh: Hi Participants,

Thank you for registering! We are excited to see how you tackle one of the most significant challenges in the B2B FinTech space: The end-to-end automation of enterprise credit underwriting.

The Challenge

Your mission is to build a hosted web application (accessible without a VPN) that transforms raw, unstructured financial data into a comprehensive, AI-backed investment/assessment report.

The User Journey

Your solution must guide a Credit Analyst (User) through the following four stages:

1.⁠ ⁠Entity Onboarding

The Interface: A seamless onboarding page to capture basic entity details (CIN, PAN, Sector, Turnover, etc.) and specific Loan Details (Type, Amount, Tenure, Interest).
Note: This can be a multi-step form for better UX.
2.⁠ ⁠Intelligent Data Ingestion

The Task: A secure upload interface for 5 critical document types for the entity being analysed. (Sample documents will be shared with all participants)
ALM (Asset-Liability Management)
Shareholding Pattern
Borrowing Profile
Annual Reports (P&L, Cashflow, Balance Sheet)
Portfolio Cuts/Performance Data
3.⁠ ⁠Automated Extraction & Schema Mapping (The Core)

Classification: Automatically identify and categorize the uploaded files.
Human-in-the-loop: Allow users to approve, deny, or edit the auto-classification.
Dynamic Schema: Enable users to define or configure the output schema to ingest / structure data extracted from the raw files / documents.
Extraction: Ingest the data from the files into your defined schema with high precision, with user defined adjustments as needed.
4.⁠ ⁠Pre-Cognitive Secondary Analysis & Reporting

Secondary Research: Programmatically scrape alternate data (News, Legal, Market Sentiment, anything else) to provide a 360-degree view of the entity/sector/subsector/macro trends etc
Triangulate secondary research information with data extracted from above.
Explainable Prediction / Recommendation: Build a recommendation engine for loan approval with a clear "Reasoning Engine."
SWOT & GenAI: Generate a comprehensive SWOT analysis and a downloadable final investment report, presented in a easily explainable / consumable structure.
Success Criteria & Evaluation

We will judge the products based on the following:

Operational Excellence: Is the web app stable? Do uploads and forms work flawlessly?
Extraction Accuracy: How well does the parser handle complex, non-standard financial tables?
Analytical Depth: How thorough is the secondary research and the quality of the "Pre-Cognitive" risk signals?
User Experience: Is the journey from "Raw PDF/Excel/Image" + Secondary research to "Final Report" intuitive and fast?
What We Provide

To get you started, we will provide a curated unstructured dataset representing the 5 document types mentioned above (ALM, Shareholding Pattern, Borrowing Profile, Annual, Portfolio Cuts/Performance Data) to test your classification and parsing engines.