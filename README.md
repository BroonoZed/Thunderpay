# ThunderPay - Telegram Order Management Bot

A Telegram bot for order management with automatic order detection, image saving, and group forwarding features.

## Features

1. **Group Chat Monitoring** - Automatically detect messages containing order keywords
2. **Order Matching** - Extract order numbers from messages and query the database
3. **Image Saving** - Automatically extract and save images from matched messages
4. **Error Feedback** - Friendly error messages for unmatched orders
5. **Group Forwarding** - Forward replies to bot messages from Group A to Group B (whitelist protected)

## Project Structure

```
tg-order-bot/
├── bot.py              # Main entry point
├── config.py           # Configuration file
├── database.py         # Database operations
├── handlers.py         # Message handlers
├── requirements.txt    # Dependencies
├── .env.example        # Environment variables example
└── data/               # Data directory
    ├── orders.db       # SQLite database
    └── images/         # Image storage
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env file and fill in your Bot Token
```

### 3. Initialize Database

```bash
python database.py
```

### 4. Run the Bot

```bash
python bot.py
```

## Get Bot Token

1. Search @BotFather in Telegram
2. Send `/newbot` to create a new bot
3. Follow prompts to set name and username
4. Copy the token to `.env` file

## Usage

### Method 1: Auto-detection (Group Chat)
Add the bot to a group chat and it will automatically monitor messages containing order keywords:
- "Order: ORD2024001"
- "Order ORD2024001"
- "order ORD2024001"
- "order#ORD2024001"
- "#ORD2024001"

### Method 2: Active Query (Private/Group)
Send `/check order_number` to actively query an order

### Method 3: Group Forwarding
After configuring forwarding rules, when someone replies to bot messages in Group A, it will be automatically forwarded to Group B.

**⚠️ Permission Notice:** Only whitelist users can set forwarding rules

**Set Forwarding Rule:**
1. In Group A, send `/setforward <Group_B_ID>`
2. Or configure via environment variable: `FORWARD_RULES=-1001234567890:-1009876543210`

**View Forwarding Rules:**
```
/listforward
```

**Get Group ID:**
1. Add @userinfobot to the group
2. Send any message, the bot will return the group ID

**Get User ID:**
1. Private message @userinfobot
2. Send any message, the bot will return your user ID

**Environment Variable Example:**
```
FORWARD_RULES=-1001234567890:-1009876543210,-1001111111111:-1002222222222
FORWARD_ONLY_BOT_REPLIES=true

# Whitelist configuration (only these users can set forwarding)
FORWARD_WHITELIST=123456789,987654321
ADMIN_CAN_FORWARD=true  # Whether admins automatically have permission
```

## Database Structure

**orders table:**
- id: Primary key
- order_number: Order number (unique)
- status: Order status
- description: Order description
- created_at: Creation time
- updated_at: Update time

**order_images table:**
- id: Primary key
- order_id: Related order ID
- file_path: Image file path
- file_id: Telegram file ID
- telegram_message_id: Telegram message ID
- created_at: Creation time

## Commands

| Command | Description | Permission |
|---------|-------------|------------|
| /start | Start using | All |
| /check <order> | Query order | All |
| /help | Show help | All |
| /addtest <order> [status] [desc] | Add test order | All |
| /setforward <group_id> | Set forwarding rule | Whitelist only |
| /listforward | View forwarding rules | Whitelist only |

## Deployment

### Using systemd Service

```bash
sudo nano /etc/systemd/system/thunderpay.service
```

Content:
```ini
[Unit]
Description=ThunderPay Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/tg-order-bot
ExecStart=/usr/bin/python3 /path/to/tg-order-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable thunderpay
sudo systemctl start thunderpay
```

### Using Docker

```bash
docker build -t thunderpay .
docker run -d --name thunderpay --env-file .env thunderpay
```

## Notes

1. Bot needs group chat message read permission
2. Ensure `data/images` directory has write permission
3. For production, consider using PostgreSQL instead of SQLite
4. **Forwarding Whitelist:** Only whitelist users can use `/setforward` and `/listforward` commands, configure `FORWARD_WHITELIST` in `.env`

## License

MIT License
