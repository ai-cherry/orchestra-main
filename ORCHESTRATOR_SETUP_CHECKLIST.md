# Orchestrator Setup Checklist

This checklist provides detailed, step-by-step instructions for setting up both the Figma design system and backend infrastructure for Orchestra.

## Phase A: Figma Setup

### 1. Run Figma Page Setup Script

```bash
# Method 1: Provide PAT directly as argument
python3 setup_figma_pages.py YOUR_FIGMA_PAT_HERE

# Method 2: Set environment variable then run script
export FIGMA_PAT='YOUR_FIGMA_PAT_HERE'
python3 setup_figma_pages.py
```

☑️ Verify all 12 pages are created in your Figma file (ID: 368236963)

### 2. Create Figma Variables

#### Color Variables

1. Open your Figma file (ID: 368236963)
2. Navigate to the "\_Foundations & Variables" page
3. Open the Variables panel (Menu → Variables)
4. Create a new collection named "Orchestra-Color-Semantic"
5. Add 4 modes:
   - Neutral (default)
   - Cherry
   - Sophia
   - Gordon Gekko
6. Add variables with these exact values:

| Variable Name    | Neutral | Cherry  | Sophia  | Gordon Gekko |
| ---------------- | ------- | ------- | ------- | ------------ |
| accent-primary   | #8B5CF6 | #E04DDA | #38BDF8 | #F97316      |
| accent-secondary | #A78BFA | #F0ABFC | #7DD3FC | #FDBA74      |
| accent-text      | #FFFFFF | #FFFFFF | #FFFFFF | #1A1A1A      |

#### Typography Variables

1. Create another collection named "Orchestra-Typography"
2. Add variables:
   - font-family-ui: "Inter"
   - font-family-mono: "JetBrains Mono"

☑️ Verify all variables appear correctly in the Variables panel

### 3. Adapt Core Components

Navigate to "\_Core Components [Adapted]" page and create these components:

#### Button (Primary)

- Apply "Orchestra-Color-Semantic/accent-primary" to Background
- Apply "Orchestra-Color-Semantic/accent-text" to Text and Icon
- Remove border
- Create hover/active states

#### Card (Default)

- Apply "Base Surface Color Style" (Gray 800/900) to Container Background
- Add optional subtle border (Gray 700)
- Style header with Semibold Heading text (White)
- Style body with Regular Body text (Gray 300)

#### Input (Default)

- Apply "Input Background Style" (Gray 700) to Container
- Apply "Input Border Style" (Gray 600) to Border
- Apply "Input Text Style" (White) to Text
- Apply "Input Label Style" (Gray 400) to Label
- Apply "Orchestra-Color-Semantic/accent-primary" to Focus State

#### Sidebar Item

- Make Container transparent
- Style Icon with "Navigation Icon Style" (Gray 400)
- Style Text with "Navigation Text Style" (Gray 300)
- Apply "Orchestra-Color-Semantic/accent-primary" to Active State Container
- Apply "Orchestra-Color-Semantic/accent-text" to Active State Text/Icon

#### Top Bar Container

- Apply "Header Background Style" (Gray 900) to Background
- Apply "Subtle Separator Style" (Gray 800) to Border Bottom
- Apply "Page Title Style" (White, text-xl) to Title
- Apply "Action Icon Style" (Gray 400) to Action Icons
- Apply "Orchestra-Color-Semantic/accent-primary" to User Avatar Border

☑️ Verify all components use variables instead of hard-coded colors

### 4. Create Dashboard Design

1. Navigate to "Web - Dashboard" page
2. Use Figma's "First Draft" feature
3. Paste content from figma-first-draft-prompt.txt
4. After generation, replace generic elements with your adapted components
5. Ensure the layout follows these specifications:
   - Dark background (#111827)
   - Left sidebar (width: 64px/240px)
   - Top navigation bar (height: 64px)
   - 12-column grid with 24px gutters
   - 24px padding around containers
6. Verify all interface elements are present:
   - Prompt Hub (top, span 8 columns)
   - Unified Chat Feed (below Prompt Hub, span 8 columns)
   - Active Agents List (top-right, span 4 columns)
   - System Health Card (below Agents, span 4 columns)
   - LLM Token Gauge (bottom-right, span 4 columns)

☑️ Verify dashboard uses proper styling, components, and layout

## Phase B: Backend Infrastructure

### 5. Provision GCP Infrastructure

```bash
# Navigate to infra directory
cd /workspaces/orchestra-main/infra

# Initialize Terraform
terraform init

# Select dev workspace
terraform workspace select dev

# Plan the changes
terraform plan -var="env=dev"

# Apply configuration (approve when prompted)
terraform apply -var="env=dev"
```

☑️ Note all output values (URLs, resource IDs) for the next steps

### 6. Configure Environment Variables

```bash
# Set GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json
export GCP_PROJECT_ID=cherry-ai-project

# Set Redis configuration (use values from Terraform output)
export REDIS_HOST=[from terraform output]
export REDIS_PORT=6379
export REDIS_PASSWORD_SECRET_NAME=redis-auth-dev
```

☑️ Verify environment variables are set correctly

### 7. Run Integration Tests

```bash
# Make sure script is executable
chmod +x run_integration_tests.sh

# Enable integration tests
export RUN_INTEGRATION_TESTS=true

# Run tests
./run_integration_tests.sh
```

☑️ Verify all tests pass without errors

### 8. Verify Memory System

```bash
# Run validation script
python validate_memory_fixes.py
```

☑️ Verify script reports success for all operations

### 9. Deploy to Cloud Run (Optional)

```bash
# Make deploy script executable
chmod +x deploy_to_cloud_run.sh

# Deploy to Cloud Run
./deploy_to_cloud_run.sh dev
```

☑️ Verify deployment completes successfully

## Final Verification

### 10. Manual End-to-End Testing

Start the API server:

```bash
./run_api.sh
```

Test with curl commands:

```bash
# Test persona switching
curl -X POST "http://localhost:8000/api/interact?persona=cherry" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, who am I talking to?"}'

# Test memory storage and retrieval
curl -X POST "http://localhost:8000/api/interact?persona=cherry" \
  -H "Content-Type: application/json" \
  -d '{"text":"Remember this message", "user_id":"test_user"}'

curl -X POST "http://localhost:8000/api/interact?persona=cherry" \
  -H "Content-Type: application/json" \
  -d '{"text":"What was my last message?", "user_id":"test_user"}'
```

☑️ Verify the system responds correctly to all requests
