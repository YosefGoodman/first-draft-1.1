# AI Chatbot Management System

## Overview

This project is a sophisticated multi-AI chatbot management platform that enables users to interact with multiple AI services (ChatGPT, Claude, Mistral, Gemini) simultaneously through a unified web interface. The system serves developers, researchers, and power users who need to:

- **Compare AI responses** across different models for the same query
- **Maintain conversation context** using semantic embeddings and historical data
- **Scrape and analyze** AI conversation data for research or analysis
- **Automate AI interactions** while supporting manual intervention when needed

The platform combines automated context enhancement with manual interaction workflows, storing all conversations with embeddings for semantic search and context retrieval. Users can send messages to all AI services at once ("Ask All" functionality) or interact with individual services, with the system maintaining conversation history and providing relevant context for each interaction.

## Quick Start

### Prerequisites
- Python 3.8+
- Chrome browser (for browser automation)

### Installation & Setup
```bash
# Clone the repository
git clone https://github.com/YosefGoodman/first-draft-1.1.git
cd first-draft-1.1

# Install dependencies
pip install -r requirements.txt

# Start the application
python app.py
```

### Access the Application
Open your browser and navigate to `http://localhost:5001`

### Basic Usage
1. **Start AI Sessions**: Click "Start Session" for any AI service to open browser tabs
2. **Manual Login**: Log into each AI service manually in the opened tabs
3. **Send Messages**: Use individual panel inputs or the global "Ask All" feature
4. **Scrape Data**: Click "Scrape Data" to extract and store conversation data with embeddings

## Key Features

### ✅ Quad Browser Dashboard
- Four-panel layout for simultaneous AI service management
- Real-time status indicators and connection management
- Checkbox toggles for selective AI service activation

### ✅ Browser Session Management
- Bypasses iframe CSP restrictions using `window.open()`
- Playwright integration for browser automation via Chrome DevTools Protocol
- Manual login workflow with automated message injection

### ✅ Context Enhancement
- SentenceTransformer embeddings for semantic similarity search
- Automatic context retrieval from conversation history
- Enhanced message generation with relevant historical context

### ✅ Local Data Storage
- JSON file storage with configurable paths (Windows/Linux)
- SQLite database for conversation history and embeddings
- Automatic file consolidation and organization

### ✅ Message Broadcasting
- "Ask All" functionality for simultaneous multi-AI queries
- Individual panel messaging with context enhancement
- Real-time chat preview and status updates

## Project Organization

### Core Systems and Services

**1. HTTP Server Backend (`app.py`)** - Main application server
- Handles all API endpoints and session management
- Manages browser sessions for each AI service
- Integrates with database for context retrieval
- Coordinates file storage operations

**2. Web Frontend** - Browser-based user interface
- `templates/index.html` - Multi-panel AI interface structure
- `static/app.js` - JavaScript application logic with ChatApp and AIPanel classes  
- `static/style.css` - Responsive UI styling

**3. Database Layer (`database.py`)** - Persistent conversation storage
- SQLite database with embedding support
- Semantic similarity search using sentence transformers
- Context retrieval for message enhancement

**4. Storage System** - File-based data persistence
- JSON files for messages and scraped data
- Timestamped files with embeddings
- Sample storage files for testing and examples

**5. Deployment Infrastructure** - Cross-platform startup
- `startup.sh` / `startup.bat` - Platform-specific startup scripts
- `requirements.txt` - Python dependencies
- `desktop_app.py` - Alternative PyWebView desktop interface

### Main Files and Directories

```
├── app.py                          # Main HTTP server (AIBrowserHandler)
├── database.py                     # SQLite + embeddings storage
├── startup.sh / startup.bat        # Cross-platform deployment
├── requirements.txt                # Python dependencies
├── templates/
│   └── index.html                  # Multi-panel web interface
├── static/
│   ├── app.js                      # Frontend JavaScript (ChatApp/AIPanel)
│   └── style.css                   # UI styling
├── sample_storage_files/           # Example data and documentation
│   ├── README.md                   # Storage system documentation
│   ├── sample_message_chatgpt.json # Example message format
│   └── sample_scraped_chatgpt.json # Example scraped data format
├── desktop_app.py                  # Alternative PyWebView interface
├── TESTING.md                      # Comprehensive testing guide
└── iframe_test.html               # AI service compatibility testing
```

## Technical Implementation

### Browser Automation
The system bypasses iframe CSP restrictions by using `window.open()` to launch separate browser windows for each AI service. Playwright integration provides automation capabilities via Chrome DevTools Protocol.

### Context Enhancement
Uses SentenceTransformer (`all-MiniLM-L6-v2`) to generate 384-dimensional embeddings for semantic similarity search. Previous conversations are automatically retrieved and included as context in new messages.

### Storage Configuration
- **Windows**: `C:\Users\yosef\OneDrive\Desktop\Attachments`
- **Linux**: `/home/ubuntu/scraped_data`
- **Custom**: Set `AI_STORAGE_PATH` environment variable

### File Types
1. **Message Files**: `message_{service}_{timestamp}.json`
2. **Scraped Data Files**: `{service}_{timestamp}.json`
3. **Response Files**: `{service}_response_{timestamp}.json`

## Testing

See [TESTING.md](TESTING.md) for comprehensive testing instructions and verification procedures.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (see TESTING.md)
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
