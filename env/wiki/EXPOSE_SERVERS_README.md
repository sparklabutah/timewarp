# Wiki Server Exposure Guide

This guide explains how to make your wiki servers publicly accessible from anywhere on the internet.

## Quick Start

### Option 1: Expose a Single Theme (Recommended for Testing)

```bash
# Expose only theme 1
./expose_servers.sh -1

# Expose only theme 3
./expose_servers.sh -3
```

### Option 2: Expose All Themes (For Full Data Collection)

```bash
# Expose all 6 themes
./expose_servers.sh -all
```

## Installation

### Step 1: Install Cloudflared (Recommended)

**For Windows WSL:**
```bash
wget https://github.com/cloudflare/cloudflaredeleases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

**For macOS:**
```bash
brew install cloudflared
```

**For Linux:**
```bash
# Debian/Ubuntu
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Step 2: Make Script Executable

```bash
cd "E:\Projects - GitHub\TimeWarp\env\wiki"
chmod +x expose_servers.sh
```

## Usage Examples

### Basic Usage

```bash
# Expose theme 1 (uses cloudflared by default)
./expose_servers.sh -1

# Expose theme 2
./expose_servers.sh -2

# Expose all themes
./expose_servers.sh -all
```

### Advanced Usage

```bash
# Use ngrok instead of cloudflared
./expose_servers.sh -3 --method ngrok

# Start from a different port
./expose_servers.sh -1 --port 6000

# Expose all themes with ngrok
./expose_servers.sh -all --method ngrok

# Expose multiple specific themes (run multiple times)
./expose_servers.sh -1 &
./expose_servers.sh -3 &
./expose_servers.sh -5 &
```

## What Happens When You Run It

1. **Server Check**: Script checks if wiki servers are running
2. **Server Start**: If not running, starts the required theme(s)
3. **Tunnel Creation**: Creates secure tunnels to expose servers
4. **URL Display**: Shows public URLs for each theme
5. **`.env` Update**: Automatically updates your `.env` file with URLs

### Example Output

```
============================================================
Wiki Server Public Exposure Script
============================================================
Method: cloudflared
Starting port: 5000
Themes: 1
Working directory: /path/to/TimeWarp/env/wiki
============================================================

Starting wiki servers...
  Waiting for server on port 5000... ✓ Ready

✓ Wiki servers are running

============================================================
Exposing servers with Cloudflare Tunnel
============================================================

Starting tunnel for Theme 1 (port 5000)...
  Waiting for tunnel URL... ✓

Public URLs for wiki servers:
============================================================
Theme 1 (port 5000): https://abc-def-123.trycloudflare.com
============================================================

Creating/updating .env file...
  ✓ Updated ../../data_annotation/.env

✓ All tunnels are running!

Press Ctrl+C to stop all tunnels and servers
```

## Methods Comparison

### Cloudflared (Default) ✅ RECOMMENDED

**Pros:**
- ✅ Free, unlimited tunnels
- ✅ No account required
- ✅ Fast setup
- ✅ Stable connections
- ✅ No rate limits

**Cons:**
- ⚠️ Random URLs each time (can't customize)

**Install:**
```bash
# See installation section above
```

### ngrok

**Pros:**
- ✅ Custom subdomains (paid)
- ✅ Web dashboard at localhost:4040
- ✅ Request inspection

**Cons:**
- ⚠️ Free tier limited to 1-3 tunnels
- ⚠️ Requires account signup
- ⚠️ Must configure authtoken

**Install & Setup:**
```bash
# 1. Download from https://ngrok.com/download
# 2. Sign up at https://ngrok.com
# 3. Configure authtoken
ngrok config add-authtoken YOUR_TOKEN_HERE
```

## Accessing Your Servers

After running the script, you'll get URLs like:

- `https://abc-def-123.trycloudflare.com` (Theme 1)
- `https://ghi-jkl-456.trycloudflare.com` (Theme 2)
- etc.

**These URLs can be:**
- ✅ Accessed from anywhere in the world
- ✅ Shared with anyone
- ✅ Used in your data collection scripts
- ✅ Opened on any device (phone, tablet, etc.)

## Integration with Data Collection

The script automatically updates your `.env` file:

```bash
# Your .env file will look like:
WIKI1=https://abc-def-123.trycloudflare.com
WIKI2=https://ghi-jkl-456.trycloudflare.com
WIKI3=https://mno-pqr-789.trycloudflare.com
...
```

Now you can run your data collection script:

```bash
cd ../../data_annotation
./collect_batch.sh wiki 1  # Uses WIKI1 from .env
./collect_batch.sh wiki all # Uses all WIKI* URLs
```

## Troubleshooting

### Problem: "cloudflared not found"

**Solution:**
```bash
# Check if installed
which cloudflared

# If not, install it (see Installation section)
```

### Problem: "Server failed to start"

**Solution:**
```bash
# Check if port is already in use
netstat -tuln | grep 5000

# Kill existing process
kill $(lsof -t -i:5000)

# Or use a different port
./expose_servers.sh -1 --port 6000
```

### Problem: "Tunnel timeout"

**Solution:**
- Check your internet connection
- Try again (sometimes cloudflare servers are slow)
- Try ngrok instead: `./expose_servers.sh -1 --method ngrok`

### Problem: Can't access the public URL

**Solution:**
- Wait 30 seconds after tunnel creation
- Check if server is running: `curl http://localhost:5000`
- Try opening URL in incognito/private browser
- Check tunnel logs in the terminal

## Stopping the Servers

Press `Ctrl+C` in the terminal where the script is running. This will:
1. Stop all tunnels
2. Clean up temporary files
3. Keep wiki servers running (you can stop them separately if needed)

## Security Notes

- 🔒 URLs are random and hard to guess
- 🔒 Tunnels use HTTPS encryption
- ⚠️ URLs are public - anyone with the URL can access
- ⚠️ Don't share URLs with untrusted parties
- ⚠️ Tunnels expire when script stops

## FAQ

**Q: Can I use the same URLs later?**
A: No, cloudflared generates new URLs each time. For persistent URLs, use ngrok paid plan.

**Q: How many themes can I expose at once?**
A: All 6! Just use `-all` flag.

**Q: Do I need to keep the terminal open?**
A: Yes, closing the terminal will stop the tunnels.

**Q: Can I run this in the background?**
A: Yes, use `nohup ./expose_servers.sh -all &` but you'll need to kill processes manually.

**Q: What if I want to expose news/webshop/homepage servers?**
A: Similar scripts can be created for other environments. This one is specific to wiki.

## Advanced: Custom Port Ranges

```bash
# Start theme 1 on port 8000
./expose_servers.sh -1 --port 8000

# Start all themes from port 9000
./expose_servers.sh -all --port 9000
# This creates: 9000, 9001, 9002, 9003, 9004, 9005
```

## Support

If you encounter issues:
1. Check this README
2. Run with `--help` flag: `./expose_servers.sh --help`
3. Check the terminal output for error messages
4. Verify cloudflared/ngrok installation

---

Happy data collecting! 🚀


