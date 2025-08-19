
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DATABASE = 'blog_app.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            preferred_topics TEXT,
            reading_level TEXT,
            writing_style TEXT,
            target_audience TEXT,
            specializations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create blogs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER,
            status TEXT DEFAULT 'published',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create drafts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# User Profile endpoints
@app.route('/api/users', methods=['POST'])
def create_user():
    """Create or update user profile"""
    try:
        data = request.get_json()
        
        # Validate required fields

        if not data.get('name') or not data.get('email'):
            return jsonify({'error': 'Name and email are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (data['email'],))
        existing_user = cursor.fetchone()

        # Prepare values for DB
        name = data['name']
        email = data['email']
        preferred_topics = json.dumps(data.get('preferredTopics', []))
        reading_level = data.get('readingLevel', 'intermediate')
        writing_style = data.get('writingStyle', 'formal')
        target_audience = data.get('targetAudience', '')
        specializations = json.dumps(data.get('specializations', []))

        if existing_user:
            # Update existing user
            cursor.execute('''
                UPDATE users 
                SET name = ?, preferred_topics = ?, reading_level = ?, 
                    writing_style = ?, target_audience = ?, specializations = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE email = ?
            ''', (
                name,
                preferred_topics,
                reading_level,
                writing_style,
                target_audience,
                specializations,
                email
            ))
            user_id = existing_user['id'] if isinstance(existing_user, dict) else existing_user[0]
        else:
            # Create new user
            cursor.execute('''
                INSERT INTO users (name, email, preferred_topics, reading_level, 
                                 writing_style, target_audience, specializations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                email,
                preferred_topics,
                reading_level,
                writing_style,
                target_audience,
                specializations
            ))
            user_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'User profile saved successfully',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<email>', methods=['GET'])
def get_user(email):
    """Get user profile by email"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Convert row to dict and parse JSON fields
        user_data = dict(user)
        user_data['preferredTopics'] = json.loads(user_data['preferred_topics'] or '[]')
        user_data['specializations'] = json.loads(user_data['specializations'] or '[]')
        
        # Remove internal fields
        user_data.pop('preferred_topics', None)
        user_data.pop('id', None)
        
        conn.close()
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Blog endpoints
@app.route('/api/blogs', methods=['POST'])
def create_blog():
    """Publish a new blog post"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('content'):
            return jsonify({'error': 'Title and content are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert blog post
        cursor.execute('''
            INSERT INTO blogs (title, content, user_id)
            VALUES (?, ?, ?)
        ''', (
            data['title'],
            data['content'],
            data.get('user_id')  # Optional user_id
        ))
        
        blog_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Blog published successfully',
            'blog_id': blog_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blogs', methods=['GET'])
def get_blogs():
    """Get all published blogs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.title, b.content, b.created_at, b.updated_at,
                   u.name as author_name, u.email as author_email
            FROM blogs b
            LEFT JOIN users u ON b.user_id = u.id
            ORDER BY b.created_at DESC
        ''')
        
        blogs = cursor.fetchall()
        
        # Convert to list of dictionaries
        blogs_list = []
        for blog in blogs:
            blog_dict = dict(blog)
            blogs_list.append(blog_dict)
        
        conn.close()
        
        return jsonify({
            'blogs': blogs_list,
            'total': len(blogs_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>', methods=['GET'])
def get_blog(blog_id):
    """Get a specific blog by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.title, b.content, b.created_at, b.updated_at,
                   u.name as author_name, u.email as author_email
            FROM blogs b
            LEFT JOIN users u ON b.user_id = u.id
            WHERE b.id = ?
        ''', (blog_id,))
        
        blog = cursor.fetchone()
        
        if not blog:
            return jsonify({'error': 'Blog not found'}), 404
        
        blog_dict = dict(blog)
        conn.close()
        
        return jsonify(blog_dict), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    """Update a blog post"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if blog exists
        cursor.execute('SELECT id FROM blogs WHERE id = ?', (blog_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Blog not found'}), 404
        
        # Update blog
        cursor.execute('''
            UPDATE blogs 
            SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('title'),
            data.get('content'),
            blog_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Blog updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blogs/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    """Delete a blog post"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if blog exists
        cursor.execute('SELECT id FROM blogs WHERE id = ?', (blog_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Blog not found'}), 404
        
        # Delete blog
        cursor.execute('DELETE FROM blogs WHERE id = ?', (blog_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Blog deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Draft endpoints
@app.route('/api/drafts', methods=['POST'])
def save_draft():
    """Save a blog draft"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('content'):
            return jsonify({'error': 'Title and content are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert draft
        cursor.execute('''
            INSERT INTO drafts (title, content, user_id)
            VALUES (?, ?, ?)
        ''', (
            data['title'],
            data['content'],
            data.get('user_id')  # Optional user_id
        ))
        
        draft_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Draft saved successfully',
            'draft_id': draft_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/drafts', methods=['GET'])
def get_drafts():
    """Get all drafts"""
    try:
        user_id = request.args.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT d.id, d.title, d.content, d.created_at, d.updated_at,
                       u.name as author_name, u.email as author_email
                FROM drafts d
                LEFT JOIN users u ON d.user_id = u.id
                WHERE d.user_id = ?
                ORDER BY d.updated_at DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT d.id, d.title, d.content, d.created_at, d.updated_at,
                       u.name as author_name, u.email as author_email
                FROM drafts d
                LEFT JOIN users u ON d.user_id = u.id
                ORDER BY d.updated_at DESC
            ''')
        
        drafts = cursor.fetchall()
        
        # Convert to list of dictionaries
        drafts_list = []
        for draft in drafts:
            draft_dict = dict(draft)
            drafts_list.append(draft_dict)
        
        conn.close()
        
        return jsonify({
            'drafts': drafts_list,
            'total': len(drafts_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Blog backend is running',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=3001)