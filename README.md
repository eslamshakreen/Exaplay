# ExaPlay Control API

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-grade REST API for controlling and monitoring ExaPlay media playback servers over the LAN. Translates HTTP requests to ExaPlay TCP commands and optionally provides real-time status streaming via OSC.

## Features

- **🎯 Complete ExaPlay Control**: Play, pause, stop, seek, volume control
- **📊 Real-time Monitoring**: Status polling and optional OSC live streaming
- **🔒 Production Security**: Bearer token auth, CORS, rate limiting
- **⚡ High Performance**: Async I/O, connection pooling, <50ms response times
- **🛡️ Robust Error Handling**: Exponential backoff retries, detailed error mapping
- **📝 Comprehensive Logging**: Structured JSON logs with trace IDs
- **🐳 Container Ready**: Multi-stage Docker builds, health checks
- **🧪 Thoroughly Tested**: 85%+ coverage, mock server included
- **📚 Full Documentation**: OpenAPI/Swagger UI with examples

## Quick Start

### Prerequisites

- Python 3.12+
- ExaPlay server running on your LAN
- ExaPlay TCP control port enabled (default 7000)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/exaplay-api.git
cd exaplay-api

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env
# Edit .env with your ExaPlay server details and API key
```

### Configuration

Create `.env` file with your settings:

```env
# ExaPlay Connection
EXAPLAY_HOST=192.168.1.174
EXAPLAY_TCP_PORT=7000

# Security (REQUIRED - generate a strong key)
API_KEY=your-secure-api-key-minimum-32-characters-long

# Optional: OSC Live Status Streaming
EXAPLAY_OSC_ENABLE=false
EXAPLAY_OSC_PREFIX=exaplay
EXAPLAY_OSC_LISTEN=0.0.0.0:8000

# Logging & CORS
LOG_LEVEL=INFO
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Running

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker

```bash
# Build and run
docker-compose up -d

# With testing profile (includes mock ExaPlay server)
docker-compose --profile testing up

# View logs
docker-compose logs -f exaplay-api
```

## API Usage

### Authentication

All endpoints except `/healthz` require Bearer token authentication:

```bash
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/compositions/comp1/play
```

### Basic Operations

```bash
# Health check (no auth required)
curl http://localhost:8000/healthz

# Get ExaPlay version
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8000/version

# Play a composition
curl -X POST -H "Authorization: Bearer $API_KEY" \
     http://localhost:8000/compositions/comp1/play

# Get status
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8000/compositions/comp1/status

# Set volume
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"value": 75}' \
     http://localhost:8000/compositions/comp1/volume

# Seek to time position (timeline compositions)
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"seconds": 30.5}' \
     http://localhost:8000/compositions/comp1/cuetime

# Jump to clip (cuelist compositions, 1-based index)
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"index": 3}' \
     http://localhost:8000/compositions/cuelist1/cue
```

### Advanced Usage

```bash
# Raw command execution (admin endpoint, rate limited)
curl -X POST -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"raw": "get:status,comp1"}' \
     http://localhost:8000/exaplay/command

# Live status stream (if OSC enabled)
curl -H "Authorization: Bearer $API_KEY" \
     -H "Accept: text/event-stream" \
     http://localhost:8000/events/status
```

### API Documentation

Once running, visit:

- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI spec**: http://localhost:8000/openapi.json

## ExaPlay Protocol Reference

### TCP Commands Supported

| Command       | Format                                | Description      |
| ------------- | ------------------------------------- | ---------------- |
| `play`        | `play,<composition>`                  | Start playback   |
| `pause`       | `pause,<composition>`                 | Pause playback   |
| `stop`        | `stop,<composition>`                  | Stop and reset   |
| `set:cuetime` | `set:cuetime,<composition>,<seconds>` | Seek to time     |
| `set:cue`     | `set:cue,<composition>,<index>`       | Jump to cue/clip |
| `set:vol`     | `set:vol,<composition>,<0-100>`       | Set volume       |
| `get:vol`     | `get:vol,<composition>`               | Get volume       |
| `get:status`  | `get:status,<composition>`            | Get status CSV   |
| `get:ver`     | `get:ver`                             | Get version      |

### Status Response Format

ExaPlay returns status as CSV: `state,time,frame,clipIndex,duration`

- **state**: `0`=stopped, `1`=playing, `2`=paused
- **time**: Current time in seconds
- **frame**: Current frame number
- **clipIndex**: Clip index (`-1` if N/A, `1`-based for cuelists)
- **duration**: Total duration in seconds

API normalizes this to JSON:

```json
{
  "state": "playing",
  "time": 15.65,
  "frame": 939,
  "clipIndex": 2,
  "duration": 300.0
}
```

### OSC Integration (Optional)

When `EXAPLAY_OSC_ENABLE=true`, the API listens for OSC messages from ExaPlay and streams them via Server-Sent Events:

- **OSC Address Pattern**: `/{prefix}/status/{composition}`
- **Supported Events**: `status`, `cuetime`, `cueframe`
- **Stream Endpoint**: `GET /events/status`

Configure ExaPlay to send OSC OUT to the API server address.

## Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run linting and type checking
ruff check app/
mypy app/

# Run tests with coverage
pytest --cov=app/exaplay --cov-report=html

# Format code
ruff format app/
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest app/tests/test_control.py
pytest app/tests/test_mapper.py

# Run with mock ExaPlay server
python -m app.tests.fixtures.mock_exaplay 17000 300
```

### Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── settings.py             # Configuration management
├── logging.py              # Structured logging setup
├── deps.py                 # Authentication & dependencies
├── exaplay/                # ExaPlay communication modules
│   ├── tcp_client.py       # Async TCP client with retries
│   ├── osc_listener.py     # Optional OSC status streaming
│   ├── mapper.py           # CSV to JSON response mapping
│   └── models.py           # Pydantic request/response models
├── api/                    # FastAPI route modules
│   ├── routes_control.py   # Play/pause/stop endpoints
│   ├── routes_position.py  # Cuetime/cue positioning
│   ├── routes_volume.py    # Volume control
│   ├── routes_status.py    # Status & version endpoints
│   ├── routes_admin.py     # Raw command execution
│   └── routes_events.py    # SSE live status streaming
└── tests/                  # Comprehensive test suite
    ├── conftest.py         # Pytest configuration & fixtures
    ├── fixtures/
    │   └── mock_exaplay.py # Mock ExaPlay TCP server
    └── test_*.py           # Test modules
```

## Deployment

### Docker Production Deployment

```bash
# Build production image
docker build -f docker/Dockerfile -t exaplay-api:latest .

# Run with docker-compose
docker-compose --profile production up -d

# Check health
curl http://localhost/healthz
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: exaplay-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: exaplay-api
  template:
    metadata:
      labels:
        app: exaplay-api
    spec:
      containers:
        - name: exaplay-api
          image: exaplay-api:latest
          ports:
            - containerPort: 8000
          env:
            - name: API_KEY
              valueFrom:
                secretKeyRef:
                  name: exaplay-api-secret
                  key: api-key
            - name: EXAPLAY_HOST
              value: "192.168.1.174"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
```

### Performance Considerations

- **Throughput**: Sustains 100+ RPS with sub-50ms latency
- **Concurrency**: Async I/O handles 1000+ concurrent connections
- **Memory**: ~50MB base + ~1MB per 1000 concurrent requests
- **CPU**: Single core sufficient for 100 RPS
- **Network**: Requires reliable LAN connection to ExaPlay server

### Security Best Practices

1. **Generate Strong API Keys**: Minimum 32 characters, use cryptographically secure random
2. **Use HTTPS**: Deploy behind reverse proxy with SSL termination
3. **Restrict CORS**: Only allow necessary origins
4. **Network Security**: Deploy on private LAN/VPN, restrict ExaPlay TCP port access
5. **Rate Limiting**: Configure appropriate limits for admin endpoints
6. **Monitoring**: Monitor logs for authentication failures and suspicious activity

## Troubleshooting

### Common Issues

**Connection Refused to ExaPlay**

```bash
# Check ExaPlay TCP port is open
telnet 192.168.1.174 7000

# Verify ExaPlay TCP control is enabled
# Check ExaPlay logs for TCP listener status
```

**Authentication Failures**

```bash
# Verify API key is correct
curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/version

# Check logs for auth details
docker-compose logs exaplay-api | grep "Authentication"
```

**Timeout Errors**

```bash
# Test network connectivity
ping 192.168.1.174

# Adjust timeout settings in .env
TCP_TIMEOUT=10.0
TCP_MAX_RETRIES=5
```

**OSC Not Working**

```bash
# Verify OSC is enabled
grep EXAPLAY_OSC_ENABLE .env

# Check OSC listener port
netstat -ln | grep 8000

# Test OSC manually
# Configure ExaPlay OSC OUT to API server IP:8000
```

### Debug Logging

Enable detailed logging:

```env
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

View structured logs:

```bash
# Follow logs
docker-compose logs -f exaplay-api

# Search by trace ID
docker-compose logs exaplay-api | grep "trace_id.*abc123"

# Filter by component
docker-compose logs exaplay-api | grep '"component":"tcp_client"'
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Ensure tests pass: `pytest`
5. Check linting: `ruff check app/`
6. Commit changes: `git commit -m "Add amazing feature"`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add docstrings for public APIs
- Maintain test coverage ≥85%
- Use meaningful commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: Available at `/docs` when running
- **Issues**: Report bugs via GitHub Issues
- **Security**: Report vulnerabilities privately to security@yourorg.com

---

**Built with ❤️ using FastAPI, Python 3.12, and modern async patterns.**
