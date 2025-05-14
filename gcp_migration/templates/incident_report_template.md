# MCP Server Incident Report

Generated: {timestamp}

## Service Status

* **Service Name**: {service_name}
* **Status**: {service_status}
* **Port**: {port} ({port_status})
{port_details}

## Issues Summary

* **Log Errors**: {log_error_count} errors found
* **Configuration Issues**: {config_issue_count} issues found
* **Data Directory Issues**: {data_issue_count} issues found
* **Network Status**: {network_status}

## Detailed Findings

### Log Errors

{{#if log_errors}}
Found {log_error_count} errors in logs:

{{#each log_errors}}
1. **{file}** (Line {line})
   * Time: {timestamp}
   * Message: `{message}`
{{/each}}
{{else}}
No errors found in logs.
{{/if}}

### Configuration Issues

{{#if config_issues}}
Found {config_issue_count} configuration issues:

{{#each config_issues}}
1. **{file}**
   * Issue: {issue}
   * Severity: {severity}
   {{#if line}}* Line: {line}{{/if}}
{{/each}}
{{else}}
No configuration issues found.
{{/if}}

### Data Directory Issues

{{#if data_issues}}
Found {data_issue_count} data directory issues:

{{#each data_issues}}
1. **{directory}**
   * Issue: {issue}
   * Severity: {severity}
{{/each}}
{{else}}
No data directory issues found.
{{/if}}

### Network Connectivity

* **Local Port**: {local_port_status}
* **Loopback Interface**: {loopback_status}
* **External Services**: {external_services_status}

## Service Details

```
{service_details}
```

## Recommendations

{{#if !service_running}}
1. Start the MCP server service:
   ```
   sudo systemctl start {service_name}
   ```
{{/if}}

{{#if !port_available}}
2. Resolve port conflict:
   ```
   sudo lsof -i :{port}
   # Identify and stop the process using the port
   ```
{{/if}}

{{#if config_issues}}
3. Fix configuration issues:
   ```
   # Edit configuration files in {config_dir}
   ```
{{/if}}

## Incident Resolution Steps

1. Identify the root cause: _________________________________
2. Applied fix: ___________________________________________
3. Verification steps: _____________________________________
4. Prevention measures: ____________________________________

## Sign-off

- [ ] Issue resolved
- [ ] Documentation updated
- [ ] Monitoring configured

Resolved by: ________________________
Date: _______________________________