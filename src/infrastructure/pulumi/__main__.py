import pulumi
config = pulumi.Config()
LAMBDA_LABS_API_KEY = config.require_secret("LAMBDA_LABS_API_KEY")
LAMBDA_SSH_KEY = config.require_secret("LAMBDA_SSH_KEY") 