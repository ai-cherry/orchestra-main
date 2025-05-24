# Project Orchestra: Roo Code Best Practices

This guide outlines best practices for using the Roo Code AI-assisted development setup in Project Orchestra. Following these guidelines will help ensure security, maintainability, and effective collaboration.

## Workflow Best Practices

### Human Oversight & Verification

- Always review AI-generated outputs, especially architecture decisions, security-related code, and infrastructure definitions
- Conduct code reviews on AI-generated PRs
- Run additional static analysis or security scans in CI
- Verify critical code or infrastructure changes before deploying to production

### Incremental Development

- Encourage the AI to work in small, testable chunks
- Run tests frequently to validate AI-generated code
- Commit code at logical milestones for easier tracking and rollback
- Use feature branches for isolation of AI-generated changes

### Prompt Engineering

- Be specific and detailed in your prompts
- Provide context and constraints
- Reference existing patterns in the codebase
- For complex tasks, start with architecture planning in Architect mode

## Security Considerations

### Secrets Management

- Never hardcode secrets in AI-generated code
- Use environment variables or secret managers
- Configure the `.roomodes` to restrict which modes can edit files
- Teach the AI to use GitHub secrets and GCP Secret Manager

### AI Tool Permissions

- Regularly audit mode permissions in `.roomodes`
- Restrict file editing to only the necessary modes
- Use file pattern restrictions to limit what Creative mode can edit
- Be cautious when giving command execution permissions

### GCP Integration

- Use service accounts with minimal permissions (principle of least privilege)
- Rotate GCP_MASTER_SERVICE_JSON periodically
- Use different service accounts for different environments
- Audit cloud resources regularly

## Effective Mode Usage

### Architect Mode

- Use for high-level design and planning
- Ask for diagrams and component breakdowns
- Request specific justification for technological choices
- Good first step for any new feature

### Code Mode

- Provide clear requirements derived from Architect mode
- Reference existing patterns in the codebase
- Ask for tests alongside implementation
- Review code before applying changes

### Reviewer Mode

- Have it check for security vulnerabilities
- Use for style consistency checks
- Ask for performance improvement suggestions
- Run after Code mode completes its task

### Ask Mode

- Use for research on APIs, libraries, or GCP services
- Retrieve documentation for unfamiliar tools
- Clarify error messages or unexpected behavior
- Gather information before making decisions

### Strategy Mode

- Use to compare different approaches
- Ask for pros/cons analysis
- Get help breaking down complex workflows
- Plan resource allocation and scaling strategies

### Creative Mode

- Generate comprehensive documentation
- Create onboarding guides for new team members
- Draft user guides and API documentation
- Write release notes and changelogs

### Debug Mode

- Use when tests fail or errors occur
- Provide full error logs and context
- Let it suggest and implement fixes
- Verify fixes with tests

## Memory and Context Management

### Effective Use of MCP Memory

- Store architecture diagrams and decisions
- Keep track of implementation progress
- Save common patterns for reuse
- Document key design decisions

### Context Preservation

- Use memory to maintain context between sessions
- Summarize previous steps when starting new tasks
- Reference stored information in new prompts
- Use the orchestrator for complex multi-step workflows

## CI/CD Integration

### GitHub Actions

- Use the provided workflow for deployment
- Add custom steps for specific project needs
- Set up environment-specific validations
- Configure notifications for workflow results

### Deployment Safety

- Deploy to development environment first
- Use Terraform workspaces for environment isolation
- Implement drift detection
- Have rollback procedures in place

## Cost Management

### API Usage Optimization

- Use cheaper models for simpler tasks
- Reserve top-tier models for complex design work
- Monitor token usage through Portkey
- Cache common responses in memory

### Efficient Workflows

- Structure prompts to minimize token usage
- Reuse previous results via memory
- Break complex tasks into smaller, focused subtasks
- Use the orchestrator to optimize workflows

## Collaboration Guidelines

### Knowledge Sharing

- Document AI-generated architecture decisions
- Share effective prompts with the team
- Update prompts based on feedback
- Train new team members on effective AI collaboration

### Version Control

- Commit `.roomodes` and MCP configurations to the repository
- Document changes to mode configurations
- Version control prompt templates
- Track model performance for different tasks

## Continuous Improvement

### Feedback Loop

- Regularly evaluate AI output quality
- Refine mode configurations based on performance
- Update system prompts with new learnings
- Implement best of breed patterns discovered by the AI

### Staying Current

- Monitor for new model releases
- Update model configurations in portkey-router.js
- Test new models on benchmark tasks
- Share insights on model strengths and weaknesses

By following these best practices, your team can effectively leverage Roo Code's AI capabilities while maintaining security, quality, and efficiency in your development process.
