# AI Control Panel Testing Guide

## Overview

This document provides comprehensive testing instructions for the AI Control Panel web application.

## Prerequisites

1. Python 3.8+ with required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Chrome browser with remote debugging enabled (optional for advanced features)

## Starting the Application

```bash
python app.py
```

The server will start on port 5001. Access the application at `http://localhost:5001`

## Core Features Testing

### 1. Quad Browser Dashboard
- ✅ Verify all 4 AI panels display correctly (ChatGPT, Claude, Mistral, Gemini)
- ✅ Check panel icons and status indicators
- ✅ Test checkbox toggles for enabling/disabling panels

### 2. Browser Session Management
- ✅ Click "Start Session" buttons for each AI service
- ✅ Verify new browser tabs open for each service
- ✅ Confirm status changes from "Not Connected" to "Connected"
- ✅ Test manual login workflow in opened tabs

### 3. Message Injection
- ✅ Type messages in individual panel input fields
- ✅ Click send buttons to inject messages
- ✅ Verify messages appear in chat preview areas

### 4. Ask All Broadcasting
- ✅ Type message in global "Message Active AI Panels" input
- ✅ Click send button to broadcast to all enabled panels
- ✅ Verify message appears in all active panel previews

### 5. Data Scraping & Storage
- ✅ Click "Scrape Data" buttons for active panels
- ✅ Verify JSON files created in storage directory
- ✅ Check embedding generation (384-dimensional vectors)
- ✅ Confirm proper file naming conventions

### 6. Context Enhancement
- ✅ Send multiple messages to test context retrieval
- ✅ Verify similar context is included in enhanced messages
- ✅ Check database storage of interactions

## Storage System Testing

### File Structure Verification
Check that files are created in the correct storage path:
- **Linux**: `/home/ubuntu/scraped_data/`
- **Windows**: `C:\Users\yosef\OneDrive\Desktop\Attachments`

### Expected File Types
1. **Message Files**: `message_{service}_{timestamp}.json`
2. **Scraped Data Files**: `{service}_{timestamp}.json`
3. **Response Files**: `{service}_response_{timestamp}.json`

### JSON Structure Validation
Each scraped file should contain:
- `service`: AI service name
- `timestamp`: ISO format timestamp
- `chat_elements`: Array of conversation turns
- `embedding`: 384-dimensional vector array
- `full_text`: Concatenated conversation text

## Database Testing

### SQLite Database Verification
```bash
# Check database file exists
ls -la database.db

# Verify table structure (optional)
sqlite3 database.db ".schema"
```

### Context Retrieval Testing
1. Send initial message to any AI service
2. Send follow-up message with similar content
3. Verify context from previous conversation is included

## Troubleshooting

### Common Issues
1. **Port 5001 already in use**: Kill existing process or use different port
2. **Playwright connection fails**: Ensure Chrome remote debugging is available
3. **Storage permission errors**: Check write permissions for storage directory
4. **Missing dependencies**: Run `pip install -r requirements.txt`

### Debug Mode
Enable verbose logging by modifying `app.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Testing

### Load Testing
- Test with multiple simultaneous browser sessions
- Verify embedding generation performance
- Check memory usage with large conversation histories

### Storage Testing
- Test with large conversation datasets
- Verify file consolidation functionality
- Check disk space usage over time

## Security Considerations

### CSP Bypass Verification
- Confirm iframe restrictions are properly bypassed
- Test `window.open()` functionality for all AI services
- Verify Playwright automation works without CSP violations

### Data Privacy
- Ensure local storage only (no external data transmission)
- Verify embedding generation happens locally
- Check that sensitive conversation data remains on local machine

## Automated Testing

Future improvements could include:
- Unit tests for core functionality
- Integration tests for browser automation
- Performance benchmarks for embedding generation
- CI/CD pipeline for automated testing

## Test Results Documentation

When testing, document:
- Browser versions tested
- Operating system compatibility
- Performance metrics
- Any issues encountered
- Screenshots of successful operations

## Conclusion

This testing guide ensures comprehensive validation of all AI Control Panel features. Regular testing helps maintain system reliability and user experience quality.
