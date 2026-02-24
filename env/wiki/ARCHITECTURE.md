# Architecture: How Public Access Works

This document explains the technical architecture behind the public server exposure system.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR COMPUTER                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Wiki Theme 1 │  │ Wiki Theme 2 │  │ Wiki Theme 3 │         │
│  │ Port 5000    │  │ Port 5001    │  │ Port 5002    │  ...    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                     │
│         ┌──────────────────▼──────────────────┐                 │
│         │   expose_servers.sh (this script)   │                 │
│         │   Creates tunnels using:             │                 │
│         │   - cloudflared OR                   │                 │
│         │   - ngrok                            │                 │
│         └──────────────────┬──────────────────┘                 │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │ Secure Tunnel
                             │ (WebSocket over HTTPS)
                             │
                    ┌────────▼────────┐
                    │   Tunnel        │
                    │   Service       │
                    │   (Cloudflare/  │
                    │    ngrok)       │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
      https://abc-1.      https://def-2.   https://ghi-3.
      trycloudflare.com   trycloudflare.com trycloudflare.com
            │                │                │
            │                │                │
            ▼                ▼                ▼
      ┌──────────┐     ┌──────────┐     ┌──────────┐
      │  User    │     │  User    │     │  User    │
      │  Device  │     │  Device  │     │  Device  │
      │  (Phone) │     │ (Tablet) │     │ (Laptop) │
      └──────────┘     └──────────┘     └──────────┘
```

## Component Breakdown

### 1. Wiki Servers (`wiki_app.py`)

**What they do:**
- Serve Wikipedia-like content
- Run on Flask (Python web framework)
- Each theme = separate server instance

**Where they run:**
- Locally on your computer
- Default ports: 5000, 5001, 5002, 5003, 5004, 5005
- Accessible at: `http://localhost:PORT`

**How they start:**
```python
# Automatically started by expose_servers.sh if not running
python3 wiki_app.py -all --port=5000
```

### 2. Tunnel Creation (`expose_servers.sh`)

**What it does:**
- Detects running servers (or starts them)
- Creates secure tunnels for each server
- Generates public URLs
- Updates `.env` file with URLs

**Flow:**
```bash
./expose_servers.sh -all
  ↓
Check if servers running
  ↓
Start servers if needed
  ↓
Create tunnel for each server
  ↓
Get public URLs
  ↓
Update .env file
  ↓
Display URLs to user
  ↓
Keep tunnels alive (wait for Ctrl+C)
```

### 3. Tunnel Services

#### Option A: Cloudflared (Default)

```
Your Server (localhost:5000)
        ↓
cloudflared client (running on your computer)
        ↓ WebSocket connection
Cloudflare Edge Network
        ↓ HTTPS
Public URL (https://abc.trycloudflare.com)
        ↓
Internet users
```

**How it works:**
1. `cloudflared` creates outbound connection to Cloudflare
2. Cloudflare assigns random public URL
3. Incoming requests go to Cloudflare edge
4. Cloudflare forwards to your `cloudflared` client
5. `cloudflared` forwards to your localhost server

**Security:**
- All traffic encrypted (TLS/HTTPS)
- No inbound firewall rules needed
- No port forwarding needed
- Your IP address hidden

#### Option B: ngrok

```
Your Server (localhost:5000)
        ↓
ngrok client (running on your computer)
        ↓ Secure tunnel
ngrok Cloud
        ↓ HTTPS
Public URL (https://xyz.ngrok-free.app)
        ↓
Internet users
```

**How it works:**
1. `ngrok` creates outbound connection to ngrok servers
2. ngrok assigns random (or custom) public URL
3. Incoming requests go to ngrok cloud
4. ngrok forwards to your client
5. Client forwards to localhost server

**Additional features:**
- Web interface at `http://localhost:4040`
- Request inspection
- Replay requests
- Custom domains (paid)

### 4. `.env` File Integration

**Location:** `data_annotation/.env`

**Purpose:** Store public URLs for use in other scripts

**Format:**
```bash
WIKI1=https://url-for-theme-1.trycloudflare.com
WIKI2=https://url-for-theme-2.trycloudflare.com
...
```

**Usage in other scripts:**
```bash
# In collect_batch.sh
source .env
echo "Collecting from $WIKI1"
```

## Request Flow (Detailed)

### Step-by-Step: User Accesses Your Wiki

```
1. User's Browser
   │ Opens: https://abc-123.trycloudflare.com
   │
   ▼
2. DNS Resolution
   │ Resolves to Cloudflare IP
   │
   ▼
3. Cloudflare Edge Server (nearest to user)
   │ Receives HTTPS request
   │ Terminates TLS
   │
   ▼
4. Cloudflare Core
   │ Looks up tunnel ID
   │ Finds your cloudflared connection
   │
   ▼
5. Your cloudflared Client
   │ Receives forwarded request
   │ Forwards to localhost:5000
   │
   ▼
6. Your Wiki Server (Flask)
   │ Processes request
   │ Generates HTML
   │ Returns response
   │
   ▼
7. cloudflared Client
   │ Receives response
   │ Forwards to Cloudflare
   │
   ▼
8. Cloudflare Edge
   │ Encrypts with TLS
   │ Sends to user
   │
   ▼
9. User's Browser
   │ Displays wiki page
   └─ ✓ Complete!
```

**Total time:** Usually 100-500ms (depending on location)

## Network Topology

### Traditional Port Forwarding (NOT used)

```
Internet
   ↓
Your Router (NAT)
   ↓ Port forward 5000 → 192.168.1.100:5000
Your Computer (192.168.1.100)
   ↓
Wiki Server (localhost:5000)

❌ Problems:
- Exposes your public IP
- Requires router configuration
- Firewall rules needed
- Security risks
- No HTTPS by default
```

### Tunnel Approach (What we use)

```
Internet
   ↓
Cloudflare/ngrok (their IP)
   ↓ Existing tunnel connection
Your Computer
   ↓
Wiki Server (localhost:5000)

✅ Benefits:
- Your IP hidden
- No router config
- No firewall changes
- HTTPS automatic
- Secure by default
```

## Security Model

### Defense Layers

1. **URL Obscurity**
   - Random, hard-to-guess URLs
   - No directory listing

2. **HTTPS Encryption**
   - All traffic encrypted
   - TLS 1.2/1.3

3. **Outbound-Only Connection**
   - No inbound ports opened
   - All connections initiated by you

4. **Temporary URLs**
   - URLs expire when tunnel stops
   - New URLs each session

5. **Rate Limiting** (by tunnel provider)
   - DDoS protection
   - Abuse prevention

### What's Exposed

**✅ Intended exposure:**
- Wiki page content
- Search functionality
- Article navigation

**❌ NOT exposed:**
- Your file system
- Other services on your computer
- Your local network
- Your IP address

## Scalability

### Single Theme

```
1 Server (Port 5000)
   ↓
1 Tunnel
   ↓
1 Public URL
   ↓
✅ Can handle: ~100 concurrent users (limited by your hardware)
```

### All Themes

```
6 Servers (Ports 5000-5005)
   ↓
6 Tunnels
   ↓
6 Public URLs
   ↓
✅ Can handle: ~100 users per theme (600 total)
```

**Bottlenecks:**
1. Your computer's CPU/RAM
2. Your internet upload speed
3. Flask's single-threaded nature

**Optimization tips:**
- Use production WSGI server (gunicorn, waitress)
- Increase worker processes
- Enable caching
- Use CDN for static assets

## Data Flow: Script Execution

### Phase 1: Server Check & Start

```
expose_servers.sh
   ↓
Check if servers running (nc -z localhost PORT)
   ↓
If not running → python3 wiki_app.py -all --port=5000
   ↓
Wait for servers to respond (up to 60 seconds each)
   ↓
✓ Servers ready
```

### Phase 2: Tunnel Creation

```
For each theme:
   ↓
Start cloudflared tunnel --url http://localhost:PORT
   ↓
Capture output to temp file
   ↓
Wait for URL in output (up to 30 seconds)
   ↓
Extract URL (grep for https://*.trycloudflare.com)
   ↓
Store URL in array
   ↓
✓ Tunnel ready
```

### Phase 3: Configuration Update

```
Read existing .env file (if exists)
   ↓
Backup to .env.backup
   ↓
Preserve non-WIKI variables
   ↓
Add/update WIKI* variables with new URLs
   ↓
Write to .env
   ↓
✓ Configuration updated
```

### Phase 4: Monitoring & Cleanup

```
Display all URLs to user
   ↓
Wait for user interrupt (Ctrl+C)
   ↓
On interrupt or exit:
   ↓
Kill all cloudflared processes
   ↓
Remove temp files
   ↓
✓ Clean shutdown
```

## File Structure

```
TimeWarp/
├── env/wiki/
│   ├── wiki_app.py                    # Flask server
│   ├── expose_servers.sh              # Main script (THIS!)
│   ├── start_wiki.sh                  # Local-only server start
│   ├── README_EXPOSURE.md             # Overview
│   ├── QUICK_START.md                 # Quick guide
│   ├── ACCESSING_SERVERS.md           # URL guide
│   ├── EXPOSE_SERVERS_README.md       # Detailed docs
│   └── ARCHITECTURE.md                # This file
│
└── data_annotation/
    ├── .env                           # Generated URLs (gitignored)
    ├── .env.backup                    # Backup (auto-created)
    └── collect_batch.sh               # Uses URLs from .env
```

## Environment Variables

### Generated by Script

```bash
WIKI1=https://theme-1-url.trycloudflare.com
WIKI2=https://theme-2-url.trycloudflare.com
WIKI3=https://theme-3-url.trycloudflare.com
WIKI4=https://theme-4-url.trycloudflare.com
WIKI5=https://theme-5-url.trycloudflare.com
WIKI6=https://theme-6-url.trycloudflare.com
```

### Used by Collect Script

```bash
#!/bin/bash
source .env

# Access URLs
echo "Theme 1: $WIKI1"
echo "Theme 2: $WIKI2"
# etc...
```

## Process Management

### Process Tree

```
bash (your terminal)
  └─ expose_servers.sh
      ├─ python3 wiki_app.py -all --port=5000
      │   ├─ python3 wiki_app.py -1 --port=5000  (child process)
      │   ├─ python3 wiki_app.py -2 --port=5001  (child process)
      │   ├─ python3 wiki_app.py -3 --port=5002  (child process)
      │   ├─ python3 wiki_app.py -4 --port=5003  (child process)
      │   ├─ python3 wiki_app.py -5 --port=5004  (child process)
      │   └─ python3 wiki_app.py -6 --port=5005  (child process)
      │
      ├─ cloudflared tunnel --url http://localhost:5000 &
      ├─ cloudflared tunnel --url http://localhost:5001 &
      ├─ cloudflared tunnel --url http://localhost:5002 &
      ├─ cloudflared tunnel --url http://localhost:5003 &
      ├─ cloudflared tunnel --url http://localhost:5004 &
      └─ cloudflared tunnel --url http://localhost:5005 &
```

### Signal Handling

```bash
# Script sets up trap
trap cleanup EXIT INT TERM

cleanup() {
    # Kill all cloudflared processes
    for pid in "${TUNNEL_PIDS[@]}"; do
        kill $pid 2>/dev/null || true
    done
    # Note: Wiki servers keep running
}
```

## Performance Characteristics

### Latency

- **Local access:** 1-10ms
- **Tunnel overhead:** 50-200ms
- **Total (remote user):** 100-500ms

### Bandwidth

- **Upload:** Limited by your internet
- **Download:** Limited by user's internet
- **Typical page:** 50-500KB

### Concurrent Users

- **Per theme:** ~50-100 users (Flask limitation)
- **All themes:** ~300-600 users (distributed)

### Resource Usage

```
CPU: ~5-10% per server (idle)
     ~20-30% per server (active)

RAM: ~50-100MB per server
     ~300-600MB total (6 servers)

Network: ~10KB/s per idle tunnel
         ~100KB-1MB/s per active user
```

## Comparison Matrix

| Feature | Cloudflared | ngrok | Port Forwarding |
|---------|------------|-------|-----------------|
| Setup | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐ Medium | ⭐⭐ Hard |
| Cost | Free | Free/Paid | Free |
| Security | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐ Poor |
| Speed | ⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Fastest |
| Tunnels | ∞ Unlimited | 1-3 (free) | ∞ Unlimited |
| Custom URL | ❌ No | ✅ Yes (paid) | ✅ Yes |
| Monitoring | ⭐⭐ Basic | ⭐⭐⭐⭐⭐ Excellent | ⭐ None |

## Technical Specifications

### Supported Protocols
- HTTP/1.1
- HTTP/2
- WebSocket
- HTTPS/TLS 1.2+

### URL Format
- Cloudflared: `https://[random].trycloudflare.com`
- ngrok: `https://[random].ngrok-free.app`

### Port Range
- Default: 5000-5005
- Configurable: any free port

### Browser Compatibility
- ✅ Chrome/Edge
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## Future Enhancements

Potential improvements:

1. **Docker Integration**
   ```bash
   # Run entire stack in containers
   docker-compose up -d
   ```

2. **Load Balancing**
   ```bash
   # Multiple servers per theme
   ./expose_servers.sh -1 --replicas 3
   ```

3. **Custom Domains**
   ```bash
   # Use your own domain
   ./expose_servers.sh -1 --domain wiki1.yourdomain.com
   ```

4. **Monitoring Dashboard**
   ```bash
   # Web UI for monitoring
   http://localhost:8080/dashboard
   ```

5. **Automatic Restart**
   ```bash
   # Restart on crash
   ./expose_servers.sh -1 --watch
   ```

---

## Summary

This architecture provides:

✅ **Secure** public access without exposing your network  
✅ **Simple** one-command deployment  
✅ **Scalable** support for multiple themes  
✅ **Flexible** choice of tunneling providers  
✅ **Integrated** automatic .env updates  

The system elegantly solves the problem of making local development servers publicly accessible while maintaining security and ease of use.


