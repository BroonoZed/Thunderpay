# Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Token (Get from @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/orders.db')
IMAGES_DIR = os.getenv('IMAGES_DIR', 'data/images')

# Order Keywords Configuration
ORDER_KEYWORDS = ['order', 'order#', 'orderno', '#']

# Order Number Regex Patterns (Optimized: supports letters/numbers/hyphens/underscores, min 7 chars, excludes decimals/currency)
ORDER_NUMBER_PATTERNS = [
    r'order[\s:：]*#?([a-zA-Z0-9_\-]{7,})',      # After order, supports letters/numbers/hyphens/underscores, min 7 chars
    r'order#([a-zA-Z0-9_\-]{7,})',               # After order#, supports letters/numbers/hyphens/underscores, min 7 chars
    r'#([a-zA-Z0-9_\-]{7,})',                    # After #, supports letters/numbers/hyphens/underscores, min 7 chars
    r'(?<!\.)\b([a-zA-Z0-9_\-]{7,})\b(?!\.)',    # Global match, supports letters/numbers/hyphens/underscores, min 7 chars, excludes decimals
]

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Admin ID List (for debug notifications)
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]

# ===== Group Forwarding Configuration =====
# Forwarding Rules: {source_group_id: target_group_id}
# Example: -1001234567890: -1009876543210 means messages from Group A(-1001234567890) will be forwarded to Group B(-1009876543210)
FORWARD_RULES = {}

# Read forwarding rules from environment variable, format: "source1:target1,source2:target2"
_forward_env = os.getenv('FORWARD_RULES', '')
if _forward_env:
    for rule in _forward_env.split(','):
        if ':' in rule:
            source, target = rule.split(':', 1)
            try:
                FORWARD_RULES[int(source.strip())] = int(target.strip())
            except ValueError:
                pass

# Whether to only forward replies to bot messages (True=only bot replies, False=all replies)
FORWARD_ONLY_BOT_REPLIES = os.getenv('FORWARD_ONLY_BOT_REPLIES', 'true').lower() in ('true', '1', 'yes')

# Forwarding feature whitelist user ID list
FORWARD_WHITELIST = [int(x.strip()) for x in os.getenv('FORWARD_WHITELIST', '').split(',') if x.strip()]

# Whether admins (ADMIN_IDS) automatically have forwarding permission
ADMIN_CAN_FORWARD = os.getenv('ADMIN_CAN_FORWARD', 'true').lower() in ('true', '1', 'yes')
