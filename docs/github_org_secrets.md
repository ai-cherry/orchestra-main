# GitHub Organization Secrets Configuration

## Required Secrets

### Pulumi Configuration
| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `PULUMI_CONFIGURE_PASSPHRASE` | Encryption passphrase for Pulumi state | `your-secure-passphrase` |
| `ORG_PULUMI_ACCESS_TOKEN` | Pulumi Cloud access token | `pul-1234567890abcdef` |

### Infrastructure Providers
| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `ORG_LAMBDA_API_KEY` | Lambda API key | `dop_v1_1234567890abcdef` |
| `ORG_MONGODB_ORG_ID` | MongoDB Atlas Organization ID | `1234567890abcdef12345678` |
| `ORG_MONGODB_API_PUBLIC_KEY` | MongoDB Atlas API Public Key | `abcdefgh-1234-5678-90ab-cdef12345678` |
| `ORG_MONGODB_API_PRIVATE_KEY` | MongoDB Atlas API Private Key | `12345678-90ab-cdef-1234-567890abcdef` |

### AI Service APIs
| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `ORG_OPENAI_API_KEY` | OpenAI API key | `sk-1234567890abcdef1234567890abcdef` |
| `ORG_ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-api03-1234567890abcdef-12345678` |
| `ORG_OPENROUTER_API_KEY` | OpenRouter API key | `sk-or-1234567890abcdef1234567890abcdef` |

## Setting Up Secrets

### Using GitHub CLI
```bash
gh secret set PULUMI_CONFIGURE_PASSPHRASE --body "your-passphrase" --org your-org
gh secret set ORG_LAMBDA_API_KEY --body "your-do-token" --org your-org
```

### Using the Provided Script
```bash
./infra/populate_pulumi_secrets.sh
```

## Secret Rotation Schedule
| Secret Type | Rotation Frequency | Notes |
|-------------|--------------------|-------|
| Pulumi Passphrase | 90 days | Must update all environments |
| API Tokens | 180 days | Rotate via provider dashboards |
| Database Credentials | 90 days | Coordinate with maintenance windows |

## Troubleshooting

### Common Issues
1. **Missing Secrets**: Verify all required secrets are set in GitHub org
2. **Permission Issues**: Ensure workflows have `secrets: read` permission
3. **Format Errors**: Check for trailing whitespace in secret values

## Security Best Practices
- Never commit secret values to version control
- Use minimal required permissions for each secret
- Audit secret access logs monthly
