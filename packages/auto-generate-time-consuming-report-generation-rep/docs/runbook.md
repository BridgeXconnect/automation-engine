# Runbook: Auto-Generate Time-consuming report generation Reports

## Quick Reference

- **Workflow Name**: auto_generate_time_consuming_report_generation_reports_automation
- **Risk Level**: 44.0%
- **Dependencies**: Executive stakeholder approval needed, Migration from existing tools
- **On-Call Contact**: [Your team contact]

## Monitoring

### Health Checks

1. **Workflow Status**
   ```bash
   # Check if workflow is active
   curl -X GET "https://your-n8n-instance/api/v1/workflows/auto_generate_time_consuming_report_generation_reports_automation"
   ```

2. **Recent Executions**
   - Monitor execution history in n8n dashboard
   - Check for failed executions
   - Validate data quality

### Key Metrics to Monitor

- Execution success rate (target: >99%)
- Average execution time (target: <72s)
- Error rate (target: <1%)
- Data accuracy (target: 100%)

## Troubleshooting Procedures

### Common Issues

#### Issue: Workflow Not Triggering
**Symptoms**: No new executions, manual trigger works
**Investigation Steps**:
1. Check trigger configuration
2. Verify webhook URLs (if applicable)
3. Review trigger conditions
4. Check external system connectivity

**Resolution**:
1. Restart workflow
2. Update trigger settings
3. Verify integration credentials

#### Issue: Authentication Failures
**Symptoms**: 401/403 errors in execution logs
**Investigation Steps**:
1. Check credential expiration
2. Verify API permissions
3. Test manual API calls

**Resolution**:
1. Refresh API tokens
2. Update credentials in n8n
3. Verify permission scopes

#### Issue: Data Processing Errors
**Symptoms**: Execution fails at data transformation nodes
**Investigation Steps**:
1. Review input data structure
2. Check data transformation logic
3. Validate field mappings

**Resolution**:
1. Update data mapping
2. Add data validation steps
3. Handle edge cases

### Emergency Procedures

#### Complete Workflow Failure
1. **Immediate Actions**:
   - Disable workflow to prevent further issues
   - Alert stakeholders
   - Switch to manual process if available

2. **Investigation**:
   - Review recent changes
   - Check system dependencies
   - Analyze error logs

3. **Recovery**:
   - Roll back recent changes
   - Test workflow with sample data
   - Gradual re-enablement

## Maintenance

### Daily Tasks
- [ ] Review execution logs
- [ ] Check success/failure rates
- [ ] Monitor system performance

### Weekly Tasks
- [ ] Update credentials if needed
- [ ] Review and clean up old executions
- [ ] Analyze performance trends

### Monthly Tasks
- [ ] Full system health check
- [ ] Review and update documentation
- [ ] Capacity planning review

## Rollback Procedures

### Workflow Rollback
1. Export current workflow configuration
2. Import previous stable version
3. Update configuration as needed
4. Test with sample data
5. Enable and monitor

### Data Recovery
1. Identify affected records
2. Use backup data sources
3. Manual correction if needed
4. Validate data integrity

## Contact Information

- **Primary On-Call**: [Name, Contact]
- **Secondary Support**: [Team Contact]
- **Escalation**: [Manager Contact]

---
*Generated on 2025-08-12 15:43:22*
