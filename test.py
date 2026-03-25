#!/usr/bin/env python3
# 测试脚本 - 用于验证机器人功能
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_database, create_order, search_order, 
    get_all_orders, delete_order, fuzzy_search_order
)


def test_database():
    """测试数据库功能"""
    print("=" * 50)
    print("🧪 数据库功能测试")
    print("=" * 50)
    
    # 初始化数据库
    init_database()
    
    # 添加测试订单
    test_orders = [
        ('TEST001', 'completed', '测试订单1'),
        ('TEST002', 'pending', '测试订单2'),
        ('ORD2024001', 'processing', '处理中订单'),
        ('ABC123456', 'completed', '字母数字混合'),
    ]
    
    print("\n📦 添加测试订单...")
    for order_num, status, desc in test_orders:
        if create_order(order_num, status, desc):
            print(f"   ✅ {order_num} - {desc}")
        else:
            print(f"   ⚠️ {order_num} - 已存在或失败")
    
    # 测试查询
    print("\n🔍 测试订单查询...")
    for order_num, _, _ in test_orders:
        result = search_order(order_num)
        if result:
            print(f"   ✅ 找到: {result['order_number']} ({result['status']})")
        else:
            print(f"   ❌ 未找到: {order_num}")
    
    # 测试模糊搜索
    print("\n🔎 测试模糊搜索...")
    results = fuzzy_search_order('TEST')
    print(f"   搜索 'TEST' 找到 {len(results)} 个结果")
    for r in results:
        print(f"      - {r['order_number']}")
    
    # 列出所有订单
    print("\n📋 所有订单列表:")
    all_orders = get_all_orders()
    for order in all_orders:
        print(f"   • {order['order_number']}: {order['status']} ({order['image_count']} 张图片)")
    
    print("\n✅ 数据库测试完成!")


def test_order_extraction():
    """测试订单号提取功能"""
    print("\n" + "=" * 50)
    print("🧪 订单号提取测试")
    print("=" * 50)
    
    test_cases = [
        ("订单号: ABC123", "ABC123"),
        ("订单 ABC123", "ABC123"),
        ("order ABC123", "ABC123"),
        ("order#ABC123", "ABC123"),
        ("order: ABC123", "ABC123"),
        ("#ABC123", "ABC123"),
        ("ORD2024001 发货了", "ORD2024001"),
        ("请查收订单号123456", "123456"),
        ("ORDER#TEST001 已完成", "TEST001"),
    ]
    
    from handlers import extract_order_number
    
    print()
    for text, expected in test_cases:
        result = extract_order_number(text)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{text}'")
        print(f"      预期: {expected}, 实际: {result}")
    
    print("\n✅ 提取测试完成!")


if __name__ == '__main__':
    try:
        test_database()
        test_order_extraction()
        print("\n🎉 所有测试通过!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
