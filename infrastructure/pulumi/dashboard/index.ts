// Pulumi infrastructure configuration for Admin UI
// Deploys to Google Cloud Platform with auto-scaling and monitoring

import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import * as docker from "@pulumi/docker";

// Configuration
const config = new pulumi.Config();
const projectId = config.require("gcp:project");
const region = config.get("region") || "us-central1";
const environment = pulumi.getStack();

// Labels for all resources
const labels = {
    app: "admin-ui",
    environment: environment,
    managedBy: "pulumi",
};

// Service name based on environment
const serviceName = `admin-ui-${environment}`;

// Enable required APIs
const enabledApis = [
    "run.googleapis.com",
    "containerregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
].map(api => new gcp.projects.Service(`${api}-service`, {
    service: api,
    disableOnDestroy: false,
}));

// Service Account for Cloud Run
const serviceAccount = new gcp.serviceaccount.Account("admin-ui-sa", {
    accountId: `${serviceName}-sa`,
    displayName: "Admin UI Service Account",
    description: "Service account for Admin UI Cloud Run service",
});

// IAM roles for service account
const serviceAccountRoles = [
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/secretmanager.secretAccessor",
].map((role, index) => new gcp.projects.IAMMember(`admin-ui-sa-role-${index}`, {
    project: projectId,
    role: role,
    member: pulumi.interpolate`serviceAccount:${serviceAccount.email}`,
}));

// Secret Manager for API keys
const apiKeySecret = new gcp.secretmanager.Secret("admin-ui-api-key", {
    secretId: `${serviceName}-api-key`,
    replication: {
        auto: {},
    },
    labels: labels,
});

const apiKeySecretVersion = new gcp.secretmanager.SecretVersion("admin-ui-api-key-version", {
    secret: apiKeySecret.id,
    secretData: config.getSecret("apiKey") || "placeholder-api-key",
});

// VPC Network
const network = new gcp.compute.Network("admin-ui-vpc", {
    name: `${serviceName}-vpc`,
    autoCreateSubnetworks: false,
});

const subnet = new gcp.compute.Subnetwork("admin-ui-subnet", {
    name: `${serviceName}-subnet`,
    ipCidrRange: "10.0.0.0/24",
    region: region,
    network: network.id,
    privateIpGoogleAccess: true,
});

// Build and push Docker image
const adminUiImage = new docker.Image("admin-ui-image", {
    imageName: pulumi.interpolate`gcr.io/${projectId}/admin-ui:${environment}-${Date.now()}`,
    build: {
        context: "../../../dashboard",
        dockerfile: "../../../dashboard/Dockerfile",
        args: {
            NEXT_PUBLIC_API_URL: config.get("apiUrl") || "http://localhost:8080",
        },
    },
    registry: {
        server: "gcr.io",
        username: "_json_key",
        password: config.requireSecret("gcpServiceAccountKey"),
    },
});

// Cloud Run Service
const cloudRunService = new gcp.cloudrunv2.Service("admin-ui-service", {
    name: serviceName,
    location: region,
    template: {
        serviceAccount: serviceAccount.email,
        scaling: {
            minInstanceCount: environment === "production" ? 2 : 1,
            maxInstanceCount: environment === "production" ? 100 : 10,
        },
        containers: [{
            image: adminUiImage.imageName,
            resources: {
                limits: {
                    cpu: environment === "production" ? "2" : "1",
                    memory: environment === "production" ? "1Gi" : "512Mi",
                },
                cpuIdle: true,
            },
            envs: [
                {
                    name: "NODE_ENV",
                    value: "production",
                },
                {
                    name: "API_KEY",
                    valueSource: {
                        secretKeyRef: {
                            secret: apiKeySecret.secretId,
                            version: "latest",
                        },
                    },
                },
            ],
            ports: [{
                containerPort: 3000,
            }],
            startupProbe: {
                initialDelaySeconds: 0,
                timeoutSeconds: 1,
                periodSeconds: 3,
                failureThreshold: 1,
                tcpSocket: {
                    port: 3000,
                },
            },
            livenessProbe: {
                httpGet: {
                    path: "/api/health",
                },
                initialDelaySeconds: 10,
                periodSeconds: 10,
                timeoutSeconds: 5,
                failureThreshold: 3,
            },
        }],
        vpcAccess: {
            networkInterfaces: [{
                network: network.id,
                subnetwork: subnet.id,
            }],
            egress: "PRIVATE_RANGES_ONLY",
        },
    },
    traffics: [{
        type: "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST",
        percent: 100,
    }],
    labels: labels,
}, { dependsOn: enabledApis });

// Allow unauthenticated access (for public dashboard)
const cloudRunIamMember = new gcp.cloudrun.IamMember("admin-ui-invoker", {
    service: cloudRunService.name,
    location: region,
    role: "roles/run.invoker",
    member: "allUsers",
});

// Cloud Armor Security Policy
const securityPolicy = new gcp.compute.SecurityPolicy("admin-ui-security-policy", {
    name: `${serviceName}-security-policy`,
    rules: [
        {
            action: "throttle",
            priority: 1000,
            match: {
                versionedExpr: "SRC_IPS_V1",
                config: {
                    srcIpRanges: ["*"],
                },
            },
            rateLimitOptions: {
                conformAction: "allow",
                exceedAction: "deny(429)",
                rateLimitThreshold: {
                    count: 100,
                    intervalSec: 60,
                },
            },
        },
        {
            action: "allow",
            priority: 2147483647,
            match: {
                versionedExpr: "SRC_IPS_V1",
                config: {
                    srcIpRanges: ["*"],
                },
            },
        },
    ],
});

// Global IP Address
const globalAddress = new gcp.compute.GlobalAddress("admin-ui-ip", {
    name: `${serviceName}-ip`,
});

// Managed SSL Certificate
const sslCertificate = new gcp.compute.ManagedSslCertificate("admin-ui-cert", {
    name: `${serviceName}-cert`,
    managed: {
        domains: environment === "production" 
            ? ["admin.yourdomain.com"] 
            : [`admin-${environment}.yourdomain.com`],
    },
});

// Network Endpoint Group for Cloud Run
const neg = new gcp.compute.RegionNetworkEndpointGroup("admin-ui-neg", {
    name: `${serviceName}-neg`,
    networkEndpointType: "SERVERLESS",
    region: region,
    cloudRun: {
        service: cloudRunService.name,
    },
});

// Health Check
const healthCheck = new gcp.compute.HealthCheck("admin-ui-health-check", {
    name: `${serviceName}-health-check`,
    httpsHealthCheck: {
        port: 443,
        requestPath: "/api/health",
    },
    checkIntervalSec: 10,
    timeoutSec: 5,
    healthyThreshold: 2,
    unhealthyThreshold: 3,
});

// Backend Service with CDN
const backendService = new gcp.compute.BackendService("admin-ui-backend", {
    name: `${serviceName}-backend`,
    backends: [{
        group: neg.id,
    }],
    cdnPolicy: {
        cacheMode: "CACHE_ALL_STATIC",
        defaultTtl: 3600,
        clientTtl: 7200,
        maxTtl: 86400,
        negativeCaching: true,
        serveWhileStale: 86400,
        signedUrlCacheMaxAgeSec: 7200,
    },
    securityPolicy: securityPolicy.id,
    healthChecks: [healthCheck.id],
    logConfig: {
        enable: true,
        sampleRate: 1.0,
    },
});

// URL Map
const urlMap = new gcp.compute.URLMap("admin-ui-url-map", {
    name: `${serviceName}-url-map`,
    defaultService: backendService.id,
});

// HTTPS Proxy
const httpsProxy = new gcp.compute.TargetHttpsProxy("admin-ui-https-proxy", {
    name: `${serviceName}-https-proxy`,
    urlMap: urlMap.id,
    sslCertificates: [sslCertificate.id],
});

// Global Forwarding Rule
const forwardingRule = new gcp.compute.GlobalForwardingRule("admin-ui-forwarding-rule", {
    name: `${serviceName}-forwarding-rule`,
    ipAddress: globalAddress.address,
    ipProtocol: "TCP",
    portRange: "443",
    target: httpsProxy.id,
});

// Monitoring Alert Policy
const alertPolicy = new gcp.monitoring.AlertPolicy("admin-ui-high-error-rate", {
    displayName: `${serviceName} - High Error Rate`,
    combiner: "OR",
    conditions: [{
        displayName: "Error rate > 5%",
        conditionThreshold: {
            filter: pulumi.interpolate`metric.type="run.googleapis.com/request_count" resource.type="cloud_run_revision" resource.label."service_name"="${serviceName}" metric.label."response_code_class"="5xx"`,
            duration: "300s",
            comparison: "COMPARISON_GT",
            thresholdValue: 0.05,
            aggregations: [{
                alignmentPeriod: "60s",
                perSeriesAligner: "ALIGN_RATE",
            }],
        },
    }],
    notificationChannels: environment === "production" 
        ? [config.get("alertChannelId") || ""] 
        : [],
    alertStrategy: {
        autoClose: "1800s",
    },
});

// Exports
export const serviceUrl = cloudRunService.uri;
export const loadBalancerIp = globalAddress.address;
export const dashboardUrl = environment === "production"
    ? "https://admin.yourdomain.com"
    : pulumi.interpolate`https://admin-${environment}.yourdomain.com`;