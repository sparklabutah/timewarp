# How to Access Wiki Servers Publicly

## TL;DR - What You Need to Know

When you run the `expose_servers.sh` script, it gives you **public HTTPS URLs** that anyone can access from anywhere in the world.

### What URLs Look Like

```
https://random-words-1234.trycloudflare.com
```

These are:
- ✅ Secure (HTTPS)
- ✅ Public (accessible from anywhere)
- ✅ Temporary (valid while script is running)
- ✅ Random (new URL each time you run the script)

### No IP Address Needed!

**You DON'T need to know your IP address** at all! The tunneling service (Cloudflare/ngrok) handles everything for you.

## How It Works

```
Your Computer            Cloudflare/ngrok           Internet
┌──────────┐            ┌───────────────┐         ┌─────────┐
│  Wiki    │            │               │         │         │
│  Server  │◄──────────►│    Tunnel     │◄───────►│ Anyone  │
│  :5000   │  Secure    │   Service     │ Public  │         │
└──────────┘  Tunnel    └───────────────┘  URL    └─────────┘
```

1. **Your server** runs on `localhost:5000` (only you can access)
2. **Script creates tunnel** through Cloudflare/ngrok
3. **Public URL generated** (e.g., `https://abc-123.trycloudflare.com`)
4. **Anyone with URL** can access your server

## Step-by-Step Example

### Step 1: Run the script

```bash
cd "E:\Projects - GitHub\TimeWarp\env\wiki"
./expose_servers.sh -1
```

### Step 2: Wait for output

```
Starting Cloudflare Tunnels...

Starting tunnel for Theme 1 (port 5000)...
  Waiting for tunnel URL... ✓

Public URLs for wiki servers:
============================================================
Theme 1 (port 5000): https://super-turtle-9876.trycloudflare.com
============================================================
```

### Step 3: Copy the URL

Copy this URL: `https://super-turtle-9876.trycloudflare.com`

### Step 4: Access from anywhere!

You can now:

- **Open it in YOUR browser** on your computer
- **Open it on your phone** (same WiFi or different network)
- **Share it with a friend** who can open it from their location
- **Use it in your scripts** (it's already added to `.env`)

## Examples of What You Can Do

### Example 1: Access from Your Phone

1. Run script on your computer
2. Get URL: `https://happy-dog-1234.trycloudflare.com`
3. Open URL on your phone browser
4. ✅ You can now interact with your wiki from your phone!

### Example 2: Share with Collaborator

1. Run script with all themes: `./expose_servers.sh -all`
2. Get 6 URLs
3. Send URLs to your collaborator via email/Slack
4. ✅ They can access all themes from their location!

### Example 3: Use in Data Collection

1. Run script: `./expose_servers.sh -all`
2. URLs auto-saved to `.env` file
3. Run data collection: `cd ../../data_annotation && ./collect_batch.sh wiki 1`
4. ✅ Script uses public URL from `.env`!

## Understanding the URLs

### Cloudflared URLs

Format: `https://[random-words-numbers].trycloudflare.com`

Examples:
- `https://super-turtle-9876.trycloudflare.com`
- `https://happy-elephant-5432.trycloudflare.com`
- `https://clever-fox-1357.trycloudflare.com`

**Properties:**
- Random each time
- Free unlimited tunnels
- No account needed
- HTTPS by default

### ngrok URLs

Format: `https://[random-id].ngrok-free.app`

Examples:
- `https://abc123def456.ngrok-free.app`
- `https://xyz789qrs012.ngrok-free.app`

**Properties:**
- Random (custom domains on paid plan)
- Free tier: limited tunnels
- Requires account
- Web dashboard at `http://localhost:4040`

## What About IP Addresses?

You might be wondering: "But what's MY IP address?"

**You don't need it!** Here's why:

### Traditional Method (Complex) ❌

1. Find your public IP: `123.456.789.012`
2. Configure router port forwarding
3. Configure firewall rules
4. Access via: `http://123.456.789.012:5000`
5. ⚠️ Not HTTPS (insecure)
6. ⚠️ Exposes your home IP
7. ⚠️ Complex setup

### Tunnel Method (Simple) ✅

1. Run: `./expose_servers.sh -1`
2. Get URL: `https://abc-123.trycloudflare.com`
3. ✅ That's it!
4. ✅ HTTPS by default
5. ✅ Your IP hidden
6. ✅ No router/firewall config

## Security & Privacy

### What's Exposed
- ✅ Your wiki server content (HTML pages)
- ✅ Your server's responses to requests

### What's NOT Exposed
- ✅ Your home IP address (hidden by tunnel)
- ✅ Your computer files (only server content)
- ✅ Your local network

### Best Practices
1. **Don't share URLs publicly** on social media
2. **Only share with trusted people** who need access
3. **Stop tunnel when done** (Ctrl+C)
4. **URLs expire** when you stop the script (automatic security)

## Troubleshooting Access

### "I can't access the URL"

**Try these:**
1. Wait 30 seconds after tunnel starts
2. Try accessing `http://localhost:5000` first (verify server works)
3. Check terminal for errors
4. Try opening URL in incognito/private window
5. Check your internet connection

### "URL works on my computer but not phone"

**This should NOT happen** - URLs work from anywhere. If it does:
1. Check phone's internet connection
2. Try different phone network (WiFi vs mobile data)
3. Clear browser cache on phone
4. Try different browser on phone

### "URL stopped working"

**Likely causes:**
1. Script was stopped (Ctrl+C) - **Solution:** Run script again
2. Computer went to sleep - **Solution:** Keep computer awake
3. Internet disconnected - **Solution:** Reconnect and restart script
4. Server crashed - **Solution:** Check terminal for errors

## Real-World Access Scenarios

### Scenario 1: Testing on Different Devices

**Goal:** Test wiki on phone, tablet, and laptop

```bash
# On your computer
./expose_servers.sh -1

# Output: https://test-url-123.trycloudflare.com

# Now open this URL on:
# - Your laptop browser ✅
# - Your phone browser ✅
# - Your tablet browser ✅
# - All devices see the same content!
```

### Scenario 2: Remote Data Collection

**Goal:** Collect data from a remote location

```bash
# Before leaving your office/home
./expose_servers.sh -all

# Copy the 6 URLs
# Go to library/coffee shop
# Use the URLs there - they still work!
```

### Scenario 3: Collaboration

**Goal:** Multiple people collecting data simultaneously

```bash
# Person A runs script
./expose_servers.sh -all

# Person A shares 6 URLs with Persons B, C, D
# All 4 people can access simultaneously
# Each can work on different themes
```

## Comparison: Local vs Public Access

| Aspect | Local (localhost:5000) | Public (tunnel URL) |
|--------|----------------------|-------------------|
| **Access** | Only your computer | Anywhere in world |
| **URL** | `http://localhost:5000` | `https://abc.trycloudflare.com` |
| **Security** | Private | Public (but URL is hard to guess) |
| **HTTPS** | ❌ No | ✅ Yes |
| **Share** | ❌ Can't share | ✅ Easy to share |
| **Setup** | ✅ Already works | ✅ Run one script |

## Quick Reference

| Want to... | Command |
|-----------|---------|
| Expose theme 1 | `./expose_servers.sh -1` |
| Expose all themes | `./expose_servers.sh -all` |
| Use ngrok | `./expose_servers.sh -1 --method ngrok` |
| Check ngrok dashboard | Open `http://localhost:4040` |
| Stop tunnels | Press `Ctrl+C` |
| Get new URLs | Stop and run script again |

## Summary

**Bottom Line:** You get HTTPS URLs that work from anywhere, and you don't need to know or configure IP addresses at all. The tunneling service handles everything for you automatically!

```bash
# This single command...
./expose_servers.sh -1

# ...gives you a URL like this:
https://random-name-1234.trycloudflare.com

# ...that works from ANYWHERE! 🌍
```

---

**Next Steps:**
1. Read [`QUICK_START.md`](QUICK_START.md) for installation
2. Read [`EXPOSE_SERVERS_README.md`](EXPOSE_SERVERS_README.md) for detailed docs
3. Run the script and start sharing! 🚀


