# 🎮 MCP Twitch Server

Professional Model Context Protocol server for Twitch Helix API with 141 tools and intelligent filtering.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

## 🚀 Features

- **141 Tools** from real Twitch Helix API
- **Smart Filtering** by 30+ categories 
- **FastMCP Framework** with all modern features
- **Railway Ready** - One-click deploy
- **Docker Support** for easy deployment
- **Multiple Transports** - HTTP, STDIO, SSE

## 📦 Quick Deploy

### Railway (Recommended)

1. Click "Deploy on Railway" button above
2. Set environment variables:
   ```
   TWITCH_CLIENT_ID=your_client_id
   TWITCH_ACCESS_TOKEN=your_token (optional)
   ```
3. Deploy! 🚀

### Docker

```bash
# Build
docker build -t mcp-twitch .

# Run
docker run -p 8080:8080 \
  -e TWITCH_CLIENT_ID=your_client_id \
  mcp-twitch
```

### Local Development

```bash
# Install
pip install -r requirements.txt

# Configure
cp example.env .env
# Edit .env with your Twitch API keys

# Run
python mcp_twitch_server.py
```

## 🔑 API Keys Setup

1. **Get Client ID**:
   - Go to https://dev.twitch.tv/console/apps
   - Create new application
   - Copy Client ID

2. **Get Access Token** (optional):
   - Visit https://twitchtokengenerator.com
   - Select required scopes
   - Copy token

## 🏷️ Available Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| `Channels` | 6 | Channel management |
| `Users` | 8 | User information |
| `Chat` | 15 | Chat interactions |
| `Moderation` | 20 | Moderation tools |
| `Streams` | 6 | Live stream data |
| `Clips` | 2 | Video clips |
| `Games` | 2 | Game information |
| And 23+ more... | 141 total | Full Twitch API |

## 🛠️ Usage Examples

### All Tools
```bash
python mcp_twitch_server.py
```

### HTTP Server
```bash
python mcp_twitch_server.py --transport http --port 8080
```

### Filtered by Category
```bash
python mcp_twitch_server.py --include-tags channels users streams
```

### Without Moderation
```bash
python mcp_twitch_server.py --exclude-tags moderation
```

## 🔗 Integration

### Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "twitch": {
      "command": "python",
      "args": ["/path/to/mcp_twitch_server.py"],
      "env": {
        "TWITCH_CLIENT_ID": "your_client_id"
      }
    }
  }
}
```

### HTTP API
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "get_top_games", "arguments": {"first": 5}}}'
```

## 📊 API Limits

| Token Type | Rate Limit | Usage |
|------------|------------|-------|
| No Token | 30/min | Public data only |
| App Token | 800/min | Recommended |
| User Token | 120/min/user | Personal data |

## 🆘 Support

- **Documentation**: See `SETUP_GUIDE.md` and `TWITCH_API_SETUP.md`  
- **Issues**: Create GitHub issue
- **Railway Deploy**: One-click deployment ready

## 📄 License

MIT License - see LICENSE file for details.

---

**Ready for production deployment with Railway! 🚂**
