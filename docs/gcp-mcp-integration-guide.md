# GCP MCP Integration Guide: Pub/Sub & Service Directory

This guide details the recommended code modifications and best practices for integrating MCP servers with Google Cloud Pub/Sub and Service Directory, ensuring clarity, efficiency, and maintainability.

---

## 1. Pub/Sub Integration

### **A. Dependencies**
- Add `google-cloud-pubsub` to your requirements (Poetry or requirements.txt).

### **B. Configuration**
- Add the following to your MCP server config:
  - `PUBSUB_TOPIC`: Name of the Pub/Sub topic (e.g., `orchestra-events`)
  - `PUBSUB_SUBSCRIPTION`: Name of the subscription (e.g., `orchestra-events-sub`)
  - `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key (or use Workload Identity)

### **C. Publishing Events**
```python
from google.cloud import pubsub_v1
import os

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(os.environ["GCP_PROJECT"], os.environ["PUBSUB_TOPIC"])

def publish_event(event_type, payload):
    data = json.dumps({"type": event_type, "payload": payload}).encode("utf-8")
    future = publisher.publish(topic_path, data)
    future.result(timeout=10)
```

### **D. Subscribing to Events**
```python
from google.cloud import pubsub_v1
import os

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(os.environ["GCP_PROJECT"], os.environ["PUBSUB_SUBSCRIPTION"])

def callback(message):
    print(f"Received: {message.data}")
    message.ack()

subscriber.subscribe(subscription_path, callback=callback)
```

### **E. Best Practices**
- Use batch publishing for high-throughput scenarios.
- Handle message deduplication and retries.
- Monitor Pub/Sub health and log errors.

---

## 2. Service Directory Integration

### **A. Dependencies**
- Add `google-cloud-service-directory` to your requirements.

### **B. Registration at Startup**
```python
from google.cloud import servicedirectory_v1

client = servicedirectory_v1.RegistrationServiceClient()
namespace = f"projects/{project_id}/locations/us-central1/namespaces/orchestra"
service = f"{namespace}/services/mcp-server"

endpoint = servicedirectory_v1.Endpoint(
    address=public_ip, port=service_port, metadata={"version": "v1", "health": "healthy"}
)
client.create_endpoint(parent=service, endpoint_id="main", endpoint=endpoint)
```

### **C. Health Updates**
- Periodically update endpoint metadata with health status.

### **D. Resolving Endpoints**
```python
from google.cloud import servicedirectory_v1

client = servicedirectory_v1.LookupServiceClient()
service_name = f"projects/{project_id}/locations/us-central1/namespaces/orchestra/services/mcp-server"
response = client.resolve_service(name=service_name)
for endpoint in response.service.endpoints:
    print(endpoint.address, endpoint.port, endpoint.metadata)
```

### **E. Best Practices**
- Use namespaces for environment separation (dev, prod).
- Store version and health in endpoint metadata.
- Implement fallback to static config if Service Directory is unavailable.

---

## 3. Implementation Steps

1. Add required dependencies to your project.
2. Update MCP server config to include Pub/Sub and Service Directory settings.
3. Implement publish/subscribe logic for event-driven workflows.
4. Register MCP endpoints in Service Directory at startup and update health metadata.
5. Refactor service discovery to use Service Directory for endpoint resolution.
6. Add health checks and error handling for all integrations.
7. Test end-to-end event flow and service discovery.

---

## 4. References

- [Pub/Sub Python Client](https://cloud.google.com/pubsub/docs/publisher)
- [Service Directory Python Client](https://cloud.google.com/service-directory/docs/reference/libraries)
- [Pulumi GCP Docs](https://www.pulumi.com/registry/packages/gcp/)
- [GCP IAM Best Practices](https://cloud.google.com/iam/docs/least-privilege)

---

**This guide ensures your MCP servers are cloud-native, observable, and ready for robust, scalable orchestration on GCP.**