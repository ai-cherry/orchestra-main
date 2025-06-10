# Notion Database Schemas - Complete Reference

## 📊 **Overview**

This document provides complete schemas for all 12 Notion databases in the Orchestra AI workspace, including property types, relationships, and usage examples.

## 🎯 **Project Management Databases**

### **Epic & Feature Tracking**
**Purpose**: High-level feature planning and epic management  
**Database ID**: `20bdba04-9402-8114-b57b-df7f1d4b2712`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Epic Title | Title | - | ✅ | Main epic identifier |
| Status | Select | Planning, In Progress, Testing, Done | ✅ | Current epic status |
| Priority | Select | Low, Medium, High, Critical | ✅ | Epic priority level |
| Persona | Select | Cherry, Sophia, Karen, Platform | ❌ | Target persona/domain |
| Estimated Effort | Number | - | ❌ | Story points or hours |
| Actual Effort | Number | - | ❌ | Actual time spent |
| Start Date | Date | - | ❌ | Epic start date |
| Target Date | Date | - | ❌ | Planned completion |
| Description | Rich Text | - | ❌ | Detailed epic description |
| Acceptance Criteria | Rich Text | - | ❌ | Success criteria |
| Technical Notes | Rich Text | - | ❌ | Implementation details |

### **Task Management**
**Purpose**: Detailed task tracking and assignment  
**Database ID**: `20bdba04-9402-81a2-99f3-e69dc37b73d6`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Task | Title | - | ✅ | Task name/identifier |
| Status | Select | Ready, In Progress, Review, Done, Blocked | ✅ | Current task status |
| Assignee | Select | Human Developer, Cursor AI,  AI, Continue AI | ✅ | Task assignee |
| Priority | Select | Low, Medium, High, Critical | ✅ | Task priority |
| Type | Select | Feature, Bug, Refactor, Documentation, Infrastructure | ✅ | Task category |
| Epic | Relation | → Epic & Feature Tracking | ❌ | Parent epic link |
| Estimated Hours | Number | - | ❌ | Time estimate |
| Actual Hours | Number | - | ❌ | Actual time spent |
| Due Date | Date | - | ❌ | Task deadline |
| Description | Rich Text | - | ❌ | Detailed task description |
| Technical Details | Rich Text | - | ❌ | Implementation specifics |
| Completion Notes | Rich Text | - | ❌ | Post-completion insights |

### **Development Log**
**Purpose**: Comprehensive development activity tracking  
**Database ID**: `20bdba04-9402-81fd-9558-d66c07d9576c`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Title | Title | - | ✅ | Activity description |
| Type | Select | Code, Config, Deploy, Debug, Research, Review | ✅ | Activity type |
| Tool Used | Select | Manual, Cursor, , Continue, GitHub, Notion | ✅ | Primary tool used |
| Date | Date | - | ✅ | Activity date |
| Files Changed | Number | - | ❌ | Number of files modified |
| Lines Added | Number | - | ❌ | Lines of code added |
| Lines Removed | Number | - | ❌ | Lines of code removed |
| Commit Hash | Rich Text | - | ❌ | Git commit reference |
| Notes | Rich Text | - | ❌ | Activity notes |
| Performance Impact | Select | Positive, Neutral, Negative | ❌ | Performance effect |
| Learning Insights | Rich Text | - | ❌ | Key learnings |

## 🤖 **AI Coding Databases**

### **Coding Rules & Standards**
**Purpose**: AI coding assistant configuration and standards  
**Database ID**: `20bdba04940281bdadf1e78f4e0989e8`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Title | Title | - | ✅ | Rule name/identifier |
| Category | Select | Python, TypeScript, React, Infrastructure, AI Tools, Security | ✅ | Rule category |
| Status | Select | Active, Draft, Deprecated | ✅ | Rule status |
| Priority | Select | Low, Medium, High, Critical | ✅ | Rule importance |
| Rule Content | Rich Text | - | ✅ | Detailed rule specification |
| Examples | Rich Text | - | ❌ | Code examples |
| Rationale | Rich Text | - | ❌ | Why this rule exists |
| Tools Applied | Multi-select | Cursor, , Continue, All | ❌ | Which tools use this rule |
| Last Updated | Date | - | ❌ | Last modification date |

### **MCP Server Connections**
**Purpose**: Model Context Protocol server activity and health monitoring  
**Database ID**: `20bdba04940281aea36af6144ec68df2`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Tool | Title | - | ✅ | Tool/server name |
| Activity | Rich Text | - | ❌ | Recent activity description |
| Status | Select | Active, Inactive, Error, Connecting | ✅ | Connection status |
| Context | Rich Text | - | ❌ | Context information |
| Timestamp | Date | - | ❌ | Last activity time |
| Response Time | Number | - | ❌ | Response time (ms) |
| Error Details | Rich Text | - | ❌ | Error information |
| Success Rate | Number | - | ❌ | Success percentage |

### **Code Reflection & Learning**
**Purpose**: AI insights and continuous improvement tracking  
**Database ID**: `20bdba049402814d8e53fbec166ef030`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Tool | Title | - | ✅ | AI tool providing insight |
| Category | Select | Performance, Workflow, Optimization, Learning, Error | ✅ | Insight category |
| Insight | Rich Text | - | ✅ | Detailed insight description |
| Status | Select | New, Reviewed, Implemented, Archived | ✅ | Processing status |
| Priority | Select | Low, Medium, High | ✅ | Implementation priority |
| Implementation | Rich Text | - | ❌ | How to implement |
| Impact | Select | Minor, Moderate, Major | ❌ | Expected impact |
| Date | Date | - | ❌ | Insight creation date |

### **AI Tool Performance Metrics**
**Purpose**: Performance tracking for AI coding tools  
**Database ID**: `20bdba049402813f8404fa8d5f615b02`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Tool | Select | Cursor, , Continue, MCP Server | ✅ | Tool being measured |
| Metric Type | Select | Performance, Usage, Quality, Error Rate | ✅ | Type of metric |
| Value | Number | - | ❌ | Metric value |
| Unit | Select | Milliseconds, Requests, Percentage, Count | ❌ | Measurement unit |
| Status | Select | Good, Warning, Critical | ❌ | Performance status |
| Details | Rich Text | - | ❌ | Additional context |
| Timestamp | Date | - | ❌ | Measurement time |
| Context | Rich Text | - | ❌ | Measurement context |

## 👥 **Persona Feature Databases**

### **Cherry Features**
**Purpose**: Personal assistant AI features and capabilities  
**Database ID**: `20bdba04-9402-8162-9e3c-fa8c8e41fd16`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Feature Name | Title | - | ✅ | Feature identifier |
| Status | Select | Planned, In Development, Testing, Released | ✅ | Development status |
| Priority | Select | Low, Medium, High, Critical | ✅ | Feature priority |
| Category | Select | Productivity, Automation, Learning, Integration | ✅ | Feature category |
| Description | Rich Text | - | ✅ | Feature description |
| Use Cases | Rich Text | - | ❌ | Primary use cases |
| Technical Requirements | Rich Text | - | ❌ | Implementation needs |
| Target Release | Date | - | ❌ | Planned release date |

### **Sophia Features**
**Purpose**: Financial services AI features and capabilities  
**Database ID**: `20bdba04-9402-811d-83b4-cdc1a2505623`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Feature Name | Title | - | ✅ | Feature identifier |
| Status | Select | Planned, In Development, Testing, Released | ✅ | Development status |
| Priority | Select | Low, Medium, High, Critical | ✅ | Feature priority |
| Category | Select | Payment Processing, Compliance, Analytics, Security | ✅ | Feature category |
| Description | Rich Text | - | ✅ | Feature description |
| Compliance Requirements | Rich Text | - | ❌ | Regulatory needs |
| Security Considerations | Rich Text | - | ❌ | Security requirements |
| Target Release | Date | - | ❌ | Planned release date |

### **Karen Features**
**Purpose**: Medical coding AI features and capabilities  
**Database ID**: `20bdba04-9402-819c-b2ca-d3d3828691e6`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Feature Name | Title | - | ✅ | Feature identifier |
| Status | Select | Planned, In Development, Testing, Released | ✅ | Development status |
| Priority | Select | Low, Medium, High, Critical | ✅ | Feature priority |
| Category | Select | Medical Coding, Compliance, Integration, Analytics | ✅ | Feature category |
| Description | Rich Text | - | ✅ | Feature description |
| Medical Standards | Rich Text | - | ❌ | Relevant standards (ICD-10, CPT) |
| HIPAA Requirements | Rich Text | - | ❌ | Privacy/security needs |
| Target Release | Date | - | ❌ | Planned release date |

## 📚 **Operations Databases**

### **Patrick Instructions**
**Purpose**: Development guidelines and operational procedures  
**Database ID**: `20bdba04-9402-81b4-9890-e663db2b50a3`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Title | Title | - | ✅ | Instruction title |
| Category | Select | Development, Deployment, Security, AI Tools, Daily Operations | ✅ | Instruction category |
| Priority | Select | Low, Medium, High, Critical | ✅ | Instruction importance |
| Status | Select | Active, Draft, Deprecated | ✅ | Instruction status |
| Instructions | Rich Text | - | ✅ | Detailed instructions |
| Prerequisites | Rich Text | - | ❌ | Requirements/dependencies |
| Examples | Rich Text | - | ❌ | Usage examples |
| Last Updated | Date | - | ❌ | Last modification |

### **Knowledge Base**
**Purpose**: Foundational project knowledge and references  
**Database ID**: `20bdba04-9402-81a4-bc27-e06d160e3378`

| Property | Type | Options | Required | Description |
|----------|------|---------|----------|-------------|
| Knowledge Item | Title | - | ✅ | Knowledge title |
| Category | Select | Architecture, APIs, Infrastructure, Best Practices, Troubleshooting | ✅ | Knowledge category |
| Type | Select | Guide, Reference, Tutorial, FAQ | ✅ | Content type |
| Status | Select | Current, Outdated, Under Review | ✅ | Knowledge status |
| Detailed Content | Rich Text | - | ✅ | Full knowledge content |
| Related Items | Rich Text | - | ❌ | Related knowledge links |
| Tags | Multi-select | Frontend, Backend, Mobile, Infrastructure, AI | ❌ | Content tags |
| Last Updated | Date | - | ❌ | Last modification |

## 🔗 **Database Relationships**

### **Primary Relationships**
- **Tasks** → **Epics**: Many-to-one relationship for epic tracking
- **Development Log** → **Tasks**: Implicit relationship through commit references
- **Code Reflection** → **AI Tool Metrics**: Related insights and performance data
- **Persona Features** → **Epics**: Feature implementation tracking

### **Cross-Database Workflows**
1. **Epic Planning**: Epic & Feature Tracking → Task Management → Development Log
2. **AI Optimization**: AI Tool Metrics → Code Reflection → Coding Rules
3. **Feature Development**: Persona Features → Task Management → Development Log
4. **Knowledge Management**: Knowledge Base → Patrick Instructions → Code Reflection

## 📝 **Usage Examples**

### **Creating a New Epic**
```json
{
  "Epic Title": "Enhanced AI Tool Coordination",
  "Status": "Planning",
  "Priority": "High",
  "Persona": "Platform",
  "Description": "Improve task routing and context sharing between AI tools",
  "Acceptance Criteria": "50% improvement in task routing accuracy"
}
```

### **Logging Development Activity**
```json
{
  "Title": "Implemented MCP server optimization",
  "Type": "Code",
  "Tool Used": "Cursor",
  "Files Changed": 3,
  "Lines Added": 150,
  "Performance Impact": "Positive"
}
```

### **Recording AI Insight**
```json
{
  "Tool": "",
  "Category": "Workflow",
  "Insight": "Sequential thinking patterns improve complex task breakdown",
  "Status": "New",
  "Priority": "High"
}
```

## 🔄 **Maintenance Guidelines**

### **Weekly Tasks**
- Review and update database schemas
- Clean up outdated entries
- Validate relationship integrity

### **Monthly Tasks**
- Analyze database usage patterns
- Optimize property configurations
- Update documentation

### **Best Practices**
- Use consistent naming conventions
- Maintain required field integrity
- Regular backup and validation
- Document schema changes

---

**Last Updated**: 2025-01-24  
**Version**: 2.0  
**Contact**: Orchestra AI Development Team 