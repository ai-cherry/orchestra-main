# Figma Setup Quick Guide

This guide provides focused instructions for setting up the Figma design system for Orchestra.

## 1. Run the Figma Page Setup Script

```bash
# Have your Figma Personal Access Token (PAT) ready
python3 setup_figma_pages.py YOUR_FIGMA_PAT_HERE
```

This will create these standard pages in your Figma file (ID: 368236963):
- _Foundations & Variables
- _Core Components [Adapted]
- Web - Dashboard
- Web - Agents
- Web - Personas
- And more...

## 2. Create Color Variables

1. Go to "_Foundations & Variables" page
2. Open Variables panel
3. Create "Orchestra-Color-Semantic" collection with 4 modes:
   - Neutral (default)
   - Cherry
   - Sophia
   - Gordon Gekko

4. Add these specific color variables:

| Variable | Neutral | Cherry | Sophia | Gordon Gekko |
|----------|---------|--------|--------|--------------|
| accent-primary | #8B5CF6 (Purple) | #E04DDA (Pink) | #38BDF8 (Blue) | #F97316 (Orange) |
| accent-secondary | #A78BFA | #F0ABFC | #7DD3FC | #FDBA74 |
| accent-text | #FFFFFF | #FFFFFF | #FFFFFF | #1A1A1A |

## 3. Create Typography Variables

1. Create "Orchestra-Typography" collection
2. Add typography variables:
   - font-family-ui: "Inter"
   - font-family-mono: "JetBrains Mono"

## 4. Adapt Core Components

Navigate to "_Core Components [Adapted]" page and create:

1. **Button (Primary)** - Use accent-primary for background, accent-text for text
2. **Card (Default)** - Dark background with subtle border
3. **Input (Default)** - Text input field with label and states
4. **Sidebar Item** - Navigation item with icon and text
5. **Top Bar Container** - App header with title and actions

Refer to component-adaptation-mapping.json for specific styling details.

## 5. Create Dashboard Design

1. Navigate to "Web - Dashboard" page
2. Use Figma's "First Draft" feature
3. Paste content from figma-first-draft-prompt.txt
4. Replace generated components with your adapted components
5. Follow the dark tech dashboard layout specs:
   - Dark background (#111827)
   - Left sidebar/icon rail
   - Top navigation bar
   - Main content divided into cards

## Dashboard Elements to Include:

- Prompt Hub (top)
- Unified Chat Feed (middle)
- Active Agents List (right side)
- System Health Card (right side)
- LLM Token Gauge (bottom right)

Follow the detailed specifications in figma-first-draft-prompt.txt for placement and styling.
