# DigitalOcean Admin UI Site Deployment

This template helps you get started with Pulumi and the `pulumi-digitalocean` provider to deploy a static site to DigitalOcean App Platform.

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
- [DigitalOcean CLI](https://docs.digitalocean.com/reference/doctl/how-to/install/)
- DigitalOcean account with API access

## Getting Started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure DigitalOcean credentials:

```bash
doctl auth init
pulumi config set digitalocean:token --secret YOUR_API_TOKEN
```

3. Deploy:

```bash
pulumi up
```

## Configuration

### Required Settings

- **digitalocean:token**: (Required) The DigitalOcean API token
- **admin-ui-site:domainName**: The custom domain for your site (optional)

### Optional Settings

- **region**: DigitalOcean region (default: nyc3)
- **appSize**: App Platform size (default: basic-xxs)

## Architecture

- **DigitalOcean App Platform**: Hosts the static site
- **DigitalOcean CDN**: Provides global content delivery
- **DigitalOcean Spaces**: Optional asset storage

## Maintenance

- Update dependencies: `pip install -U -r requirements.txt`
- View logs: `doctl apps logs --tail 100`
- Monitor: `doctl apps list`

## Resources

- Pulumi Docs: https://www.pulumi.com/docs/
- DigitalOcean Provider Docs: https://www.pulumi.com/registry/packages/digitalocean/
- Community Slack: https://slack.pulumi.com/
