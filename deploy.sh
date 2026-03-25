#!/bin/bash
# 部署脚本

echo "🚀 Telegram 订单机器人部署脚本"
echo "================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (y/n): " create_venv
if [ "$create_venv" = "y" ]; then
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
fi

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip install -r requirements.txt

# 初始化数据库
echo ""
echo "🗄️  初始化数据库..."
python3 database.py

# 运行测试
echo ""
echo "🧪 运行测试..."
python3 test.py

# 配置检查
echo ""
echo "⚙️  配置检查..."
if [ -f ".env" ]; then
    echo "✅ .env 文件已存在"
    if grep -q "your_bot_token_here" .env; then
        echo "❌ 警告: .env 中的 BOT_TOKEN 仍是默认值!"
        echo "   请编辑 .env 文件，填入从 @BotFather 获取的 Token"
    else
        echo "✅ BOT_TOKEN 已配置"
    fi
else
    echo "⚠️  .env 文件不存在，正在从示例创建..."
    cp .env.example .env
    echo "   请编辑 .env 文件，填入你的 Bot Token"
fi

echo ""
echo "================================"
echo "📝 下一步操作:"
echo ""
echo "1. 编辑 .env 文件，设置 BOT_TOKEN"
echo "   获取方式: 在 Telegram 搜索 @BotFather，发送 /newbot"
echo ""
echo "2. 启动机器人:"
echo "   python3 bot.py"
echo ""
echo "3. 将机器人添加到群聊并设为管理员"
echo ""
echo "4. 测试功能:"
echo "   - 在群聊发送: 订单号 TEST001"
echo "   - 或私聊发送: /check TEST001"
echo ""
