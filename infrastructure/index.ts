import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as awsx from "@pulumi/awsx";

// Configuration
const config = new pulumi.Config();
const domain = "cherry-ai.me";
const subdomain = "app";
const fullDomain = `${subdomain}.${domain}`;

// Create VPC for the application
const vpc = new awsx.ec2.Vpc("orchestra-vpc", {
    cidrBlock: "10.0.0.0/16",
    numberOfAvailabilityZones: 2,
    tags: {
        Name: "orchestra-ai-vpc",
        Environment: "production"
    }
});

// Create security group for the application
const appSecurityGroup = new aws.ec2.SecurityGroup("app-security-group", {
    vpcId: vpc.vpcId,
    description: "Security group for Orchestra AI application",
    ingress: [
        {
            protocol: "tcp",
            fromPort: 80,
            toPort: 80,
            cidrBlocks: ["0.0.0.0/0"],
        },
        {
            protocol: "tcp",
            fromPort: 443,
            toPort: 443,
            cidrBlocks: ["0.0.0.0/0"],
        },
        {
            protocol: "tcp",
            fromPort: 3000,
            toPort: 3000,
            cidrBlocks: ["0.0.0.0/0"],
        }
    ],
    egress: [
        {
            protocol: "-1",
            fromPort: 0,
            toPort: 0,
            cidrBlocks: ["0.0.0.0/0"],
        }
    ],
    tags: {
        Name: "orchestra-ai-sg",
        Environment: "production"
    }
});

// Create RDS PostgreSQL instance
const dbSubnetGroup = new aws.rds.SubnetGroup("db-subnet-group", {
    subnetIds: vpc.privateSubnetIds,
    tags: {
        Name: "orchestra-ai-db-subnet-group",
        Environment: "production"
    }
});

const database = new aws.rds.Instance("orchestra-db", {
    allocatedStorage: 20,
    maxAllocatedStorage: 100,
    storageType: "gp2",
    engine: "postgres",
    engineVersion: "15.4",
    instanceClass: "db.t3.micro",
    dbName: "orchestraai",
    username: "orchestraadmin",
    password: pulumi.secret("OrchestraAI2024!"),
    vpcSecurityGroupIds: [appSecurityGroup.id],
    dbSubnetGroupName: dbSubnetGroup.name,
    backupRetentionPeriod: 7,
    backupWindow: "03:00-04:00",
    maintenanceWindow: "sun:04:00-sun:05:00",
    skipFinalSnapshot: false,
    finalSnapshotIdentifier: "orchestra-ai-final-snapshot",
    tags: {
        Name: "orchestra-ai-database",
        Environment: "production"
    }
});

// Create ElastiCache Redis cluster
const redisSubnetGroup = new aws.elasticache.SubnetGroup("redis-subnet-group", {
    subnetIds: vpc.privateSubnetIds,
    description: "Subnet group for Orchestra AI Redis cluster"
});

const redisCluster = new aws.elasticache.ReplicationGroup("orchestra-redis", {
    description: "Orchestra AI Redis cluster",
    nodeType: "cache.t3.micro",
    port: 6379,
    parameterGroupName: "default.redis7",
    numCacheNodes: 1,
    subnetGroupName: redisSubnetGroup.name,
    securityGroupIds: [appSecurityGroup.id],
    atRestEncryptionEnabled: true,
    transitEncryptionEnabled: true,
    authToken: pulumi.secret("RedisAuth2024!"),
    tags: {
        Name: "orchestra-ai-redis",
        Environment: "production"
    }
});

// Create ECR repository for the application
const ecrRepo = new aws.ecr.Repository("orchestra-ai-repo", {
    name: "orchestra-ai",
    imageTagMutability: "MUTABLE",
    imageScanningConfiguration: {
        scanOnPush: true
    },
    tags: {
        Name: "orchestra-ai-ecr",
        Environment: "production"
    }
});

// Create ECS cluster
const cluster = new aws.ecs.Cluster("orchestra-cluster", {
    name: "orchestra-ai-cluster",
    capacityProviders: ["FARGATE"],
    defaultCapacityProviderStrategy: [{
        capacityProvider: "FARGATE",
        weight: 1
    }],
    tags: {
        Name: "orchestra-ai-cluster",
        Environment: "production"
    }
});

// Create Application Load Balancer
const alb = new awsx.elasticloadbalancingv2.ApplicationLoadBalancer("orchestra-alb", {
    listener: {
        port: 443,
        protocol: "HTTPS",
        certificateArn: pulumi.interpolate`arn:aws:acm:us-east-1:${aws.getCallerIdentity().then(id => id.accountId)}:certificate/your-cert-id`
    },
    defaultTargetGroup: {
        port: 3000,
        protocol: "HTTP",
        healthCheck: {
            enabled: true,
            path: "/health",
            protocol: "HTTP"
        }
    },
    securityGroups: [appSecurityGroup.id],
    subnets: vpc.publicSubnetIds,
    tags: {
        Name: "orchestra-ai-alb",
        Environment: "production"
    }
});

// Create ECS Task Definition
const taskDefinition = new aws.ecs.TaskDefinition("orchestra-task", {
    family: "orchestra-ai",
    cpu: "512",
    memory: "1024",
    networkMode: "awsvpc",
    requiresCompatibilities: ["FARGATE"],
    executionRoleArn: aws.iam.getRole({ name: "ecsTaskExecutionRole" }).then(role => role.arn),
    containerDefinitions: pulumi.jsonStringify([{
        name: "orchestra-ai",
        image: pulumi.interpolate`${ecrRepo.repositoryUrl}:latest`,
        portMappings: [{
            containerPort: 3000,
            protocol: "tcp"
        }],
        environment: [
            { name: "NODE_ENV", value: "production" },
            { name: "DATABASE_URL", value: pulumi.interpolate`postgresql://orchestraadmin:OrchestraAI2024!@${database.endpoint}/orchestraai` },
            { name: "REDIS_URL", value: pulumi.interpolate`redis://:RedisAuth2024!@${redisCluster.primaryEndpoint}:6379` },
            { name: "REDIS_USER_API_KEY", value: "S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7" },
            { name: "REDIS_ACCOUNT_KEY", value: "A4mmxx43yms087hucu51sxbau5mi9hmnz6u33k43mpauhof6rz2" },
            { name: "PINECONE_API_KEY", value: "pcsk_7PHV2G_Mj1rRCwiHZ7YsuuzJcqKch9akzNKXv6mfwDX65DenD8Q72w3Qjh4AmuataTnEDW" },
            { name: "WEAVIATE_REST_ENDPOINT", value: "w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud" },
            { name: "WEAVIATE_GRPC_ENDPOINT", value: "grpc-w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud" },
            { name: "WEAVIATE_API_KEY", value: "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf" }
        ],
        logConfiguration: {
            logDriver: "awslogs",
            options: {
                "awslogs-group": "/ecs/orchestra-ai",
                "awslogs-region": "us-east-1",
                "awslogs-stream-prefix": "ecs"
            }
        },
        essential: true
    }]),
    tags: {
        Name: "orchestra-ai-task",
        Environment: "production"
    }
});

// Create CloudWatch Log Group
const logGroup = new aws.cloudwatch.LogGroup("orchestra-logs", {
    name: "/ecs/orchestra-ai",
    retentionInDays: 30,
    tags: {
        Name: "orchestra-ai-logs",
        Environment: "production"
    }
});

// Create ECS Service
const service = new aws.ecs.Service("orchestra-service", {
    cluster: cluster.arn,
    taskDefinition: taskDefinition.arn,
    desiredCount: 1,
    launchType: "FARGATE",
    networkConfiguration: {
        subnets: vpc.privateSubnetIds,
        securityGroups: [appSecurityGroup.id],
        assignPublicIp: false
    },
    loadBalancers: [{
        targetGroupArn: alb.defaultTargetGroup.arn,
        containerName: "orchestra-ai",
        containerPort: 3000
    }],
    dependsOn: [alb],
    tags: {
        Name: "orchestra-ai-service",
        Environment: "production"
    }
});

// Create Route53 hosted zone (if not exists)
const hostedZone = aws.route53.getZone({
    name: domain,
    privateZone: false
});

// Create Route53 record for the application
const record = new aws.route53.Record("orchestra-record", {
    zoneId: hostedZone.then(zone => zone.zoneId),
    name: fullDomain,
    type: "A",
    aliases: [{
        name: alb.loadBalancer.dnsName,
        zoneId: alb.loadBalancer.zoneId,
        evaluateTargetHealth: true
    }]
});

// Export important values
export const vpcId = vpc.vpcId;
export const databaseEndpoint = database.endpoint;
export const redisEndpoint = redisCluster.primaryEndpoint;
export const albDnsName = alb.loadBalancer.dnsName;
export const ecrRepositoryUrl = ecrRepo.repositoryUrl;
export const applicationUrl = pulumi.interpolate`https://${fullDomain}`;
export const clusterName = cluster.name;
export const serviceName = service.name;

