# Orchestra AI Memory System - Infrastructure Deployment Guide

## Overview

This guide covers the deployment of the Orchestra AI Memory System infrastructure on Vultr using Pulumi. The infrastructure includes:

- PostgreSQL database (optimized for memory storage)
- Redis cache (L2 shared memory tier)
- Application servers (auto-scaling)
- Load balancer
- Monitoring stack (Prometheus + Grafana)
- VPC networking with security groups

## Prerequisites

1. **Vultr Account**
   - Active Vultr account with API access
   - API key configured
   - SSH key uploaded to Vultr

2. **Pulumi Setup**
   ```bash
   # Install Pulumi
   curl -fsSL https://get.pulumi.com | sh
   
   # Login to Pulumi (use backend of choice)
   pulumi login
   ```

3. **Python Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Configuration

### 1. Set Vultr API Key

```bash
export VULTR_API_KEY="your-vultr-api-key"
```

### 2. Configure Pulumi Stack

```bash
cd infrastructure/pulumi/memory_system

# Create a new stack
pulumi stack init production

# Set configuration values
pulumi config set ssh_key_id "your-vultr-ssh-key-id" --secret
pulumi config set postgres_password "secure-password" --secret
pulumi config set redis_password "secure-password" --secret
pulumi config set grafana_password "secure-password" --secret
```

### 3. Optional Configuration

```bash
# Change region (default: ewr - New Jersey)
pulumi config set region "lax"  # Los Angeles

# Change instance sizes
pulumi config set postgres_plan "vc2-8c-16gb"  # Larger PostgreSQL
pulumi config set redis_plan "vc2-4c-8gb"      # Larger Redis

# Scaling configuration
pulumi config set min_app_instances 3
pulumi config set max_app_instances 20
```

## Deployment

### 1. Preview Changes

```bash
pulumi preview
```

### 2. Deploy Infrastructure

```bash
pulumi up
```

This will:
- Create VPC network
- Set up firewall rules
- Deploy PostgreSQL instance
- Deploy Redis instance
- Deploy application servers
- Configure load balancer
- Set up monitoring server

### 3. Get Outputs

```bash
# Get all outputs
pulumi stack output

# Get specific outputs
pulumi stack output postgres_ip
pulumi stack output redis_ip
pulumi stack output load_balancer_ip
pulumi stack output monitoring_url
```

## Post-Deployment Setup

### 1. Configure DNS

Point your domain to the load balancer IP:

```bash
LB_IP=$(pulumi stack output load_balancer_ip)
echo "Create A record: @ -> $LB_IP"
echo "Create A record: www -> $LB_IP"
```

### 2. Access Monitoring

```bash
MONITORING_URL=$(pulumi stack output monitoring_url)
echo "Grafana URL: $MONITORING_URL"
echo "Default login: admin / $(pulumi config get grafana_password)"
```

### 3. Configure Application

SSH into app servers and update configuration:

```bash
# Get app server IPs
pulumi stack output app_server_ips

# SSH to each server
ssh root@<app-server-ip>

# Update environment variables
vim /home/orchestra/app/.env
```

### 4. Set Up SSL (Let's Encrypt)

On the load balancer or app servers:

```bash
# Install certbot
apt-get update
apt-get install -y certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Monitoring and Maintenance

### 1. Access Grafana Dashboards

1. Navigate to monitoring URL
2. Login with admin credentials
3. Import dashboards:
   - Node Exporter Full (ID: 1860)
   - PostgreSQL Database (ID: 9628)
   - Redis Dashboard (ID: 763)

### 2. Set Up Alerts

Create alert rules in Grafana for:
- High CPU usage (>80%)
- High memory usage (>90%)
- Database connection issues
- Redis memory full
- Application errors

### 3. Backup Configuration

Backups are automatically enabled. To restore:

```bash
# List backups
vultr-cli backups list

# Restore from backup
vultr-cli instance restore <instance-id> --backup <backup-id>
```

## Scaling

### 1. Manual Scaling

```bash
# Update app instance count
pulumi config set app_instance_count 5
pulumi up
```

### 2. Auto-Scaling Setup

The infrastructure supports auto-scaling. Configure based on metrics:

```python
# In __main__.py, add auto-scaling rules
auto_scaling_group = vultr.AutoScalingGroup(
    "app-asg",
    min_instances=2,
    max_instances=10,
    target_cpu_utilization=70,
    scale_up_cooldown=300,
    scale_down_cooldown=600,
)
```

## Troubleshooting

### 1. Check Instance Status

```bash
# Via Pulumi
pulumi stack output

# Via Vultr CLI
vultr-cli instance list
```

### 2. View Logs

```bash
# Application logs
ssh root@<app-server-ip>
tail -f /var/log/orchestra/app.log

# PostgreSQL logs
ssh root@<postgres-ip>
tail -f /var/log/postgresql/postgresql-*.log

# Redis logs
ssh root@<redis-ip>
tail -f /var/log/redis/redis-server.log
```

### 3. Common Issues

**Issue: Cannot connect to database**
- Check VPC connectivity
- Verify firewall rules
- Check PostgreSQL pg_hba.conf

**Issue: High latency**
- Check instance locations
- Verify load balancer configuration
- Monitor network metrics

**Issue: Out of memory**
- Scale up instance types
- Configure Redis eviction policies
- Add more app instances

## Cost Optimization

### 1. Instance Right-Sizing

Monitor actual usage and adjust:

```bash
# Check current usage
vultr-cli instance metrics <instance-id>

# Resize if needed
pulumi config set postgres_plan "vc2-2c-4gb"  # Smaller instance
pulumi up
```

### 2. Reserved Instances

For production workloads, consider reserved instances for cost savings.

### 3. Snapshot Management

```bash
# Create snapshot schedule
vultr-cli snapshot schedule create \
  --instance <instance-id> \
  --hour 2 \
  --dow 0  # Sunday
```

## Disaster Recovery

### 1. Backup Strategy

- Automated daily backups (enabled by default)
- PostgreSQL WAL archiving
- Redis AOF persistence
- Application code in Git

### 2. Recovery Procedures

**Database Recovery:**
```bash
# Restore PostgreSQL
pg_restore -h <postgres-ip> -U orchestra_user -d orchestra_memory backup.dump
```

**Redis Recovery:**
```bash
# Restore Redis from AOF
redis-cli --rdb /var/lib/redis/dump.rdb
```

### 3. Failover Testing

Regularly test failover procedures:

1. Simulate instance failure
2. Verify automatic recovery
3. Test backup restoration
4. Document recovery time

## Security Best Practices

1. **Network Security**
   - Use VPC for internal communication
   - Restrict SSH access to specific IPs
   - Enable DDoS protection

2. **Access Control**
   - Use SSH keys (no passwords)
   - Implement least privilege
   - Regular security updates

3. **Data Protection**
   - Encrypt data at rest
   - Use SSL/TLS for all connections
   - Regular security audits

## Maintenance Schedule

- **Daily**: Check monitoring dashboards
- **Weekly**: Review logs and metrics
- **Monthly**: Security updates, performance tuning
- **Quarterly**: Disaster recovery testing

## Support

For infrastructure issues:
1. Check Vultr status page
2. Review Pulumi logs: `pulumi logs`
3. Contact Vultr support for instance issues

For application issues:
1. Check application logs
2. Review monitoring metrics
3. Consult runbooks in `/docs/runbooks/`