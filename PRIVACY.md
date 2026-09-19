Privacy & data handling guidance

- Store only minimal PII: `student_id`, name (optional). Avoid storing full IDs in exports.
- Exports are stored in `/exports`. Implement lifecycle cleanup in production.
- Use encryption at rest and TLS in transit.
- Provide consent mechanism for storing student submissions.
- Audit logs must not contain sensitive PII.

