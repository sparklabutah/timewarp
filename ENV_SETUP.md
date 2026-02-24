# Environment Variables Setup

## ✅ What Was Fixed

1. **Updated all application files** to load from `.env`:
   - `env/wiki/wiki_app.py`
   - `env/news/news_app.py`
   - `env/webshop/web_agent_site/app.py`
   - `env/homepage/homepage_app.py`

2. **Added `python-dotenv`** to all requirements files

3. **Created example usage file**: `env/example_env_usage.py`

## ⚠️ Action Required: Fix Your `.env` File

Your `.env` file currently has this format:
```
WIKI1 = "http://localhost:5001"
```

**It should be** (no spaces, no quotes):
```
WIKI1=http://localhost:5001
```

### Correct Format Rules:
- ✅ `KEY=VALUE` (no spaces around `=`)
- ✅ No quotes needed (unless the value itself contains spaces)
- ✅ One variable per line
- ✅ Comments start with `#`

### Example `.env` file:
```bash
# Wiki URLs
WIKI1=http://localhost:5001
WIKI2=http://localhost:5002
WIKI3=http://localhost:5003
WIKI4=http://localhost:5004
WIKI5=http://localhost:5005
WIKI6=http://localhost:5006

# News URLs
NEWS1=http://localhost:5007
NEWS2=http://localhost:5008

# Webshop URLs
WEBSHOP1=http://localhost:5009
WEBSHOP2=http://localhost:5010
```

## 📖 How to Use

### In Python files:

```python
import os
from dotenv import load_dotenv

# Load environment variables (do this once at the top)
load_dotenv()

# Access variables
wiki_url = os.getenv('WIKI1')
print(wiki_url)  # Output: http://localhost:5001

# With default value (if variable doesn't exist)
wiki_url = os.getenv('WIKI1', 'http://localhost:5001')
```

### Example Usage:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Get wiki URL for theme 1
wiki1 = os.getenv('WIKI1')
if wiki1:
    print(f"Connecting to {wiki1}")
else:
    print("WIKI1 not found in .env file")
```

## 🔧 Installation

Make sure `python-dotenv` is installed:

```bash
pip install python-dotenv
```

Or install from requirements:
```bash
pip install -r env/wiki/requirements.txt
pip install -r env/news/requirements.txt
pip install -r env/homepage/requirements.txt
pip install -r env/webshop/requirements.txt
```

## ✅ Verification

After fixing your `.env` file, test it:

```bash
python env/example_env_usage.py
```

This should print the URLs from your `.env` file.


