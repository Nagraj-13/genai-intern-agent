# Flask Backend for Blog Platform

This is a Flask backend that provides REST API endpoints for blog storage and user profile management with SQLite database.

## Features

- **Blog Storage**: Save and retrieve published blogs
- **User Profile Storage**: Save and retrieve user profiles
- **Draft Management**: Save and retrieve blog drafts
- **SQLite Database**: Local file-based database for data persistence
- **CORS Support**: Cross-origin resource sharing enabled for frontend integration

## API Endpoints

### User Profile Endpoints

- `POST /api/users` - Create or update user profile
- `GET /api/users/<email>` - Get user profile by email

### Blog Endpoints

- `POST /api/blogs` - Publish a new blog post
- `GET /api/blogs` - Get all published blogs
- `GET /api/blogs/<id>` - Get a specific blog by ID
- `PUT /api/blogs/<id>` - Update a blog post
- `DELETE /api/blogs/<id>` - Delete a blog post

### Draft Endpoints

- `POST /api/drafts` - Save a blog draft
- `GET /api/drafts` - Get all drafts (optional user_id query parameter)

### Health Check

- `GET /api/health` - Health check endpoint

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    preferred_topics TEXT,  -- JSON array
    reading_level TEXT,
    writing_style TEXT,
    target_audience TEXT,
    specializations TEXT,   -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Blogs Table
```sql
CREATE TABLE blogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER,
    status TEXT DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### Drafts Table
```sql
CREATE TABLE drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## Setup Instructions

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask Application**
   ```bash
   python app.py
   ```

3. **The server will start on**
   ```
   http://localhost:3001
   ```

4. **Database Initialization**
   - The database (`blog_app.db`) will be created automatically when you first run the application
   - Tables will be created automatically using the `init_db()` function

## Usage Examples

### Create User Profile
```bash
curl -X POST http://localhost:3001/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "preferredTopics": ["Technology", "Law"],
    "readingLevel": "intermediate",
    "writingStyle": "formal",
    "targetAudience": "Legal professionals",
    "specializations": ["Corporate Law", "IP Law"]
  }'
```

### Publish a Blog
```bash
curl -X POST http://localhost:3001/api/blogs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Blog Post",
    "content": "This is the content of my first blog post about legal technology.",
    "user_id": 1
  }'
```

### Get All Blogs
```bash
curl http://localhost:3001/api/blogs
```

### Get User Profile
```bash
curl http://localhost:3001/api/users/john@example.com
```

## Development Notes

- The backend is configured to run on port 3001 to avoid conflicts with the React development server (port 3000)
- CORS is enabled for all origins in development mode
- SQLite database file (`blog_app.db`) will be created in the backend directory
- All JSON fields (preferredTopics, specializations) are stored as JSON strings in the database
- Timestamps are automatically managed by SQLite

## Error Handling

The API returns appropriate HTTP status codes:
- `200` - Success
- `201` - Created successfully
- `400` - Bad request (missing required fields)
- `404` - Not found
- `500` - Internal server error

Error responses include a JSON object with an `error` field describing the issue.