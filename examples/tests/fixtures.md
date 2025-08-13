# Test Fixtures for Automation Validation

## Example: Lead Intake → Enrichment → CRM → Slack

### Input Fixture (JSON)
```json
{
  "email": "sample@example.com",
  "name": "Test User",
  "company": "Sample Logistics Co"
}
```

### Expected Output Fixture
```json
{
  "crm_record_id": "12345ABC",
  "enrichment_status": "success",
  "slack_message_sent": true
}
```

## Assertions
- CRM record exists and matches input email.
- Enrichment returns industry and size.
- Slack message contains lead name and company.