# Message Handlers
import re
import os
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from config import (
    ORDER_KEYWORDS, ORDER_NUMBER_PATTERNS, IMAGES_DIR,
    FORWARD_RULES, FORWARD_ONLY_BOT_REPLIES,
    FORWARD_WHITELIST, ADMIN_IDS, ADMIN_CAN_FORWARD
)
from database import search_order, save_order_image, fuzzy_search_order, create_order


def is_forward_authorized(user_id: int) -> bool:
    """
    Check if user has permission to use forwarding features
    
    Permission logic:
    1. If in FORWARD_WHITELIST -> authorized
    2. If in ADMIN_IDS and ADMIN_CAN_FORWARD=True -> authorized
    3. Otherwise -> not authorized
    """
    if user_id in FORWARD_WHITELIST:
        return True
    if ADMIN_CAN_FORWARD and user_id in ADMIN_IDS:
        return True
    return False


async def download_image(file_id: str, file_path: str, context: ContextTypes.DEFAULT_TYPE) -> str:
    """
    Download Telegram image
    """
    try:
        # Get file object
        file_obj = await context.bot.get_file(file_id)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Download file
        await file_obj.download_to_drive(file_path)
        return file_path
    except Exception as e:
        print(f"Failed to download image: {e}")
        return None


def extract_order_number(text: str) -> str:
    """
    Extract order number from message text
    """
    if not text:
        return None
    
    text = text.strip()
    
    # Try various pattern matches
    for pattern in ORDER_NUMBER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().upper()
    
    return None


def contains_order_keyword(text: str) -> bool:
    """
    Check if text contains order keywords
    """
    if not text:
        return False
    
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in ORDER_KEYWORDS)


async def process_order_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process messages containing order keywords
    """
    message = update.message or update.channel_post
    if not message:
        return
    
    # Extract text content
    text = message.text or message.caption or ""
    
    # Check if contains order keywords
    if not contains_order_keyword(text):
        return
    
    # Extract order number
    order_number = extract_order_number(text)
    
    if not order_number:
        # Has keyword but no valid order number format detected
        await message.reply_text(
            "⚠️ Order keyword detected, but no valid order number format recognized.\n"
            "Supported formats: order:XXX, order XXX, #XXX"
        )
        return
    
    print(f"🔍 Order number detected: {order_number}")
    
    # Query database
    order = search_order(order_number)
    
    if order:
        # Order matched successfully
        await handle_matched_order(update, context, order, message)
    else:
        # Order not matched
        await handle_unmatched_order(update, context, order_number, text)


async def handle_matched_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order: dict, message):
    """
    Handle successfully matched order
    """
    order_number = order['order_number']
    
    # Check if message contains images
    photos = message.photo if message.photo else []
    
    if photos:
        # Get highest quality image
        photo = photos[-1]  # Last one is the original
        file_id = photo.file_id
        
        # Generate save path
        timestamp = int(message.date.timestamp())
        file_name = f"{order_number}_{timestamp}_{file_id}.jpg"
        file_path = os.path.join(IMAGES_DIR, file_name)
        
        # Download image
        downloaded_path = await download_image(file_id, file_path, context)
        
        if downloaded_path:
            # Save to database
            save_order_image(
                order_number=order_number,
                file_path=downloaded_path,
                file_id=file_id,
                message_id=message.message_id
            )
            
            # Reply confirmation message
            existing_images = len(order.get('images', []))
            await message.reply_text(
                f"✅ **Order Matched Successfully!**\n\n"
                f"📋 Order Number: `{order_number}`\n"
                f"📊 Status: {get_status_text(order['status'])}\n"
                f"📸 Image Saved ({existing_images + 1} total)\n\n"
                f"📝 {order.get('description', 'No description')}",
                parse_mode='Markdown'
            )
        else:
            await message.reply_text(
                f"✅ Order matched successfully!\n\n"
                f"📋 Order Number: {order_number}\n"
                f"📊 Status: {get_status_text(order['status'])}\n\n"
                f"⚠️ However, image save failed. Please try again."
            )
    else:
        # Matched but no image
        await message.reply_text(
            f"✅ **Order Matched Successfully!**\n\n"
            f"📋 Order Number: `{order_number}`\n"
            f"📊 Status: {get_status_text(order['status'])}\n\n"
            f"💡 To save images, please send them together with the message.",
            parse_mode='Markdown'
        )


async def handle_unmatched_order(update: Update, context: ContextTypes.DEFAULT_TYPE, order_number: str, original_text: str):
    """
    Handle unmatched order - return error message
    """
    message = update.message or update.channel_post
    
    # Try fuzzy search for suggestions
    suggestions = fuzzy_search_order(order_number[:6])  # Search using first 6 characters
    
    error_msg = (
        f"❌ **Order Query Failed**\n\n"
        f"📋 Order Number: `{order_number}`\n"
        f"🔍 No matching record found in database"
    )
    
    if suggestions:
        error_msg += "\n\n🤔 Did you mean:\n"
        for sugg in suggestions[:3]:
            error_msg += f"   • `{sugg['order_number']}` ({get_status_text(sugg['status'])})\n"
    
    await message.reply_text(error_msg, parse_mode='Markdown')


def get_status_text(status: str) -> str:
    """
    Get status display text
    """
    status_map = {
        'pending': '⏳ Pending',
        'processing': '🔄 Processing',
        'completed': '✅ Completed',
        'cancelled': '❌ Cancelled'
    }
    return status_map.get(status, f'📋 {status}')


# ============== Command Handlers ==============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start command
    """
    welcome_text = (
        "👋 **Welcome to Order Query Bot!**\n\n"
        "📌 **Features:**\n"
        "   • Auto-detect order keywords in group chats\n"
        "   • Match order numbers and save related images\n"
        "   • Support active order queries\n\n"
        "📝 **How to use:**\n"
        "   • Include in message: order XXX or #XXX\n"
        "   • Active query: /check <order_number>\n\n"
        "💡 **Examples:**\n"
        "   Order: ORD2024001\n"
        "   /check ORD2024001"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /check <order_number> command - Query order actively
    """
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide an order number\n"
            "Usage: `/check <order_number>`\n"
            "Example: `/check ORD2024001`",
            parse_mode='Markdown'
        )
        return
    
    order_number = context.args[0].strip().upper()
    order = search_order(order_number)
    
    if order:
        image_count = len(order.get('images', []))
        response = (
            f"✅ **Order Query Successful**\n\n"
            f"📋 Order Number: `{order_number}`\n"
            f"📊 Status: {get_status_text(order['status'])}\n"
            f"📸 Images: {image_count}\n"
            f"🕐 Created: {order['created_at']}\n\n"
            f"📝 Description: {order.get('description', 'None')}\n"
        )
        
        # Send images if available
        if order.get('images'):
            await update.message.reply_text(response, parse_mode='Markdown')
            for img in order['images'][:5]:  # Max 5 images
                if os.path.exists(img['file_path']):
                    await update.message.reply_photo(photo=open(img['file_path'], 'rb'))
        else:
            await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"❌ **Order Not Found**\n\n"
            f"📋 Order Number: `{order_number}`\n"
            f"🔍 No such order in database\n\n"
            f"Please check if the order number is correct or contact admin to add it.",
            parse_mode='Markdown'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help command
    """
    help_text = (
        "📖 **Command List**\n\n"
        "/start - Start using\n"
        "/check <order_number> - Query order\n"
        "/help - Show help\n\n"
        "🔍 **Auto-detect Keywords:**\n"
        "   • order\n"
        "   • order#\n\n"
        "📌 **Supported Order Number Formats:**\n"
        "   • Order: ABC123\n"
        "   • Order ABC123\n"
        "   • order ABC123\n"
        "   • order#ABC123\n"
        "   • #ABC123"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def add_test_order_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /addtest <order_number> [status] [description] - Add test order (admin only)
    """
    # Simple check - production should verify admin ID
    if not context.args:
        await update.message.reply_text("Usage: /addtest <order_number> [status] [description]")
        return
    
    order_number = context.args[0].upper()
    status = context.args[1] if len(context.args) > 1 else 'pending'
    description = ' '.join(context.args[2:]) if len(context.args) > 2 else 'Test order'
    
    if create_order(order_number, status, description):
        await update.message.reply_text(f"✅ Test order `{order_number}` added", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"⚠️ Order `{order_number}` already exists or failed to add", parse_mode='Markdown')


# ============== Group Forwarding Handlers ==============

async def forward_reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle reply messages in group chats and forward to specified groups
    
    Logic:
    1. Check if it's a reply message (reply_to_message)
    2. Check if the replied message is from the bot (if FORWARD_ONLY_BOT_REPLIES=True)
    3. Check if current group has forwarding rules
    4. Forward message to target group
    """
    message = update.message
    if not message:
        return
    
    # Check if it's a reply message
    if not message.reply_to_message:
        return
    
    # Get current group ID
    chat_id = message.chat.id
    
    # Check if forwarding rule exists
    if chat_id not in FORWARD_RULES:
        return
    
    target_chat_id = FORWARD_RULES[chat_id]
    
    # If configured to only forward replies to bot messages, check if replied message is from bot
    if FORWARD_ONLY_BOT_REPLIES:
        replied_message = message.reply_to_message
        # Check if the replied message is from a bot
        if not replied_message.from_user or not replied_message.from_user.is_bot:
            return
        # Check if it's from this bot (by comparing user ID)
        bot_info = await context.bot.get_me()
        if replied_message.from_user.id != bot_info.id:
            return
    
    # Build forwarding content
    try:
        # Get sender info
        sender = message.from_user
        sender_name = sender.full_name if sender else "Unknown User"
        sender_username = f"@{sender.username}" if sender and sender.username else ""
        
        # Get replied message content preview
        replied_msg = message.reply_to_message
        replied_text = replied_msg.text or replied_msg.caption or "[Image/Media]"
        # Truncate to 50 characters
        replied_preview = replied_text[:50] + "..." if len(replied_text) > 50 else replied_text
        
        # Build forwarding message
        forward_text = (
            f"📨 **Forwarded Message**\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 **From:** {sender_name} {sender_username}\n"
            f"💬 **Reply:**\n{message.text or message.caption or '[Image/Media]'}\n"
            f"\n📎 **Original:** {replied_preview}\n"
            f"━━━━━━━━━━━━━━━━"
        )
        
        # Send text message
        if message.text:
            await context.bot.send_message(
                chat_id=target_chat_id,
                text=forward_text,
                parse_mode='Markdown'
            )
        
        # If has image, forward image as well
        if message.photo:
            photo = message.photo[-1]  # Get highest quality image
            caption = f"📨 From: {sender_name}\n{message.caption or ''}"
            await context.bot.send_photo(
                chat_id=target_chat_id,
                photo=photo.file_id,
                caption=caption[:1024]  # Telegram caption length limit
            )
        
        # If has other media types, use copy_message
        elif message.document or message.video or message.audio or message.voice:
            await message.copy(chat_id=target_chat_id)
        
        print(f"✅ Forwarded message: from {chat_id} to {target_chat_id}")
        
    except Exception as e:
        print(f"❌ Failed to forward message: {e}")


async def set_forward_rule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setforward <target_group_id> - Set forwarding rule for current group (whitelist only)
    Forward messages from current group to specified target group
    """
    # Check if it's a group
    if update.message.chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups")
        return
    
    # Check whitelist permission
    user_id = update.message.from_user.id if update.message.from_user else None
    if not user_id or not is_forward_authorized(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to set forwarding rules.\n"
            "Please contact admin to add your user ID to the whitelist."
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide target group ID\n"
            "Usage: `/setforward <target_group_id>`\n"
            "Example: `/setforward -1001234567890`\n\n"
            "Tip: Get group ID via @userinfobot",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_chat_id = int(context.args[0])
        source_chat_id = update.message.chat.id
        
        # Update forwarding rule
        FORWARD_RULES[source_chat_id] = target_chat_id
        
        await update.message.reply_text(
            f"✅ **Forwarding Rule Set**\n\n"
            f"📤 Source: `{source_chat_id}`\n"
            f"📥 Target: `{target_chat_id}`\n\n"
            f"Replies to bot messages will now be forwarded to the target group.",
            parse_mode='Markdown'
        )
        
        print(f"📝 Set forwarding rule: {source_chat_id} -> {target_chat_id}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid group ID format. Please provide a numeric ID (e.g., -1001234567890)")


async def list_forward_rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /listforward - View current forwarding rules (whitelist only)
    """
    # Check whitelist permission
    user_id = update.message.from_user.id if update.message.from_user else None
    if not user_id or not is_forward_authorized(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to view forwarding rules.\n"
            "Please contact admin to add your user ID to the whitelist."
        )
        return
    
    if not FORWARD_RULES:
        await update.message.reply_text("📭 No forwarding rules configured")
        return
    
    rules_text = "📋 **Forwarding Rules**\n\n"
    for source, target in FORWARD_RULES.items():
        rules_text += f"• `{source}` → `{target}`\n"
    
    rules_text += f"\n🔧 Forward only bot replies: {'Yes' if FORWARD_ONLY_BOT_REPLIES else 'No'}"
    
    await update.message.reply_text(rules_text, parse_mode='Markdown')
