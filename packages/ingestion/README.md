# File Ingestion System for Orchestra

This package provides a flexible, robust asynchronous file ingestion system for Orchestra, enabling the processing of various file types up to ~500MB in size, making them searchable with hyper-contextualized memory.

## Overview

The File Ingestion System allows users to process files via natural language commands in chat, supporting a wide range of file formats. It extracts text, generates embeddings, and makes the content searchable for use in knowledge-assisted conversations.

![Architecture Diagram](https://mermaid.ink/svg/pako:eNrNVV1P2zAU_SuWnyaBpKZpS7qn8dAJaRMDNPEwIiXu9TKr1Db-YCvqf59jJ-2aamzTtD3ky_Xx8fVJzrl30gsUIYyh56sFSxSTa4EZ3YGkqSLppkBMDPOkgiO_E-lBR3wMb5UzVZyRHBIPB_DSzehvdZ4QlaM87hzfXcCVFvg8ufoACVhB3ZkPUx_GIfTG5ziG4HYIvqXHIMtP8WzqQdILX_6yFgYLkjCSZNITgtEcxuDvXbwdDh7vx-N7-AGsP2UtNO1C7Dv8-9LqRCf29jtYi7cK5XH-qDWbI8d-hCkkCHwY8YoTnpMEkBTGRTaUjG5xrZTgm5AxeE6eMJVK0QKpQCmXqf4ksZn2Cnn5FDKlJtWQKSmLHKYFzzH1XB6PYHbVhs_d-PzHWMsymTw7EB2tEkX5HqM6pDEUlO3oOb-jcNQQ-gRrpmQxVWcvGqP6hCBXpJWTWbxTzqFJUGMQRbXMIWBkzahnbRnGAFLKg-8IzZUZ5PQrSlBGpEEhqpUu_v8xthYAzUYvVDZj_p3oQGEtBJz1hRYbg2E60JpFvRpBwZYFpVvgZ_CqmMK7RgdAjG_tHjkMVF3BDU8VY1s7JEsqp2uxlyhb6WGMgc01rcJbrbPLI6PYkMVOovPJIUclwTbUJI5wdnx-FmWrzU2rYqCy4mRfS2rqSuqGDddLcHDV-VYCJ6l0ezp0enXWPeJaRvNKt2d0ySyRyiJJFVsIIssKHmQJlHZX07YNI66VukmgUBpTjhbMIikjlGxk-_zXS4vHLq0eJ6sXfx3f9Fy0i9T15i18BVcQnZTVp7Hn_GYWOKtRYk3Z9GGLjDCW4IpzRmDj9PXUbXx-06qL60pYL6SxH9lFjNJlswEzWIpzqWuADd9xphDNXYEkfEXsL1gTqK-fCqzXiQBJ2GpZRXILmTaV5CuCy8h-CaNzJDdA9dM-8vTUxf9rqRvUgzXuLpnlZg_vF2HsB36puzTDcG3jf2K66-gAkgK3NQc0SsKN0tgP37zQf6PO2UfDdAG_9_LDNLO2vb0W_gEqMv0r)

## Features

- **Asynchronous Processing**: Handle large files without blocking the chat UI
- **Multi-Format Support**: Process PDFs, DOCX, XLSX, CSV, ZIP, images (with OCR), and more
- **Robust Error Handling**: Retries for network issues and graceful failure handling
- **Status Tracking**: Real-time status updates and notifications
- **Cloud-Native**: Uses GCP services (Cloud Storage, Firestore, Pub/Sub, Vertex AI)
- **Vector Search**: Store embeddings in PostgreSQL with pgvector for semantic search
- **Natural Language Interface**: Trigger ingestion via simple chat commands

## Components

- **API Integration**: Integrates with the chat interface to detect and process ingestion commands
- **Task Tracking**: Stores task state in Firestore for reliable tracking
- **Worker Process**: Asynchronous background worker for processing files
- **Text Extraction**: Specialized extractors for different file formats
- **Embedding Generation**: Integration with Vertex AI for generating embeddings
- **Storage**: Stores raw files, extracted text, and embeddings in appropriate backends

## Usage

Users can trigger file ingestion by using natural language commands in the chat interface:

```
ingest this document: https://example.com/document.pdf
```

The system will automatically:
1. Download the file
2. Extract text based on file type
3. Generate embeddings 
4. Store everything for later retrieval

## Installation

1. Install requirements:
   ```bash
   pip install -r packages/ingestion/requirements.txt
   ```

2. Set up environment variables:
   ```
   GOOGLE_CLOUD_PROJECT=your-project-id
   ENVIRONMENT=dev
   POSTGRES_DSN=postgres://user:password@localhost:5432/orchestra
   ```

3. Start the worker process (in a separate terminal):
   ```bash
   python packages/ingestion/src/worker/run_worker.py
   ```

## Infrastructure Requirements

- **GCP Services**:
  - Google Cloud Storage for file storage
  - Firestore for task and metadata storage
  - Pub/Sub for asynchronous processing
  - Vertex AI for embedding generation (optional)
  
- **PostgreSQL**:
  - PostgreSQL database with pgvector extension
  - Tables for storing embeddings and metadata

## Architecture

The system follows a microservices-based architecture:

1. **Chat Integration**: Intercepts chat messages and creates ingestion tasks
2. **API Service**: Handles task creation and status checking
3. **Worker Service**: Processes tasks from the queue, extracts text, generates embeddings
4. **Storage Services**: Multiple backend services for different data types

## Extending

You can extend the system by:

1. Adding new text extractors for additional file types
2. Implementing additional embedding models
3. Adding support for more notification channels
4. Building custom search interfaces on top of the stored data

## Contributing

Contributions are welcome! Please follow the standard Orchestra development workflow:

1. Create a branch
2. Make your changes
3. Add tests
4. Submit a PR

## License

Same as the Orchestra project
