# Factory AI Knowledge Droid

## Overview
The Knowledge Droid specializes in documentation, knowledge management, and context retrieval. It maintains and organizes project knowledge, ensuring information is accessible and up-to-date.

## Capabilities
- **Documentation Generation**: Creates comprehensive documentation
- **Knowledge Management**: Organizes and indexes project knowledge
- **Context Retrieval**: Finds relevant information quickly
- **Learning Extraction**: Captures lessons learned and best practices
- **Semantic Search**: Enables intelligent knowledge discovery

## Integration with Roo
- Maps to: `memory_server.py`
- Context sharing: Documentation, code comments, project history
- Fallback: Roo's memory system handles requests if Factory AI is unavailable

## Request Format
```json
{
  "droid": "knowledge",
  "task": "document|search|organize|extract",
  "context": {
    "subject": "string",
    "scope": "project|module|function",
    "existing_docs": ["array"],
    "code_context": "string",
    "metadata": {
      "tags": ["array"],
      "category": "string",
      "audience": "developer|user|admin"
    }
  },
  "options": {
    "format": "markdown|rst|html",
    "detail_level": "summary|standard|comprehensive",
    "include_examples": true,
    "language": "en"
  }
}
```

## Response Format
```json
{
  "documentation": {
    "content": "string",
    "structure": "object",
    "cross_references": ["array"]
  },
  "knowledge_graph": {
    "entities": ["array"],
    "relationships": ["array"],
    "context_map": "object"
  },
  "search_results": [
    {
      "relevance": 0.95,
      "content": "string",
      "source": "string",
      "metadata": "object"
    }
  ],
  "recommendations": {
    "related_topics": ["array"],
    "missing_documentation": ["array"],
    "quality_improvements": ["array"]
  }
}
```

## Performance Characteristics
- Average response time: 1-3 seconds
- Token usage: 1000-3000 per request
- Caching: Documentation cached for 24 hours
- Concurrency: Supports up to 30 parallel requests

## Best Practices
1. Maintain consistent documentation structure
2. Use semantic versioning for documentation
3. Include code examples and use cases
4. Cross-reference related documentation
5. Regular documentation reviews and updates

## Documentation Standards
- **Structure**: Clear hierarchy with navigation
- **Style**: Consistent tone and terminology
- **Examples**: Working code samples
- **Diagrams**: Visual representations where helpful
- **Versioning**: Track changes and maintain history

## Knowledge Organization
- **Categories**: API, Guides, Tutorials, Reference
- **Tagging**: Consistent taxonomy for discovery
- **Search**: Full-text and semantic search
- **Indexing**: Automated with manual curation
- **Updates**: Triggered by code changes

## Integration Points
- **Weaviate**: Vector storage for semantic search
- **PostgreSQL**: Structured documentation storage
- **Git**: Version control integration
- **CI/CD**: Automated documentation generation
- **IDE**: In-editor documentation access

## Quality Metrics
- **Coverage**: Percentage of code documented
- **Freshness**: Time since last update
- **Accuracy**: Validation against code
- **Usability**: User feedback scores
- **Searchability**: Query success rate