# 🎮 Universal Twitch MCP Server

**Professional Model Context Protocol server for Twitch Helix API with 141 tools and intelligent filtering.**

[![FastMCP](https://img.shields.io/badge/FastMCP-2.0-blue)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 🚀 Features

- **📦 141 Tools** from real Twitch Helix API via OpenAPI generation
- **🏷️ Smart Filtering** by 30+ categories for any use case
- **🎬 Automation Mode** for clips & highlights workflow (`--automation-mode`)
- **🔄 All Transports** - HTTP, STDIO, SSE support
- **⚡ FastMCP 2.0** with all latest features
- **🛠️ Production Ready** - clean, documented code for opensource

## ⚡ Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/mcp-twitch.git
cd mcp-twitch

# Install dependencies
uv sync

# Set environment variables
cp .env.example .env
# Edit .env with your Twitch API keys
```

### Usage

**Universal mode (all 141 tools):**
```bash
uv run python mcp_twitch_server.py
```

**Filtered by categories:**
```bash
# Only channels, users, and streams
uv run python mcp_twitch_server.py --include-tags channels users streams

# Exclude moderation tools
uv run python mcp_twitch_server.py --exclude-tags moderation
```

**HTTP server for integrations:**
```bash
uv run python mcp_twitch_server.py --transport http --port 8080
```

**🎬 Automation mode for clips & highlights:**
```bash
# Specialized for content automation
uv run python mcp_twitch_server.py --automation-mode

# With N8N integration
uv run python mcp_twitch_server.py --automation-mode --transport http --port 8080
```

## 🔑 API Keys Setup

### 1. Get Client ID
1. Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Create new application
3. Copy Client ID

### 2. Get Access Token (optional)
1. Visit [TwitchTokenGenerator.com](https://twitchtokengenerator.com)
2. Select required scopes
3. Generate and copy token

### 3. Environment Variables
```bash
# Required
TWITCH_CLIENT_ID=your_client_id_here

# Optional (for authenticated endpoints)
TWITCH_ACCESS_TOKEN=your_access_token_here
TWITCH_REFRESH_TOKEN=your_refresh_token_here
```

## 🏷️ Available Categories

| Category | Tools | Description |
|----------|-------|-------------|
| `channels` | 6+ | Channel management and information |
| `users` | 8+ | User profiles and information |
| `streams` | 6+ | Live stream data and monitoring |
| `clips` | 3+ | Video clips management |
| `games` | 3+ | Game and category information |
| `search` | 4+ | Search channels, categories, streams |
| `analytics` | 5+ | Analytics and statistics |
| `moderation` | 20+ | Moderation and chat management |
| `chat` | 15+ | Chat interactions and messages |
| `content` | 10+ | Content and video management |
| `followers` | 4+ | Follower relationships |
| `following` | 3+ | Following relationships |
| `extensions` | 8+ | Twitch extensions |

## 🎬 Automation Mode

Special mode for content creators and automation workflows:

```bash
# Enable automation mode
uv run python mcp_twitch_server.py --automation-mode
```

**What it includes:**
- ✂️ Only clips, videos, streams, users, games, search endpoints
- 🔥 Special tools: `analyze_viral_potential`, `get_trending_clips` 
- 📊 Trend monitoring and analysis tools
- 🔄 Optimized for N8N workflow integration
- 🎯 Perfect for content automation pipelines

**Use cases:**
- Automated clip discovery and curation
- Trend monitoring for content creation
- Viral potential analysis of streamers
- N8N workflow integration for content pipelines

## 🔗 Integration Examples

### Claude Desktop
```json
{
  "mcpServers": {
    "twitch": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp_twitch_server.py"],
      "env": {
        "TWITCH_CLIENT_ID": "your_client_id"
      }
    }
  }
}
```

### Docker (Recommended for Production)

**Quick start with Docker:**
```bash
# Build and run
docker compose up -d

# Universal mode on port 8080
curl http://localhost:8080/health

# Automation mode on port 8081  
docker compose --profile automation up -d
```

**Build from source:**
```bash
docker build -t twitch-mcp .
docker run -p 8080:8080 -e TWITCH_CLIENT_ID=your_id twitch-mcp
```

### Railway Deployment (One-Click Deploy)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

**Manual Railway deployment:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway deploy

# Set environment variables
railway variables set TWITCH_CLIENT_ID=your_client_id
railway variables set TWITCH_ACCESS_TOKEN=your_token
```

### HTTP API
```bash
# Health check
curl http://localhost:8080/health

# List all tools
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Get top games
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_top_games", "arguments": {"first": 5}}}'
```

### N8N Workflow (Automation Mode)
```bash
# Local development
uv run python mcp_twitch_server.py --automation-mode --transport http --port 8080

# Docker
docker compose --profile automation up -d

# Railway (set AUTOMATION_MODE=true)
# N8N HTTP Request Node URL: https://your-app.railway.app/mcp
```

## 📊 Rate Limits & Performance

| Token Type | Rate Limit | Best For |
|------------|------------|----------|
| No Token | 30 requests/min | Public data, testing |
| App Token | 800 requests/min | **Recommended for production** |
| User Token | 120 requests/min/user | Personal user data |

**Performance Tips:**
- Use `--include-tags` to load only needed tools
- Use `--automation-mode` for specialized workflows
- Cache results when possible
- Monitor rate limits in production

## 🛠️ Development & Deployment

### Project Structure
```
mcp-twitch/
├── mcp_twitch_server.py    # Main server code
├── openapi.json           # Twitch API specification  
├── pyproject.toml         # Dependencies (uv)
├── Dockerfile             # Production container
├── docker-compose.yml     # Local development
├── railway.toml           # Railway deployment config
├── start.sh              # Startup script
├── .env.example          # Environment template
└── README.md             # This documentation
```

### Local Development
```bash
# List all available tags
uv run python mcp_twitch_server.py --list-tags

# Test specific category
uv run python mcp_twitch_server.py --include-tags channels

# Debug mode
uv run python mcp_twitch_server.py --no-transformations

# HTTP server for local testing
uv run python mcp_twitch_server.py --transport http --host 0.0.0.0 --port 8080
```

### Docker Development
```bash
# Build development image
docker build -t twitch-mcp:dev .

# Run with environment file
docker run --env-file .env -p 8080:8080 twitch-mcp:dev

# Development with compose
docker compose up --build

# Automation mode
docker compose --profile automation up --build
```

### Production Deployment

**Railway (Recommended):**
1. Fork this repository
2. Connect to Railway
3. Set environment variables
4. Deploy automatically

**Manual Docker:**
```bash
# Production build
docker build -t twitch-mcp:prod .

# Run production container
docker run -d \
  --name twitch-mcp \
  -p 8080:8080 \
  -e TWITCH_CLIENT_ID=your_id \
  -e AUTOMATION_MODE=false \
  --restart unless-stopped \
  twitch-mcp:prod
```

### Technology Stack
- **FastMCP 2.0** - Latest MCP framework with all modern features
- **OpenAPI Generation** - Automatic tool creation from Twitch API spec
- **Route Maps** - Intelligent filtering and categorization
- **Tool Transformations** - Enhanced UX and better descriptions
- **Python 3.12+** - Modern Python with type hints
- **uv** - Ultra-fast Python package manager
- **Docker** - Containerized deployment
- **Railway** - Cloud deployment platform

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

## 🆘 Support

- 📖 **Documentation**: See examples above
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-twitch/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/mcp-twitch/discussions)

---

**⭐ Star this repository if it helps you build amazing Twitch integrations!**