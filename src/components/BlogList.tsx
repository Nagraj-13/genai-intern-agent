import { useState, useEffect } from 'react'
import { getAllBlogs } from '../services/api'
import type { BlogPost } from '../services/api'
import './BlogList.css'

const BlogList = () => {
  const [blogs, setBlogs] = useState<BlogPost[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadBlogs()
  }, [])

  const loadBlogs = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await getAllBlogs()
      setBlogs(result.blogs)
    } catch (err) {
      console.error('Error loading blogs:', err)
      setError('Failed to load blogs. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Unknown date'
    }
  }

  if (loading) {
    return (
      <div className="blog-list">
        <div className="blog-list-header">
          <h2>Published Blogs</h2>
        </div>
        <div className="loading">Loading blogs...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="blog-list">
        <div className="blog-list-header">
          <h2>Published Blogs</h2>
        </div>
        <div className="error">
          {error}
          <button onClick={loadBlogs} className="btn-secondary">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="blog-list">
      <div className="blog-list-header">
        <h2>Published Blogs</h2>
        <p>Total: {blogs.length} blogs</p>
        <button onClick={loadBlogs} className="btn-secondary">
          Refresh
        </button>
      </div>

      {blogs.length === 0 ? (
        <div className="no-blogs">
          <p>No blogs published yet.</p>
          <p>Start writing your first blog post!</p>
        </div>
      ) : (
        <div className="blogs-grid">
          {blogs.map((blog) => (
            <div key={blog.id} className="blog-card">
              <div className="blog-card-header">
                <h3 className="blog-title">{blog.title}</h3>
                <div className="blog-meta">
                  {blog.author_name && (
                    <span className="blog-author">By {blog.author_name}</span>
                  )}
                  <span className="blog-date">
                    {formatDate(blog.created_at || '')}
                  </span>
                </div>
              </div>
              
              <div className="blog-content-preview">
                <p>
                  {blog.content.length > 200 
                    ? `${blog.content.substring(0, 200)}...` 
                    : blog.content
                  }
                </p>
              </div>
              
              <div className="blog-card-footer">
                <span className="blog-id">ID: {blog.id}</span>
                <span className="blog-updated">
                  Updated: {formatDate(blog.updated_at || '')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default BlogList