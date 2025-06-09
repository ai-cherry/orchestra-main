"""
Pulumi infrastructure as code for the feedback system.

This module provides Pulumi code for deploying the feedback system
directly to production, with no sandbox environments.
"""

import pulumi
import pulumi_aws as aws
import pulumi_postgresql as pg

# Configuration
config = pulumi.Config()
db_name = config.get("db_name") or "orchestra_feedback"
db_user = config.get("db_user") or "admin"
db_password = config.require_secret("db_password")
vpc_id = config.get("vpc_id")
subnet_ids = config.get_object("subnet_ids") or []
environment = "production"  # Always deploy to production

# Create PostgreSQL database for feedback
feedback_db = aws.rds.Instance("feedback-db",
    engine="postgres",
    engine_version="13.7",
    instance_class="db.t3.small",
    allocated_storage=20,
    storage_type="gp2",
    name=db_name,
    username=db_user,
    password=db_password,
    skip_final_snapshot=True,
    vpc_security_group_ids=[],  # Will be populated based on security group
    db_subnet_group_name=None,  # Will be populated if subnet_ids provided
    tags={
        "Name": "orchestra-feedback-db",
        "Environment": environment,
        "Project": "Orchestra AI"
    }
)

# Create Redis instance for caching
redis_cluster = aws.elasticache.Cluster("feedback-cache",
    engine="redis",
    engine_version="6.x",
    node_type="cache.t3.micro",
    num_cache_nodes=1,
    parameter_group_name="default.redis6.x",
    port=6379,
    subnet_group_name=None,  # Will be populated if subnet_ids provided
    security_group_ids=[],  # Will be populated based on security group
    tags={
        "Name": "orchestra-feedback-cache",
        "Environment": environment,
        "Project": "Orchestra AI"
    }
)

# Create security group for database access
db_security_group = aws.ec2.SecurityGroup("feedback-db-sg",
    description="Security group for Orchestra AI feedback database",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,
            to_port=5432,
            cidr_blocks=["10.0.0.0/16"]  # Restrict to VPC CIDR
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={
        "Name": "orchestra-feedback-db-sg",
        "Environment": environment,
        "Project": "Orchestra AI"
    }
)

# Create security group for Redis access
redis_security_group = aws.ec2.SecurityGroup("feedback-redis-sg",
    description="Security group for Orchestra AI feedback Redis",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=6379,
            to_port=6379,
            cidr_blocks=["10.0.0.0/16"]  # Restrict to VPC CIDR
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags={
        "Name": "orchestra-feedback-redis-sg",
        "Environment": environment,
        "Project": "Orchestra AI"
    }
)

# Create DB subnet group if subnet IDs are provided
if subnet_ids:
    db_subnet_group = aws.rds.SubnetGroup("feedback-db-subnet-group",
        subnet_ids=subnet_ids,
        tags={
            "Name": "orchestra-feedback-db-subnet-group",
            "Environment": environment,
            "Project": "Orchestra AI"
        }
    )
    
    redis_subnet_group = aws.elasticache.SubnetGroup("feedback-redis-subnet-group",
        subnet_ids=subnet_ids,
        tags={
            "Name": "orchestra-feedback-redis-subnet-group",
            "Environment": environment,
            "Project": "Orchestra AI"
        }
    )
    
    # Update DB and Redis with subnet groups
    feedback_db.db_subnet_group_name = db_subnet_group.name
    redis_cluster.subnet_group_name = redis_subnet_group.name

# Update security group IDs
feedback_db.vpc_security_group_ids = [db_security_group.id]
redis_cluster.security_group_ids = [redis_security_group.id]

# Create tables in PostgreSQL
def create_tables(endpoint):
    """
    Create feedback tables in PostgreSQL.
    
    Args:
        endpoint: Database endpoint
    """
    connection_string = f"postgresql://{db_user}:{db_password}@{endpoint}:5432/{db_name}"
    
    # Create feedback table
    feedback_table = pg.Table("feedback",
        name="feedback",
        database=db_name,
        schema="public",
        connection_string=connection_string,
        columns=[
            pg.TableColumnArgs(name="id", type="SERIAL", primary_key=True),
            pg.TableColumnArgs(name="user_id", type="VARCHAR(50)"),
            pg.TableColumnArgs(name="feedback_text", type="TEXT", not_null=True),
            pg.TableColumnArgs(name="sentiment", type="VARCHAR(20)"),
            pg.TableColumnArgs(name="source", type="VARCHAR(50)"),
            pg.TableColumnArgs(name="context_data", type="JSONB"),
            pg.TableColumnArgs(name="persona_id", type="VARCHAR(50)"),
            pg.TableColumnArgs(name="task_id", type="VARCHAR(50)"),
            pg.TableColumnArgs(name="rating", type="INTEGER"),
            pg.TableColumnArgs(name="created_at", type="TIMESTAMP", default="NOW()")
        ]
    )
    
    # Create feedback themes table
    themes_table = pg.Table("feedback_themes",
        name="feedback_themes",
        database=db_name,
        schema="public",
        connection_string=connection_string,
        columns=[
            pg.TableColumnArgs(name="id", type="SERIAL", primary_key=True),
            pg.TableColumnArgs(name="theme_name", type="VARCHAR(100)", not_null=True),
            pg.TableColumnArgs(name="theme_keywords", type="TEXT[]"),
            pg.TableColumnArgs(name="sentiment_distribution", type="JSONB"),
            pg.TableColumnArgs(name="feedback_count", type="INTEGER", default="0"),
            pg.TableColumnArgs(name="first_detected_at", type="TIMESTAMP", default="NOW()"),
            pg.TableColumnArgs(name="last_detected_at", type="TIMESTAMP", default="NOW()")
        ]
    )
    
    # Create feedback-theme mapping table
    mapping_table = pg.Table("feedback_theme_mapping",
        name="feedback_theme_mapping",
        database=db_name,
        schema="public",
        connection_string=connection_string,
        columns=[
            pg.TableColumnArgs(name="feedback_id", type="INTEGER", references="feedback(id)"),
            pg.TableColumnArgs(name="theme_id", type="INTEGER", references="feedback_themes(id)"),
            pg.TableColumnArgs(name="confidence_score", type="FLOAT")
        ],
        primary_key=["feedback_id", "theme_id"]
    )
    
    # Create persona feedback metrics table
    metrics_table = pg.Table("persona_feedback_metrics",
        name="persona_feedback_metrics",
        database=db_name,
        schema="public",
        connection_string=connection_string,
        columns=[
            pg.TableColumnArgs(name="persona_id", type="VARCHAR(50)"),
            pg.TableColumnArgs(name="time_period", type="VARCHAR(20)"),
            pg.TableColumnArgs(name="period_start", type="TIMESTAMP"),
            pg.TableColumnArgs(name="period_end", type="TIMESTAMP"),
            pg.TableColumnArgs(name="positive_count", type="INTEGER", default="0"),
            pg.TableColumnArgs(name="neutral_count", type="INTEGER", default="0"),
            pg.TableColumnArgs(name="negative_count", type="INTEGER", default="0"),
            pg.TableColumnArgs(name="average_rating", type="FLOAT"),
            pg.TableColumnArgs(name="common_themes", type="JSONB")
        ],
        primary_key=["persona_id", "time_period", "period_start"]
    )
    
    # Create indexes
    feedback_user_index = pg.Index("idx_feedback_user_id",
        name="idx_feedback_user_id",
        database=db_name,
        schema="public",
        table="feedback",
        columns=["user_id"],
        connection_string=connection_string
    )
    
    feedback_sentiment_index = pg.Index("idx_feedback_sentiment",
        name="idx_feedback_sentiment",
        database=db_name,
        schema="public",
        table="feedback",
        columns=["sentiment"],
        connection_string=connection_string
    )
    
    feedback_created_index = pg.Index("idx_feedback_created_at",
        name="idx_feedback_created_at",
        database=db_name,
        schema="public",
        table="feedback",
        columns=["created_at"],
        connection_string=connection_string
    )
    
    feedback_persona_index = pg.Index("idx_feedback_persona_id",
        name="idx_feedback_persona_id",
        database=db_name,
        schema="public",
        table="feedback",
        columns=["persona_id"],
        connection_string=connection_string
    )
    
    theme_name_index = pg.Index("idx_theme_name",
        name="idx_theme_name",
        database=db_name,
        schema="public",
        table="feedback_themes",
        columns=["theme_name"],
        connection_string=connection_string
    )
    
    return {
        "feedback_table": feedback_table,
        "themes_table": themes_table,
        "mapping_table": mapping_table,
        "metrics_table": metrics_table,
        "indexes": [
            feedback_user_index,
            feedback_sentiment_index,
            feedback_created_index,
            feedback_persona_index,
            theme_name_index
        ]
    }

# Create tables after database is provisioned
tables = feedback_db.endpoint.apply(create_tables)

# Export connection information
pulumi.export("feedback_db_endpoint", feedback_db.endpoint)
pulumi.export("feedback_db_name", db_name)
pulumi.export("feedback_db_port", 5432)
pulumi.export("redis_endpoint", redis_cluster.cache_nodes[0].address)
pulumi.export("redis_port", 6379)
pulumi.export("environment", environment)
