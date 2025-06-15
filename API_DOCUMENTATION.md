# Orchestra AI Platform - API Documentation

## 🚀 API Overview

The Orchestra AI Platform provides a comprehensive REST API for persona management, advanced search, and AI orchestration. This documentation covers all available endpoints and their usage.

**Base URL**: `http://localhost:8000`  
**API Version**: v1  
**Authentication**: Currently open (authentication planned for future releases)

---

## 📋 Table of Contents

1. [Health & System](#health--system)
2. [Persona Management](#persona-management)
3. [Advanced Search](#advanced-search)
4. [Chat & Messaging](#chat--messaging)
5. [Analytics](#analytics)
6. [Error Handling](#error-handling)

---

## 🏥 Health & System

### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-15T17:22:00Z",
  "version": "1.0.0"
}
```

### GET /api/system/status
Comprehensive system status including database and services.

**Response:**
```json
{
  "status": "operational",
  "database": {
    "connected": true,
    "response_time_ms": 12
  },
  "services": {
    "persona_management": "active",
    "search_engine": "active",
    "chat_interface": "active"
  },
  "uptime_seconds": 3600
}
```

---

## 👤 Persona Management

### GET /api/personas
Retrieve all available personas.

**Response:**
```json
{
  "personas": [
    {
      "id": "uuid-here",
      "name": "Cherry",
      "persona_type": "assistant",
      "description": "Creative AI specialized in content creation, design, and innovation",
      "communication_style": {
        "tone": "friendly",
        "style": "creative"
      },
      "knowledge_domains": ["creative", "design", "content"],
      "is_active": true,
      "created_at": "2025-06-15T10:00:00Z",
      "domain_leanings": {
        "keywords": ["creative", "design", "innovation"],
        "weight_multiplier": 1.2
      },
      "voice_settings": {
        "voice_id": "elevenlabs_voice_id",
        "stability": 0.75,
        "similarity_boost": 0.85
      },
      "search_preferences": {
        "default_mode": "normal",
        "include_database": true,
        "max_results": 10
      }
    }
  ]
}
```

### GET /api/personas/{persona_id}
Retrieve a specific persona by ID.

**Parameters:**
- `persona_id` (path): UUID of the persona

**Response:**
```json
{
  "id": "uuid-here",
  "name": "Sophia",
  "persona_type": "analyst",
  "description": "Strategic AI focused on analysis, planning, and complex problem-solving",
  "communication_style": {
    "tone": "professional",
    "style": "analytical"
  },
  "knowledge_domains": ["analysis", "strategy", "business"],
  "is_active": true,
  "domain_leanings": {
    "keywords": ["business", "analytics", "strategy"],
    "weight_multiplier": 1.3
  },
  "voice_settings": {
    "voice_id": "sophia_voice_id",
    "stability": 0.8,
    "similarity_boost": 0.9
  }
}
```

### PUT /api/personas/{persona_id}
Update a persona's configuration.

**Parameters:**
- `persona_id` (path): UUID of the persona

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "communication_style": {
    "tone": "professional",
    "style": "analytical"
  },
  "knowledge_domains": ["analysis", "strategy"],
  "domain_leanings": {
    "keywords": ["business", "analytics"],
    "weight_multiplier": 1.4
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Persona updated successfully",
  "persona": { /* updated persona object */ }
}
```

### PUT /api/personas/{persona_id}/domain-leanings
Update domain leanings for a persona.

**Request Body:**
```json
{
  "keywords": ["business", "analytics", "strategy", "data"],
  "weight_multiplier": 1.3,
  "learning_enabled": true
}
```

### PUT /api/personas/{persona_id}/voice-settings
Update voice settings for a persona.

**Request Body:**
```json
{
  "voice_id": "elevenlabs_voice_id",
  "stability": 0.75,
  "similarity_boost": 0.85,
  "style": "professional",
  "use_speaker_boost": true
}
```

### GET /api/personas/analytics/summary
Get analytics summary for all personas.

**Response:**
```json
{
  "total_interactions": 1250,
  "active_personas": 3,
  "top_persona": {
    "name": "Sophia",
    "usage_percentage": 45.2
  },
  "usage_by_persona": [
    {
      "persona_id": "uuid-here",
      "name": "Sophia",
      "interactions": 565,
      "percentage": 45.2
    }
  ],
  "domain_performance": {
    "business": 0.92,
    "creative": 0.88,
    "technical": 0.85
  }
}
```

---

## 🔍 Advanced Search

### GET /api/search/modes
Get available search modes and their configurations.

**Response:**
```json
{
  "modes": ["normal", "deep", "super_deep", "uncensored"],
  "configurations": {
    "normal": {
      "max_sources": 3,
      "timeout": 10,
      "apis": ["duckduckgo", "database"],
      "scraping": false,
      "cost_estimate": "Free",
      "time_estimate": "2-5s"
    },
    "deep": {
      "max_sources": 5,
      "timeout": 20,
      "apis": ["duckduckgo", "exa_ai", "serp", "database"],
      "scraping": true,
      "scraping_depth": "light",
      "cost_estimate": "$0.02-0.05",
      "time_estimate": "10-20s"
    },
    "super_deep": {
      "max_sources": 8,
      "timeout": 30,
      "apis": ["duckduckgo", "exa_ai", "serp", "apify", "phantombuster", "database"],
      "scraping": true,
      "scraping_depth": "aggressive",
      "cost_estimate": "$0.05-0.10",
      "time_estimate": "20-30s"
    },
    "uncensored": {
      "max_sources": 6,
      "timeout": 25,
      "apis": ["venice_ai", "zenrows", "exa_ai", "database"],
      "scraping": true,
      "scraping_depth": "aggressive",
      "content_filtering": false,
      "cost_estimate": "$0.03-0.08",
      "time_estimate": "15-25s"
    }
  }
}
```

### GET /api/search/sources
Get available search sources and their status.

**Response:**
```json
{
  "sources": {
    "database": {
      "available": true,
      "cost": "Free",
      "response_time_ms": 15
    },
    "duckduckgo": {
      "available": true,
      "cost": "Free",
      "response_time_ms": 250
    },
    "exa_ai": {
      "available": false,
      "cost": "$0.01/search",
      "reason": "API key not configured"
    },
    "serp_api": {
      "available": false,
      "cost": "$0.005/search",
      "reason": "API key not configured"
    },
    "apify": {
      "available": false,
      "cost": "$0.02/search",
      "reason": "API key not configured"
    }
  }
}
```

### POST /api/search/advanced
Execute an advanced search with intelligent blending.

**Request Body:**
```json
{
  "query": "artificial intelligence trends 2025",
  "search_mode": "deep",
  "persona": "sophia",
  "max_results": 15,
  "include_database": true,
  "include_internet": true,
  "filters": {
    "date_range": "past_year",
    "content_type": ["article", "research"],
    "language": "en"
  }
}
```

**Response:**
```json
{
  "search_id": "search-uuid-here",
  "query": "artificial intelligence trends 2025",
  "search_mode": "deep",
  "persona": "sophia",
  "total_results": 12,
  "processing_time_ms": 15420,
  "cost_usd": 0.034,
  "sources_used": ["database", "duckduckgo", "exa_ai"],
  "results": [
    {
      "id": "result-1",
      "title": "AI Trends 2025: What to Expect",
      "url": "https://example.com/ai-trends-2025",
      "snippet": "Comprehensive analysis of emerging AI trends...",
      "source": "exa_ai",
      "relevance_score": 0.95,
      "persona_weight": 1.3,
      "final_score": 1.235,
      "metadata": {
        "published_date": "2025-01-15",
        "author": "AI Research Institute",
        "content_type": "research"
      }
    }
  ],
  "blending_info": {
    "persona_keywords_matched": ["business", "analytics", "strategy"],
    "domain_weight_applied": 1.3,
    "source_distribution": {
      "database": 3,
      "duckduckgo": 4,
      "exa_ai": 5
    }
  }
}
```

---

## 💬 Chat & Messaging

### POST /api/chat
Send a message to a persona and get a response.

**Request Body:**
```json
{
  "message": "What are the latest trends in AI for business?",
  "persona": "sophia",
  "context": {
    "conversation_id": "conv-uuid-here",
    "previous_messages": 5
  },
  "search_enabled": true,
  "search_mode": "normal"
}
```

**Response:**
```json
{
  "response": "Based on the latest research, here are the key AI trends for business in 2025...",
  "persona": "sophia",
  "conversation_id": "conv-uuid-here",
  "message_id": "msg-uuid-here",
  "timestamp": "2025-06-15T17:22:00Z",
  "search_results": {
    "query_used": "AI trends business 2025",
    "results_count": 8,
    "sources": ["database", "duckduckgo"]
  },
  "persona_context": {
    "domain_leanings_applied": true,
    "keywords_matched": ["business", "analytics"],
    "response_style": "analytical"
  }
}
```

### POST /api/search
Basic search functionality (legacy endpoint).

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "max_results": 10
}
```

**Response:**
```json
{
  "query": "machine learning algorithms",
  "results": [
    {
      "title": "Introduction to Machine Learning Algorithms",
      "url": "https://example.com/ml-algorithms",
      "snippet": "Comprehensive guide to ML algorithms...",
      "source": "database"
    }
  ],
  "total_results": 8,
  "processing_time_ms": 245
}
```

---

## 📊 Analytics

### GET /api/analytics/search
Get search analytics and usage statistics.

**Query Parameters:**
- `start_date` (optional): ISO date string
- `end_date` (optional): ISO date string
- `persona` (optional): Filter by persona name

**Response:**
```json
{
  "period": {
    "start_date": "2025-06-01T00:00:00Z",
    "end_date": "2025-06-15T23:59:59Z"
  },
  "total_searches": 1250,
  "search_modes": {
    "normal": 850,
    "deep": 300,
    "super_deep": 75,
    "uncensored": 25
  },
  "cost_breakdown": {
    "total_cost_usd": 45.67,
    "by_mode": {
      "normal": 0.00,
      "deep": 12.50,
      "super_deep": 28.75,
      "uncensored": 4.42
    }
  },
  "performance": {
    "average_response_time_ms": 8420,
    "success_rate": 0.987
  },
  "top_queries": [
    {
      "query": "AI trends 2025",
      "count": 45,
      "avg_results": 12.3
    }
  ]
}
```

### GET /api/analytics/personas
Get persona usage analytics.

**Response:**
```json
{
  "total_interactions": 2340,
  "personas": [
    {
      "name": "Sophia",
      "interactions": 1053,
      "percentage": 45.0,
      "avg_response_time_ms": 1250,
      "satisfaction_score": 0.92,
      "top_domains": ["business", "analytics", "strategy"]
    },
    {
      "name": "Cherry",
      "interactions": 789,
      "percentage": 33.7,
      "avg_response_time_ms": 980,
      "satisfaction_score": 0.89,
      "top_domains": ["creative", "design", "content"]
    }
  ],
  "domain_performance": {
    "business": {
      "queries": 456,
      "success_rate": 0.94,
      "avg_relevance": 0.87
    }
  }
}
```

---

## ⚠️ Error Handling

### Error Response Format
All API errors follow a consistent format:

```json
{
  "error": {
    "code": "PERSONA_NOT_FOUND",
    "message": "The specified persona could not be found",
    "details": {
      "persona_id": "invalid-uuid",
      "available_personas": ["cherry", "sophia", "karen"]
    },
    "timestamp": "2025-06-15T17:22:00Z",
    "request_id": "req-uuid-here"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PERSONA_NOT_FOUND` | 404 | Specified persona does not exist |
| `INVALID_SEARCH_MODE` | 400 | Invalid search mode specified |
| `SEARCH_TIMEOUT` | 408 | Search request timed out |
| `API_KEY_MISSING` | 401 | Required API key not configured |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `DATABASE_ERROR` | 503 | Database connection issue |

### Rate Limiting
- **Standard endpoints**: 100 requests/minute
- **Search endpoints**: 20 requests/minute
- **Analytics endpoints**: 10 requests/minute

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## 🔧 Configuration

### Environment Variables
The API behavior can be configured using environment variables:

```bash
# Search Configuration
SEARCH_COST_TRACKING=true
SEARCH_ANALYTICS_ENABLED=true
MAX_SEARCH_RESULTS=50
DEFAULT_SEARCH_MODE=normal

# Persona Configuration
PERSONA_ANALYTICS_ENABLED=true
DOMAIN_LEARNING_ENABLED=true
VOICE_SYNTHESIS_ENABLED=true

# API Keys (for enhanced search modes)
EXA_AI_API_KEY=your_key_here
SERP_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

### API Versioning
The API uses URL-based versioning. Current version is `v1` (default).

Future versions will be available at:
- `/api/v2/personas`
- `/api/v2/search/advanced`

---

## 📝 Examples

### Complete Search Workflow
```bash
# 1. Check available search modes
curl http://localhost:8000/api/search/modes

# 2. Check source availability
curl http://localhost:8000/api/search/sources

# 3. Execute search
curl -X POST http://localhost:8000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI trends 2025",
    "search_mode": "deep",
    "persona": "sophia",
    "max_results": 10
  }'

# 4. Get search analytics
curl http://localhost:8000/api/analytics/search
```

### Persona Management Workflow
```bash
# 1. List all personas
curl http://localhost:8000/api/personas

# 2. Get specific persona
curl http://localhost:8000/api/personas/sophia-uuid

# 3. Update domain leanings
curl -X PUT http://localhost:8000/api/personas/sophia-uuid/domain-leanings \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["business", "analytics", "strategy"],
    "weight_multiplier": 1.4
  }'

# 4. Get analytics
curl http://localhost:8000/api/analytics/personas
```

---

**Orchestra AI API Documentation - Version 1.0**  
*Last updated: June 15, 2025*

