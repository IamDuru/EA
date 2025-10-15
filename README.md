## 🚀 One-Click Deploy
<h3 align="center">
    ─「 ᴅᴇᴩʟᴏʏ ᴏɴ ʜᴇʀᴏᴋᴜ 」─
</h3>

<p align="center"><a href="https://dashboard.heroku.com/new?template=https://github.com/IamDuru/EA"> <img src="https://img.shields.io/badge/Deploy%20On%20Heroku-black?style=for-the-badge&logo=heroku" width="220" height="38.45"/></a></p>

 </h3>
 
### Koyeb
[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=https://github.com/IamDuru/EA&branch=main&name=youtube-music-bot)

### Railway Docker
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/dockerfile?template=https://github.com/IamDuru/EA)



## 🖥️ VPS Deployment (Ubuntu/Debian)

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Python
```bash
sudo apt install -y python3.11 python3-pip git
```

### 3. Clone & Setup
```bash
git clone https://github.com/IamDuru/EA.git
cd EA
pip3 install -r requirements.txt
```

### 4. Configure
```bash
cp config.env.example config.env
nano config.env  # Add your API keys
```

### 5. Run
```bash
python3 -m ERAAPI
```

## 📡 API Usage

### Audio Download
```bash
curl "https://your-domain.com/try?key=API_KEY&query=song+name&vid=false"
```

### Video Download
```bash
curl "https://your-domain.com/try?key=API_KEY&query=video+name&vid=true"
```

### API Key Setup
1. Generate a strong API key (e.g., using `openssl rand -hex 32`)
2. Add it to `config.env`: `API_KEY=your_generated_api_key`
3. Restart the server

### Manual Docker
```bash
docker build -t youtube-bot .
docker run -p 8000:8000 \
  -e API_ID=your_api_id \
  -e API_HASH=your_api_hash \
  -e BOT_TOKEN=your_bot_token \
  -e AUDIO_CHANNEL_ID=-1001234567890 \
  -e VIDEO_CHANNEL_ID=-1009876543210 \
  -e MONGO_URL=your_mongodb_url \
  -e API_KEY=your_api_key_here \
  youtube-bot
```



