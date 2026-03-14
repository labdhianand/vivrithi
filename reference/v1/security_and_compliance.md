# Security and Compliance Notes

## Current baseline controls

- Secrets via `.env`, not committed
- Audit log for workflow steps and overrides
- Deterministic evidence and citation fields per claim

## Required upgrades before regulated production

- SSO + RBAC with least privilege
- Encryption at rest for DB and document storage
- DLP scanning and PII tokenization
- Signed immutable audit trails
- Tamper-evident export signatures
- Full legal review for bureau data handling and data residency

## India-specific governance references

- Maintain explicit handling controls for GST, banking statements, and bureau report access
- Ensure all data processing aligns with contractual and regulatory obligations
