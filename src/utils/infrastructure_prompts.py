"""
Infrastructure and Deployment Prompts for AI Agents
Specialized prompts for Lambda Labs, Pulumi, and Vercel operations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

class InfrastructurePrompts:
    """AI prompts for infrastructure operations"""
    
    @staticmethod
    def lambda_labs_deployment(gpu_type: str = "A100") -> Dict[str, Any]:
        """Generate prompts for Lambda Labs GPU deployment"""
        return {
            "context": {
                "provider": "Lambda Labs",
                "gpu_type": gpu_type,
                "api_key_env": "LAMBDA_LABS_API_KEY",
                "preferred_regions": ["us-west-1", "us-east-1"]
            },
            "prompts": {
                "provision": f"""
                Provision a Lambda Labs GPU instance:
                1. Check availability of {gpu_type} GPUs
                2. Select region with lowest latency
                3. Configure with Ubuntu 22.04 + CUDA 12.1
                4. Install Docker and nvidia-docker
                5. Set up SSH keys from ~/.ssh/id_rsa.pub
                6. Configure firewall for ports: 22, 80, 443, 8000-8010
                7. Tag instance: project=orchestra-ai, env=production
                """,
                "deploy_model": f"""
                Deploy AI model to Lambda Labs:
                1. Build Docker image with model weights
                2. Push to registry (ECR or Docker Hub)
                3. SSH to Lambda instance
                4. Pull and run container with GPU support
                5. Set up health checks on port 8000
                6. Configure auto-restart on failure
                """
            }
        }
    
    @staticmethod
    def pulumi_stack_operations() -> Dict[str, Any]:
        """Generate prompts for Pulumi operations"""
        stack = os.getenv("PULUMI_STACK", "development")
        return {
            "context": {
                "stack": stack,
                "backend": "s3://orchestra-ai-pulumi-state",
                "language": "python",
                "providers": ["aws", "docker", "kubernetes"]
            },
            "prompts": {
                "create_resource": f"""
                Create Pulumi resource in {stack} stack:
                1. Import required provider (e.g., pulumi_aws)
                2. Define resource with proper naming: orchestra-{{resource_type}}-{{name}}
                3. Add tags: Environment={stack}, ManagedBy=Pulumi, Project=Orchestra
                4. Export important attributes (ARN, URL, etc.)
                5. Run: pulumi preview
                6. If no errors, run: pulumi up --yes
                """,
                "update_infrastructure": f"""
                Update Orchestra AI infrastructure:
                1. Pull latest Pulumi code
                2. Check current stack: pulumi stack
                3. Review pending changes: pulumi preview --diff
                4. Update resources incrementally
                5. Validate health after each change
                6. Update documentation in infrastructure/README.md
                """
            }
        }
    
    @staticmethod
    def vercel_deployment() -> Dict[str, Any]:
        """Generate prompts for Vercel deployment"""
        return {
            "context": {
                "project": "orchestra-ai",
                "framework": "vite",
                "api_directory": "api",
                "output_directory": "dist"
            },
            "prompts": {
                "deploy_frontend": """
                Deploy to Vercel:
                1. Ensure all env vars are set in Vercel dashboard:
                   - VITE_API_URL
                   - VITE_PORTKEY_API_KEY
                   - VITE_OPENROUTER_API_KEY
                2. Build locally first: npm run build
                3. Test build: npm run preview
                4. Deploy: vercel --prod
                5. Verify deployment at: https://orchestra-ai.vercel.app
                6. Check function logs for API routes
                """,
                "configure_api_routes": """
                Configure Vercel API routes:
                1. Create vercel.json with rewrites:
                   {
                     "rewrites": [
                       {"source": "/api/(.*)", "destination": "/api"}
                     ],
                     "functions": {
                       "api/index.py": {
                         "maxDuration": 30
                       }
                     }
                   }
                2. Ensure api/index.py exports the FastAPI app
                3. Add requirements.txt in api/
                4. Test locally: vercel dev
                """
            }
        }
    
    @staticmethod
    def database_operations() -> Dict[str, Any]:
        """Generate prompts for database operations"""
        return {
            "postgresql": {
                "connection": os.getenv("DATABASE_URL", "postgresql://localhost/orchestra"),
                "prompts": {
                    "create_migration": """
                    Create database migration:
                    1. Generate migration: alembic revision --autogenerate -m "description"
                    2. Review generated migration file
                    3. Test migration: alembic upgrade head
                    4. Test rollback: alembic downgrade -1
                    5. Commit migration file to git
                    """,
                    "optimize_query": """
                    Optimize PostgreSQL query:
                    1. Run EXPLAIN ANALYZE on the query
                    2. Check for sequential scans on large tables
                    3. Add appropriate indexes
                    4. Consider partial indexes for filtered queries
                    5. Use VACUUM ANALYZE after changes
                    """
                }
            },
            "vector_stores": {
                "pinecone": {
                    "index": "orchestra-embeddings",
                    "dimension": 1536,
                    "prompts": {
                        "create_index": """
                        Create Pinecone index:
                        1. Initialize client with API key
                        2. Create index with cosine metric
                        3. Wait for index to be ready
                        4. Configure replicas for production
                        5. Set up metadata filtering
                        """
                    }
                },
                "weaviate": {
                    "url": os.getenv("WEAVIATE_URL", "http://localhost:8080"),
                    "prompts": {
                        "create_schema": """
                        Create Weaviate schema:
                        1. Define class with properties
                        2. Set vectorizer to text2vec-openai
                        3. Configure moduleConfig for OpenAI
                        4. Add to schema
                        5. Verify with GET /v1/schema
                        """
                    }
                }
            }
        }

class DeploymentAutomation:
    """Automated deployment prompts"""
    
    @staticmethod
    def full_stack_deployment() -> str:
        """Complete deployment workflow"""
        return """
        Full Orchestra AI Deployment:
        
        1. Pre-deployment checks:
           - Run tests: pytest
           - Lint code: black . && mypy .
           - Build frontend: npm run build
           - Validate environment variables
        
        2. Database migrations:
           - Connect to production DB
           - Run: alembic upgrade head
           - Verify schema changes
        
        3. Deploy backend:
           - Build Docker image
           - Push to registry
           - Update Lambda Labs instance
           - Run health checks
        
        4. Deploy frontend:
           - Push to main branch
           - Vercel auto-deploys
           - Verify at production URL
        
        5. Post-deployment:
           - Check error logs
           - Verify API endpoints
           - Test critical paths
           - Update status page
        """
    
    @staticmethod
    def rollback_procedure() -> str:
        """Rollback prompts"""
        return """
        Rollback Procedure:
        
        1. Identify issue:
           - Check error logs
           - Identify failing component
        
        2. Frontend rollback:
           - Vercel dashboard > Deployments
           - Click "..." on previous deployment
           - Select "Promote to Production"
        
        3. Backend rollback:
           - SSH to Lambda Labs
           - docker ps to find container
           - docker stop [container]
           - docker run [previous-image-tag]
        
        4. Database rollback:
           - alembic downgrade -1
           - Verify data integrity
        
        5. Notify and document:
           - Update status page
           - Document issue and fix
        """

# Export all prompts for AI agents
def export_infrastructure_prompts():
    """Export all infrastructure prompts"""
    prompts = {
        "lambda_labs": InfrastructurePrompts.lambda_labs_deployment(),
        "pulumi": InfrastructurePrompts.pulumi_stack_operations(),
        "vercel": InfrastructurePrompts.vercel_deployment(),
        "databases": InfrastructurePrompts.database_operations(),
        "deployment": {
            "full_stack": DeploymentAutomation.full_stack_deployment(),
            "rollback": DeploymentAutomation.rollback_procedure()
        },
        "metadata": {
            "version": "1.0",
            "updated": datetime.utcnow().isoformat(),
            "project": "Orchestra AI"
        }
    }
    
    # Save to .ai-context directory
    output_path = ".ai-context/infrastructure_prompts.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(prompts, f, indent=2)
    
    return prompts 