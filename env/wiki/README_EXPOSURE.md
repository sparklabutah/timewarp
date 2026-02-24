# Wiki Server Public Exposure - Complete Guide

This directory contains scripts and documentation for making your wiki servers publicly accessible from anywhere on the internet.

## 📁 Files Overview

```
env/wiki/
├── expose_servers.sh           ← Main script (run this!)
├── QUICK_START.md              ← 5-minute quick start guide
├── ACCESSING_SERVERS.md        ← Explains URLs and how to access
├── EXPOSE_SERVERS_README.md    ← Detailed documentation
└── README_EXPOSURE.md          ← This file (overview)
```

## 🚀 Quick Start (3 Steps)

### 1. Install Cloudflared (one-time)

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

### 2. Make script executable (one-time)

```bash
chmod +x expose_servers.sh
```

### 3. Run it!

```bash
# Expose one theme
./expose_servers.sh -1

# Or expose all themes
./expose_servers.sh -all
```

## 📖 Documentation Guide

**Read these in order:**

1. **[QUICK_START.md](QUICK_START.md)** ← Start here!
   - Fastest way to get up and running
   - Basic commands
   - 5-minute read

2. **[ACCESSING_SERVERS.md](ACCESSING_SERVERS.md)** ← Understanding URLs
   - What URLs you'll get
   - How to access them
   - No IP address knowledge needed!
   - 10-minute read

3. **[EXPOSE_SERVERS_README.md](EXPOSE_SERVERS_README.md)** ← Full details
   - All options and flags
   - Troubleshooting
   - Advanced usage
   - 20-minute read

## 🎯 What This Does

**Problem:** Your wiki servers run on `localhost` (only accessible from your computer)

**Solution:** This script creates secure tunnels that give you public HTTPS URLs

**Result:** Anyone with the URL can access your wikis from anywhere!

### Visual Example

```
BEFORE (Local Only)
┌─────────────────┐
│  Your Computer  │
│                 │
│  localhost:5000 │  ← Only you can access
└─────────────────┘


AFTER (Public Access)
┌─────────────────┐
│  Your Computer  │
│                 │
│  localhost:5000 │◄────┐
└─────────────────┘     │
                        │ Secure Tunnel
                        │
                   ┌────▼────┐
                   │Cloudflare│
                   └────┬────┘
                        │
                        ▼
        https://abc-123.trycloudflare.com  ← Anyone can access!
```

## 💡 Common Use Cases

### Use Case 1: Testing on Multiple Devices

```bash
./expose_servers.sh -1
# Get URL: https://test-abc.trycloudflare.com
# Open on: computer, phone, tablet ✅
```

### Use Case 2: Data Collection

```bash
./expose_servers.sh -all
# Gets 6 URLs (one per theme)
# Auto-saved to .env file
# Use with: cd ../../data_annotation && ./collect_batch.sh wiki all
```

### Use Case 3: Collaboration

```bash
./expose_servers.sh -all
# Share URLs with team members
# Everyone can access simultaneously ✅
```

## 🎮 Command Reference

| Command | What It Does |
|---------|-------------|
| `./expose_servers.sh -1` | Expose theme 1 only |
| `./expose_servers.sh -2` | Expose theme 2 only |
| `./expose_servers.sh -3` | Expose theme 3 only |
| `./expose_servers.sh -4` | Expose theme 4 only |
| `./expose_servers.sh -5` | Expose theme 5 only |
| `./expose_servers.sh -6` | Expose theme 6 only |
| `./expose_servers.sh -all` | Expose all 6 themes |
| `./expose_servers.sh --help` | Show help message |

### With Options

```bash
# Use ngrok instead of cloudflared
./expose_servers.sh -1 --method ngrok

# Start from different port
./expose_servers.sh -1 --port 6000

# Combine options
./expose_servers.sh -all --method cloudflared --port 7000
```

## 🔧 Methods Comparison

### Cloudflared (Default) ✅ RECOMMENDED

```bash
./expose_servers.sh -1
# or
./expose_servers.sh -1 --method cloudflared
```

**Pros:**
- ✅ Free, unlimited tunnels
- ✅ No account needed
- ✅ Instant setup
- ✅ Reliable

**Cons:**
- ⚠️ Random URLs (can't customize)

### ngrok

```bash
./expose_servers.sh -1 --method ngrok
```

**Pros:**
- ✅ Web dashboard at localhost:4040
- ✅ Request inspection
- ✅ Custom domains (paid)

**Cons:**
- ⚠️ Free tier limits tunnels
- ⚠️ Requires account + authtoken
- ⚠️ Extra setup

## 📊 What Gets Created/Updated

When you run the script:

1. **Wiki servers start** (if not running)
   - Theme 1 on port 5000
   - Theme 2 on port 5001
   - ...etc

2. **Tunnels are created**
   - Secure HTTPS connections
   - Public URLs generated

3. **`.env` file updated** (in `data_annotation/`)
   ```bash
   WIKI1=https://url-for-theme-1.trycloudflare.com
   WIKI2=https://url-for-theme-2.trycloudflare.com
   ...
   ```

4. **URLs displayed** in terminal
   ```
   Theme 1 (port 5000): https://abc.trycloudflare.com
   Theme 2 (port 5001): https://def.trycloudflare.com
   ...
   ```

## 🔐 Security & Privacy

### What's Safe
- ✅ Your IP address is hidden
- ✅ HTTPS encryption
- ✅ URLs are hard to guess (random)
- ✅ Tunnels stop when you stop the script

### What to Watch
- ⚠️ URLs are public (anyone with URL can access)
- ⚠️ Don't share URLs on social media
- ⚠️ Only share with trusted people

## 🐛 Troubleshooting

### Problem: "cloudflared not found"

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

### Problem: "Server failed to start"

```bash
# Check if port is in use
netstat -tuln | grep 5000

# Use different port
./expose_servers.sh -1 --port 6000
```

### Problem: "Can't access URL"

1. Wait 30 seconds after tunnel starts
2. Check server works locally: `curl http://localhost:5000`
3. Try URL in incognito browser
4. Check internet connection

## 🎓 Learning Path

**New to this?** Follow this path:

1. ✅ Read this file (you're here!)
2. ✅ Read [QUICK_START.md](QUICK_START.md)
3. ✅ Install cloudflared
4. ✅ Run `./expose_servers.sh -1`
5. ✅ Open the URL in your browser
6. ✅ Try opening on your phone
7. ✅ Read [ACCESSING_SERVERS.md](ACCESSING_SERVERS.md)
8. ✅ Try `./expose_servers.sh -all`
9. ✅ Read [EXPOSE_SERVERS_README.md](EXPOSE_SERVERS_README.md)

**Already familiar?**

Jump straight to:
- [QUICK_START.md](QUICK_START.md) for commands
- `./expose_servers.sh --help` for options

## 🎯 Goals This Solves

### ✅ Before this script:
- ❌ Servers only accessible on `localhost`
- ❌ Can't test on phone/tablet
- ❌ Can't share with collaborators
- ❌ Can't do remote data collection
- ❌ Manual network configuration needed

### ✅ After this script:
- ✅ Servers accessible via public URLs
- ✅ Test on any device
- ✅ Share URLs easily
- ✅ Remote data collection works
- ✅ Zero network configuration

## 📝 Example Workflow

```bash
# 1. Navigate to wiki directory
cd "E:\Projects - GitHub\TimeWarp\env\wiki"

# 2. Start exposing all themes
./expose_servers.sh -all

# 3. Wait for URLs (about 30 seconds)
# Output shows:
#   Theme 1: https://url1.trycloudflare.com
#   Theme 2: https://url2.trycloudflare.com
#   ...

# 4. URLs are auto-saved to .env file

# 5. Use in data collection
cd ../../data_annotation
./collect_batch.sh wiki 1

# 6. Or share URLs with team members

# 7. When done, press Ctrl+C to stop
```

## 🌟 Key Features

- ✨ **Simple:** One command to expose servers
- ✨ **Fast:** URLs ready in ~30 seconds
- ✨ **Secure:** HTTPS by default
- ✨ **Free:** Uses free tunneling services
- ✨ **Flexible:** Choose individual or all themes
- ✨ **Automatic:** Updates .env file for you
- ✨ **Clean:** Ctrl+C stops everything

## 🔗 Integration with Other Scripts

### Works with `collect_batch.sh`

```bash
# 1. Expose servers
cd env/wiki
./expose_servers.sh -all

# 2. Collect data
cd ../../data_annotation
./collect_batch.sh wiki 1    # Uses WIKI1 from .env
./collect_batch.sh wiki all  # Uses all WIKI* from .env
```

### Works with `start_wiki.sh`

```bash
# If servers already running from start_wiki.sh
./start_wiki.sh -all

# expose_servers.sh will detect and use them
./expose_servers.sh -all
```

## 📦 Requirements

- **Python 3** (for wiki servers)
- **Cloudflared** OR **ngrok** (for tunneling)
- **Bash** (for running script)
- **Internet connection** (for tunneling)

## 🆘 Getting Help

1. **Quick help:** `./expose_servers.sh --help`
2. **Documentation:** Read files in this order:
   - [QUICK_START.md](QUICK_START.md)
   - [ACCESSING_SERVERS.md](ACCESSING_SERVERS.md)
   - [EXPOSE_SERVERS_README.md](EXPOSE_SERVERS_README.md)
3. **Check logs:** Terminal output shows detailed progress
4. **Test locally first:** `curl http://localhost:5000`

## 🎉 Success Indicators

You know it's working when:

1. ✅ Terminal shows "✓ All tunnels are running!"
2. ✅ URLs are displayed in terminal
3. ✅ You can open URLs in your browser
4. ✅ `.env` file contains the URLs
5. ✅ URLs work on different devices

## 📚 Additional Resources

- **Cloudflared Docs:** https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- **ngrok Docs:** https://ngrok.com/docs
- **Flask Security:** https://flask.palletsprojects.com/en/2.3.x/security/

---

## TL;DR

```bash
# Install cloudflared (once)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# Run script
./expose_servers.sh -all

# Get URLs, share them, use them!
# Press Ctrl+C when done
```

**That's it!** 🎉

---

*For detailed step-by-step instructions, see [QUICK_START.md](QUICK_START.md)*


