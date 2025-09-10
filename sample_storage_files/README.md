# AI Chatbot Storage Files

This directory contains sample files that demonstrate the storage format used by the AI chatbot system.

## Storage Configuration

The system automatically detects your operating system and uses the appropriate storage path:

- **Windows**: `C:\Users\yosef\OneDrive\Desktop\Attachments`
- **Linux**: `/home/ubuntu/scraped_data`
- **Custom**: Set `AI_STORAGE_PATH` environment variable

## File Types

The system creates JSON files automatically with the following structure:

### Message Files
- Format: `message_{service}_{timestamp}.json`
- Contains: Original message, enhanced message with context, instructions

### Scraped Data Files  
- Format: `{service}_{timestamp}.json`
- Contains: Conversation data, embeddings, metadata

## Usage

1. Copy these sample files to your configured storage directory
2. The system will read existing JSON files for context
3. New files are created automatically during operation
4. You can add any other files (Word docs, etc.) to the same directory

## Context Retrieval

The system uses embeddings to find similar previous conversations and includes them as context in new messages to the AI services.
