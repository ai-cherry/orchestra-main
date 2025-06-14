"""
Orchestra AI Infrastructure as Code using Pulumi
"""

import pulumi
import pulumi_aws as aws
import pulumi_docker as docker
import pulumi_kubernetes as k8s
from pulumi import Config, Output

# Get configuration
config = Config()
environment = config.get("environment") or "dev"
domain_name = config.get("domain") or "orchestra-ai.com"

# Create VPC
vpc = aws.ec2.Vpc(
    "orchestra-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"orchestra-vpc-{environment}",
        "Environment": environment,
    }
)

# Create subnets
public_subnet_1 = aws.ec2.Subnet(
    "public-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"orchestra-public-1-{environment}",
        "Environment": environment,
    }
)

public_subnet_2 = aws.ec2.Subnet(
    "public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-east-1b",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"orchestra-public-2-{environment}",
        "Environment": environment,
    }
)

# Internet Gateway
igw = aws.ec2.InternetGateway(
    "orchestra-igw",
    vpc_id=vpc.id,
    tags={
        "Name": f"orchestra-igw-{environment}",
        "Environment": environment,
    }
)

# Route table
route_table = aws.ec2.RouteTable(
    "orchestra-route-table",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={
        "Name": f"orchestra-routes-{environment}",
        "Environment": environment,
    }
)

# Associate route tables
route_table_association_1 = aws.ec2.RouteTableAssociation(
    "rta-1",
    subnet_id=public_subnet_1.id,
    route_table_id=route_table.id,
)

route_table_association_2 = aws.ec2.RouteTableAssociation(
    "rta-2",
    subnet_id=public_subnet_2.id,
    route_table_id=route_table.id,
)

# Security Group
security_group = aws.ec2.SecurityGroup(
    "orchestra-sg",
    vpc_id=vpc.id,
    description="Security group for Orchestra AI",
    ingress=[
        # HTTP
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        # HTTPS
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
        ),
        # API
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={
        "Name": f"orchestra-sg-{environment}",
        "Environment": environment,
    }
)

# RDS Database
db_subnet_group = aws.rds.SubnetGroup(
    "orchestra-db-subnet",
    subnet_ids=[public_subnet_1.id, public_subnet_2.id],
    tags={
        "Name": f"orchestra-db-subnet-{environment}",
        "Environment": environment,
    }
)

database = aws.rds.Instance(
    "orchestra-db",
    allocated_storage=20,
    storage_type="gp3",
    engine="postgres",
    engine_version="15",
    instance_class="db.t3.micro",
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[security_group.id],
    username="orchestra",
    password=config.get_secret("db_password") or "orchestra123",
    skip_final_snapshot=True,
    tags={
        "Name": f"orchestra-db-{environment}",
        "Environment": environment,
    }
)

# ElastiCache Redis
redis_subnet_group = aws.elasticache.SubnetGroup(
    "orchestra-redis-subnet",
    subnet_ids=[public_subnet_1.id, public_subnet_2.id],
)

redis_cluster = aws.elasticache.Cluster(
    "orchestra-redis",
    engine="redis",
    node_type="cache.t3.micro",
    num_cache_nodes=1,
    subnet_group_name=redis_subnet_group.name,
    security_group_ids=[security_group.id],
    tags={
        "Name": f"orchestra-redis-{environment}",
        "Environment": environment,
    }
)

# ECS Cluster
ecs_cluster = aws.ecs.Cluster(
    "orchestra-cluster",
    tags={
        "Name": f"orchestra-ecs-{environment}",
        "Environment": environment,
    }
)

# ECR Repositories
api_repo = aws.ecr.Repository(
    "orchestra-api",
    image_tag_mutability="MUTABLE",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
)

admin_repo = aws.ecr.Repository(
    "orchestra-admin",
    image_tag_mutability="MUTABLE",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
)

# Application Load Balancer
alb = aws.lb.LoadBalancer(
    "orchestra-alb",
    load_balancer_type="application",
    subnets=[public_subnet_1.id, public_subnet_2.id],
    security_groups=[security_group.id],
    tags={
        "Name": f"orchestra-alb-{environment}",
        "Environment": environment,
    }
)

# Target Groups
api_target_group = aws.lb.TargetGroup(
    "orchestra-api-tg",
    port=8000,
    protocol="HTTP",
    vpc_id=vpc.id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/health",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=2,
    ),
)

admin_target_group = aws.lb.TargetGroup(
    "orchestra-admin-tg",
    port=5173,
    protocol="HTTP",
    vpc_id=vpc.id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=2,
    ),
)

# ALB Listeners
http_listener = aws.lb.Listener(
    "orchestra-http",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=admin_target_group.arn,
        )
    ],
)

# Path-based routing
api_rule = aws.lb.ListenerRule(
    "api-rule",
    listener_arn=http_listener.arn,
    priority=100,
    conditions=[
        aws.lb.ListenerRuleConditionArgs(
            path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                values=["/api/*"]
            )
        )
    ],
    actions=[
        aws.lb.ListenerRuleActionArgs(
            type="forward",
            target_group_arn=api_target_group.arn,
        )
    ],
)

# Outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("database_endpoint", database.endpoint)
pulumi.export("redis_endpoint", redis_cluster.cache_nodes[0].address)
pulumi.export("alb_dns", alb.dns_name)
pulumi.export("api_repository_url", api_repo.repository_url)
pulumi.export("admin_repository_url", admin_repo.repository_url) 