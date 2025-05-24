# Security Check Guide

This guide explains how to use the `security_check.sh` script to verify the security of your Python dependencies.

## What This Script Does

The `security_check.sh` script helps identify and address potential security vulnerabilities in your Python dependencies by:

1. Ensuring you have the latest version of `pip`
2. Using the recommended `safety scan` command (replacing the deprecated `check` command)
3. Creating a custom security policy that checks for vulnerabilities in unpinned dependencies
4. Scanning your requirements files for potential security issues
5. Providing recommendations for securing your dependencies

## How to Use

After setting up your development container and installing dependencies, run:

```bash
./security_check.sh
```

### Expected Output

The script will show:

1. Your current pip version and upgrade it if needed
2. Create a `.safety-policy.yml` file if one doesn't exist
3. Run a security scan on your requirements files
4. Provide security recommendations

## Addressing Unpinned Dependencies

One key issue identified in your project is the use of unpinned dependencies. For example:

```
# Unpinned (potentially insecure for production apps)
fastapi>=0.103.1
aiohttp>=3.8.5

# Pinned (recommended for production)
fastapi==0.103.1
aiohttp==3.8.5
```

### Why Pinning Matters

- **Prevents "surprise" updates**: Ensures you're using the exact versions you've tested
- **Improves reproducibility**: Everyone gets the same environment
- **Security control**: Prevents automatic upgrades to versions with unknown vulnerabilities
- **Dependency resolution**: Avoids conflicts between dependencies with competing requirements

## The Safety Policy File

The script creates a `.safety-policy.yml` file that sets:

```yaml
security:
  ignore-unpinned-requirements: false # Report vulnerabilities in unpinned packages
  ignore-vulnerabilities:
    # Add specific vulnerabilities to ignore here if needed
```

This ensures that vulnerabilities in unpinned packages are reported (they're ignored by default).

## Integration with Development Workflow

For the best results:

1. Run `./verify_container.sh` first to ensure your environment is set up correctly
2. Then run `./security_check.sh` to verify your dependencies are secure
3. Address any security issues identified before deploying to production
4. Consider adding these checks to your CI/CD pipeline

## Troubleshooting

If you encounter issues:

1. Make sure you have the `safety` package installed: `pip install safety`
2. Check that your requirements files are using the correct format
3. For complex projects using Poetry, you may need to generate a requirements file:
   ```bash
   poetry export -f requirements.txt --output requirements.txt
   ```

## Additional Resources

- [Safety Documentation](https://docs.pyup.io/docs/getting-started-with-safety)
- [Python Dependency Management Best Practices](https://pip.pypa.io/en/stable/topics/repeatable-installs/)
- [OWASP Top Ten for Python](https://owasp.org/www-project-top-ten/)
