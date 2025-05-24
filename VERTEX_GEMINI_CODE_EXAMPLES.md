# Vertex AI and Gemini API Code Examples

This guide provides code examples for using the "badass" Vertex AI and Gemini service accounts with Python. These examples demonstrate how to authenticate with the service accounts and use the APIs for various tasks.

## Authentication

### Using Service Account Keys

```python
import os
from google.oauth2 import service_account
from google.cloud import aiplatform

# Path to the service account key file
key_path = "vertex-ai-key.json"

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Initialize Vertex AI with the credentials
aiplatform.init(
    project="cherry-ai-project",
    location="us-central1",
    credentials=credentials
)
```

### Using Workload Identity Federation (for GitHub Actions)

```python
import os
from google.auth import identity_pool
from google.cloud import aiplatform

# Get the Workload Identity Provider from environment
workload_identity_provider = os.environ.get("WORKLOAD_IDENTITY_PROVIDER")

# Create credentials
credentials = identity_pool.Credentials.from_info({
    "type": "external_account",
    "audience": f"//iam.googleapis.com/{workload_identity_provider}",
    "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
    "token_url": "https://sts.googleapis.com/v1/token",
    "service_account_impersonation_url": f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/vertex-ai-badass@cherry-ai-project.iam.gserviceaccount.com:generateAccessToken",
    "credential_source": {
        "url": "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
        "headers": {"Metadata-Flavor": "Google"},
        "format": {
            "type": "json",
            "subject_token_field_name": "access_token"
        }
    }
})

# Initialize Vertex AI with the credentials
aiplatform.init(
    project="cherry-ai-project",
    location="us-central1",
    credentials=credentials
)
```

## Vertex AI Examples

### Creating a Dataset

```python
from google.cloud import aiplatform

# Initialize the client
aiplatform.init(project="cherry-ai-project", location="us-central1")

# Create a dataset
dataset = aiplatform.TabularDataset.create(
    display_name="my-dataset",
    gcs_source=["gs://my-bucket/my-data.csv"],
)

print(f"Dataset created: {dataset.resource_name}")
```

### Training a Model

```python
from google.cloud import aiplatform

# Initialize the client
aiplatform.init(project="cherry-ai-project", location="us-central1")

# Get the dataset
dataset = aiplatform.TabularDataset("projects/cherry-ai-project/locations/us-central1/datasets/my-dataset")

# Create a training job
job = aiplatform.AutoMLTabularTrainingJob(
    display_name="my-training-job",
    optimization_objective="minimize-rmse",
)

# Start the training
model = job.run(
    dataset=dataset,
    target_column="target",
    training_fraction_split=0.8,
    validation_fraction_split=0.1,
    test_fraction_split=0.1,
    budget_milli_node_hours=1000,
    model_display_name="my-model",
)

print(f"Model created: {model.resource_name}")
```

### Deploying a Model

```python
from google.cloud import aiplatform

# Initialize the client
aiplatform.init(project="cherry-ai-project", location="us-central1")

# Get the model
model = aiplatform.Model("projects/cherry-ai-project/locations/us-central1/models/my-model")

# Deploy the model
endpoint = model.deploy(
    machine_type="n1-standard-4",
    min_replica_count=1,
    max_replica_count=5,
)

print(f"Model deployed to endpoint: {endpoint.resource_name}")
```

### Making Predictions

```python
from google.cloud import aiplatform

# Initialize the client
aiplatform.init(project="cherry-ai-project", location="us-central1")

# Get the endpoint
endpoint = aiplatform.Endpoint("projects/cherry-ai-project/locations/us-central1/endpoints/my-endpoint")

# Make a prediction
prediction = endpoint.predict(
    instances=[
        {"feature1": 1.0, "feature2": "value", "feature3": 2.0},
    ]
)

print(f"Prediction: {prediction}")
```

## Gemini API Examples

### Using the Gemini API

```python
import google.generativeai as genai
from google.oauth2 import service_account

# Path to the service account key file
key_path = "gemini-key.json"

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Configure the Gemini API
genai.configure(
    api_key=None,  # Not needed when using service account
    credentials=credentials,
    project_id="cherry-ai-project",
)

# Generate text
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Write a poem about artificial intelligence.')

print(response.text)
```

### Multi-turn Conversation

```python
import google.generativeai as genai
from google.oauth2 import service_account

# Path to the service account key file
key_path = "gemini-key.json"

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Configure the Gemini API
genai.configure(
    api_key=None,  # Not needed when using service account
    credentials=credentials,
    project_id="cherry-ai-project",
)

# Create a conversation
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])

# First turn
response = chat.send_message('What is Vertex AI?')
print(f"AI: {response.text}")

# Second turn
response = chat.send_message('How does it compare to other ML platforms?')
print(f"AI: {response.text}")
```

### Image Generation with Gemini

```python
import google.generativeai as genai
from google.oauth2 import service_account
import PIL.Image

# Path to the service account key file
key_path = "gemini-key.json"

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Configure the Gemini API
genai.configure(
    api_key=None,  # Not needed when using service account
    credentials=credentials,
    project_id="cherry-ai-project",
)

# Generate an image
model = genai.GenerativeModel('gemini-pro-vision')
response = model.generate_content([
    'Generate an image of a futuristic AI assistant helping a human.',
    PIL.Image.open('reference.jpg')  # Optional reference image
])

# Save the generated image
if response.parts[0].is_image:
    image_bytes = response.parts[0].image_bytes
    with open('generated_image.png', 'wb') as f:
        f.write(image_bytes)
    print("Image saved to generated_image.png")
```

## Integration with FastAPI

### Vertex AI Endpoint in FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.cloud import aiplatform
from google.oauth2 import service_account
import uvicorn

app = FastAPI()

# Path to the service account key file
key_path = "vertex-ai-key.json"

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Initialize Vertex AI with the credentials
aiplatform.init(
    project="cherry-ai-project",
    location="us-central1",
    credentials=credentials
)

# Get the endpoint
endpoint = aiplatform.Endpoint("projects/cherry-ai-project/locations/us-central1/endpoints/my-endpoint")

class PredictionRequest(BaseModel):
    features: dict

class PredictionResponse(BaseModel):
    prediction: list

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        # Make a prediction
        prediction = endpoint.predict(
            instances=[request.features]
        )
        return {"prediction": prediction.predictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Gemini API in FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from google.oauth2 import service_account
import uvicorn

app = FastAPI()

# Path to the service account key file
key_path = "gemini-key.json"

# Create credentials
credentials = service_account.Credentials.from_service_account_file(
    key_path,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Configure the Gemini API
genai.configure(
    api_key=None,  # Not needed when using service account
    credentials=credentials,
    project_id="cherry-ai-project",
)

# Create the model
model = genai.GenerativeModel('gemini-pro')

class GenerationRequest(BaseModel):
    prompt: str

class GenerationResponse(BaseModel):
    text: str

@app.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    try:
        # Generate text
        response = model.generate_content(request.prompt)
        return {"text": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Conclusion

These examples demonstrate how to use the "badass" Vertex AI and Gemini service accounts with Python. You can adapt these examples to your specific use cases and integrate them into your applications.

Remember that these service accounts have extensive permissions, so be careful when using them in production environments. Consider using more restricted service accounts for production deployments.
