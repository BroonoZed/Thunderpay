# Database Operations
import sqlite3
import os
import json
from datetime import datetime
from config import DATABASE_PATH, IMAGES_DIR


def init_database():
    """Initialize database"""
    # Ensure directories exist
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create order images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_id TEXT,
            telegram_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_number ON orders(order_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_images_order_id ON order_images(order_id)')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_order(order_number: str):
    """
    Search order by order number
    Returns: Order info dict or None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Exact match
    cursor.execute('''
        SELECT * FROM orders 
        WHERE order_number = ? COLLATE NOCASE
    ''', (order_number,))
    
    order = cursor.fetchone()
    
    if order:
        order_dict = dict(order)
        # Get related images
        cursor.execute('''
            SELECT file_path, file_id FROM order_images 
            WHERE order_id = ?
        ''', (order_dict['id'],))
        order_dict['images'] = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return order_dict
    
    conn.close()
    return None


def fuzzy_search_order(keyword: str):
    """
    Fuzzy search orders
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM orders 
        WHERE order_number LIKE ? COLLATE NOCASE
        ORDER BY created_at DESC
        LIMIT 5
    ''', (f'%{keyword}%',))
    
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders


def save_order_image(order_number: str, file_path: str, file_id: str = None, message_id: int = None):
    """
    Save order image
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find order ID first
    cursor.execute('SELECT id FROM orders WHERE order_number = ? COLLATE NOCASE', (order_number,))
    order = cursor.fetchone()
    
    if order:
        cursor.execute('''
            INSERT INTO order_images (order_id, file_path, file_id, telegram_message_id)
            VALUES (?, ?, ?, ?)
        ''', (order['id'], file_path, file_id, message_id))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False


def create_order(order_number: str, status: str = 'pending', description: str = None):
    """
    Create new order (for testing)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO orders (order_number, status, description)
            VALUES (?, ?, ?)
        ''', (order_number, status, description))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Order already exists


def get_order_images(order_number: str):
    """
    Get all images for an order
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT oi.* FROM order_images oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.order_number = ? COLLATE NOCASE
    ''', (order_number,))
    
    images = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return images


def get_all_orders(limit: int = 20):
    """
    Get all orders list (for management)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT o.*, COUNT(oi.id) as image_count 
        FROM orders o
        LEFT JOIN order_images oi ON o.id = oi.order_id
        GROUP BY o.id
        ORDER BY o.updated_at DESC
        LIMIT ?
    ''', (limit,))
    
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders


def delete_order(order_number: str):
    """
    Delete order and its images
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get order ID
    cursor.execute('SELECT id FROM orders WHERE order_number = ? COLLATE NOCASE', (order_number,))
    order = cursor.fetchone()
    
    if order:
        # Get image paths
        cursor.execute('SELECT file_path FROM order_images WHERE order_id = ?', (order['id'],))
        images = cursor.fetchall()
        
        # Delete physical files
        for img in images:
            try:
                if os.path.exists(img['file_path']):
                    os.remove(img['file_path'])
            except Exception as e:
                print(f"Failed to delete image: {e}")
        
        # Delete database records
        cursor.execute('DELETE FROM orders WHERE id = ?', (order['id'],))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False


if __name__ == '__main__':
    # Run this file directly to initialize database
    init_database()
    
    # Add some test data
    create_order('ORD2024001', 'completed', 'Test Order 1')
    create_order('ORD2024002', 'pending', 'Test Order 2')
    create_order('ABC123456', 'processing', 'Test Order 3')
    print("✅ Test data added")
