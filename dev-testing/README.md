# Dev Testing Environment

> Isolated Docker environment for testing GUI (Pygame) and Blackjack-API components

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac/Windows)
- Or Docker + Docker Compose (Linux)

### 3-Step Setup

1. **Build the images**:
   ```bash
   make build
   ```

2. **Start the services**:
   ```bash
   make up
   ```

3. **Access the GUI**:
   - **Browser**: http://localhost:6080/vnc.html (click Connect, password: `casino123`)
   - **VNC Client**: `vnc://localhost:5900` (password: `casino123`)

4. **Test the API**:
   ```bash
   make test-api
   # Or manually:
   curl http://localhost:8000/
   ```

---

## What's Included

### Services

| Service | Description | Access |
|---------|-------------|--------|
| **blackjack-api** | FastAPI backend with in-memory game state | http://localhost:8000 |
| **gui** | Pygame application with VNC display | http://localhost:6080/vnc.html |

### Architecture

```
┌────────────────────────────────────────┐
│       Developer Machine                │
│                                        │
│  Browser (http://localhost:6080)      │
│        │                               │
│        ▼                               │
│  ┌─────────────────────────────────┐  │
│  │  Docker Network                 │  │
│  │                                 │  │
│  │  ┌─────────────────────────┐    │  │
│  │  │  GUI Container          │    │  │
│  │  │  - Xvfb (display)       │    │  │
│  │  │  - VNC Server (5900)    │    │  │
│  │  │  - noVNC (6080)         │    │  │
│  │  │  - Pygame App           │    │  │
│  │  └──────────┬──────────────┘    │  │
│  │             │ HTTP               │  │
│  │  ┌──────────▼──────────────┐    │  │
│  │  │  API Container          │    │  │
│  │  │  - FastAPI (8000)       │    │  │
│  │  └─────────────────────────┘    │  │
│  └─────────────────────────────────┘  │
└────────────────────────────────────────┘
```

---

## Available Commands

Run `make help` to see all commands. Common ones:

```bash
make build       # Build Docker images
make up          # Start all services
make down        # Stop all services
make restart     # Restart services
make logs        # View all logs
make logs-api    # View API logs only
make logs-gui    # View GUI logs only
make test-api    # Test API endpoints
make vnc         # Show VNC connection info
make shell-api   # Get shell in API container
make shell-gui   # Get shell in GUI container
make clean       # Remove everything
```

---

## Using the GUI

### Browser (Recommended)
1. Open http://localhost:6080/vnc.html
2. Click "Connect"
3. Enter password: `casino123`
4. You'll see the Pygame window fullscreen (1920x1080)

### VNC Client

**macOS**:
```bash
open vnc://localhost:5900
# Password: casino123
```

**Windows**:
1. Install [RealVNC Viewer](https://www.realvnc.com/en/connect/download/viewer/)
2. Connect to `localhost:5900`
3. Enter password: `casino123`

**Linux**:
```bash
vncviewer localhost:5900
# Password: casino123
```

---

## API Endpoints

### Base URL
`http://localhost:8000`

### Interactive Docs
http://localhost:8000/docs

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/blackjack/start` | Start new game |
| POST | `/blackjack/hit` | Draw a card |
| POST | `/blackjack/stand` | End turn |
| GET | `/blackjack/state` | Get game state |

### Example

```bash
# Start a game with $10 bet
curl -X POST http://localhost:8000/blackjack/start \
  -H "Content-Type: application/json" \
  -d '{"bet": 10}'

# Hit (draw a card)
curl -X POST http://localhost:8000/blackjack/hit

# Stand (end turn)
curl -X POST http://localhost:8000/blackjack/stand

# Get current state
curl http://localhost:8000/blackjack/state
```

---

## Troubleshooting

### GUI not showing

**Check if container is running**:
```bash
make status
# Or:
docker compose ps
```

**Check GUI logs**:
```bash
make logs-gui
```

**Restart the GUI**:
```bash
docker compose restart gui
```

### API not responding

**Check API health**:
```bash
curl http://localhost:8000/
```

**Check API logs**:
```bash
make logs-api
```

**Shell into container**:
```bash
make shell-api
# Inside container:
curl localhost:8000/
```

### Port already in use

**Find what's using the port** (macOS/Linux):
```bash
lsof -i :8000  # Check API port
lsof -i :6080  # Check noVNC port
```

**Windows**:
```powershell
netstat -ano | findstr :8000
```

**Solution**: Stop the conflicting service or change ports in `docker-compose.yml`

### VNC password not working

The password is hardcoded as `casino123`. If it's not working:

1. Rebuild the GUI container:
   ```bash
   docker compose build gui
   docker compose up -d gui
   ```

2. Check supervisor logs:
   ```bash
   docker compose exec gui cat /var/log/supervisor/x11vnc.log
   ```

---

## Project Structure

```
dev-testing/
├── README.md                 # This file
├── Makefile                  # Easy commands
├── docker-compose.yml        # Service orchestration
├── .dockerignore             # Build exclusions
├── blackjack-api/
│   ├── Dockerfile            # API container definition
│   └── requirements.txt      # Python dependencies
└── gui/
    ├── Dockerfile            # GUI + VNC container
    ├── requirements.txt      # Python dependencies
    ├── supervisord.conf      # Process manager
    └── entrypoint.sh         # Startup script
```

---

## Development Workflow

### Making Changes

1. **Edit source files** in `/gui` or `/blackjack-api`
2. **Changes are live-reloaded** (no rebuild needed!)
   - API: Uvicorn auto-reloads on file changes
   - GUI: Restart the app in VNC or restart container
3. **Test your changes** via VNC or API calls

### Viewing Logs

```bash
# All logs
make logs

# API only
make logs-api

# GUI only
make logs-gui

# Follow logs (auto-update)
docker compose logs -f
```

### Debugging

**Get a shell in the API container**:
```bash
make shell-api
# Now you can run Python, check files, etc.
```

**Get a shell in the GUI container**:
```bash
make shell-gui
# Check Xvfb, VNC processes, etc.
ps aux  # See running processes
```

---

## OS-Specific Notes

### macOS
- Docker Desktop required
- Built-in VNC client: `open vnc://localhost:5900`
- Browser access works perfectly
- Performance: Excellent

### Windows
- Docker Desktop with WSL2 required
- No built-in VNC client (install RealVNC Viewer)
- Browser access works perfectly
- Performance: Good (WSL2 improves it significantly)

### Linux
- Docker and Docker Compose required
- Many VNC clients available (Remmina, Vinagre, etc.)
- Browser access works perfectly
- Performance: Excellent

---

## Security Notes

This is a DEVELOPMENT environment only

- VNC password is hardcoded (`casino123`)
- No HTTPS/TLS
- Ports exposed to localhost only
- **DO NOT use in production**

---

## Next Steps

After testing in this environment:

1. **Integration**: Connect GUI to the main backend (Go API)
2. **Database**: Add PostgreSQL for persistent state
3. **Authentication**: Integrate with user auth system
4. **Testing**: Add automated tests (pytest, etc.)
5. **CI/CD**: Integrate with GitHub Actions

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pygame Documentation](https://www.pygame.org/docs/)
- [VNC Protocol](https://en.wikipedia.org/wiki/Virtual_Network_Computing)

---

## Known Issues

1. **GUI fullscreen**: Pygame runs in fullscreen mode. To exit, use the exit button in the UI.
2. **Volume permissions**: On some systems, you may need to adjust file permissions.
3. **Performance**: VNC adds slight latency. For performance-critical testing, consider running GUI natively.

---

## Need Help?

- Check logs: `make logs`
- Test API: `make test-api`
- View status: `make status`
- Clean rebuild: `make clean && make build && make up`

---

**Happy Testing!**
