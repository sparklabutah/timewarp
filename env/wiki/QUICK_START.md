# Quick Start - Expose Wiki Servers

## 1️⃣ Install Cloudflared (One-time setup)

```bash
# For Windows WSL
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

## 2️⃣ Make Script Executable (One-time setup)

```bash
cd "E:\Projects - GitHub\TimeWarp\env\wiki"
chmod +x expose_servers.sh
```

## 3️⃣ Run the Script

### Expose ONE theme:
```bash
./expose_servers.sh -1    # Theme 1
./expose_servers.sh -2    # Theme 2
./expose_servers.sh -3    # Theme 3
```

### Expose ALL themes:
```bash
./expose_servers.sh -all
```

## 4️⃣ Get Your URLs

The script will output something like:

```
Public URLs for wiki servers:
============================================================
Theme 1 (port 5000): https://abc-def-123.trycloudflare.com
Theme 2 (port 5001): https://ghi-jkl-456.trycloudflare.com
...
============================================================
```

## 5️⃣ Share & Use

✅ **Share the URLs** with anyone - they work from anywhere!

✅ **Use in data collection**:
```bash
cd ../../data_annotation
./collect_batch.sh wiki 1
```

✅ **URLs auto-saved** to `.env` file

## 🛑 To Stop

Press `Ctrl+C` in the terminal

---

## Common Commands

| Command | What it does |
|---------|-------------|
| `./expose_servers.sh -1` | Expose theme 1 only |
| `./expose_servers.sh -all` | Expose all 6 themes |
| `./expose_servers.sh --help` | Show full help |
| `./expose_servers.sh -3 --method ngrok` | Use ngrok instead |

## Need Help?

See `EXPOSE_SERVERS_README.md` for detailed documentation.


