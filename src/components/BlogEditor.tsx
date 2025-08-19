import { useState, useEffect } from "react";
import "./BlogEditor.css";
import {
  publishBlog,
  saveDraft,
  getKeywordRecommendations,
} from "../services/api";
import type {
  BlogPost,
  Draft,
  KeywordRecommendationRequest,
} from "../services/api";

interface KeywordSuggestion {
  word: string;
  relevance: number;
  position?: number;
}

interface BlogScore {
  overall: number;
  readability: number;
  relevance: number;
  tokenUsage: number;
}

const BlogEditor = () => {
  const [blogContent, setBlogContent] = useState("");
  const [title, setTitle] = useState("");
  const [suggestions, setSuggestions] = useState<KeywordSuggestion[]>([]);
  const [score, setScore] = useState<BlogScore>({
    overall: 0,
    readability: 0,
    relevance: 0,
    tokenUsage: 0,
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [cursorPosition, setCursorPosition] = useState(0);
  // Default user object
  const defaultUser = {
    user_id: "user123",
    preferred_topics: ["technology", "AI"],
    reading_level: "intermediate",
    writing_style: "formal",
    target_audience: "developers",
    expertise_areas: ["machine learning", "web development"],
  };

  // Try to load user from localStorage, else use default
  let userProfile;

  try {
    const storedUser = localStorage.getItem("user");
    userProfile = storedUser ? JSON.parse(storedUser) : defaultUser;
  } catch (error) {
    console.error("Error parsing user from localStorage:", error);
    userProfile = defaultUser;
  }

  // Real-time analysis with actual API call
  useEffect(() => {
    if (blogContent.length > 10) {
      setIsAnalyzing(true);

      // Debounce API calls to avoid too many requests
      const timer = setTimeout(async () => {
        try {
          const apiRequest: KeywordRecommendationRequest = {
            current_draft: blogContent,
            cursor_context: blogContent.substring(
              Math.max(0, cursorPosition - 100),
              cursorPosition + 100
            ),
            user_profile: userProfile,
          };

          // Call the actual API
          const response = await getKeywordRecommendations(apiRequest);
          console.log(response);
          const apiSuggestions: KeywordSuggestion[] = response.suggestions.map(
            (suggestion) => ({
              word: suggestion.word,
              relevance: suggestion.relevance,
              position: suggestion.position,
            })
          );

          const apiScore: BlogScore = {
            overall: Math.round(
              (response.readabilityScore + response.relevanceScore) / 2
            ),
            readability: Math.round(response.readabilityScore),
            relevance: Math.round(response.relevanceScore),
            tokenUsage: response.tokenUsage,
          };

          setSuggestions(apiSuggestions);
          setScore(apiScore);
        } catch (error) {
          console.error("Error getting keyword recommendations:", error);

          setSuggestions([]);
          setScore({
            overall: 0,
            readability: 0,
            relevance: 0,
            tokenUsage: Math.floor(blogContent.length / 4),
          });
        } finally {
          setIsAnalyzing(false);
        }
      }, 10000);

      return () => clearTimeout(timer);
    } else {
      setSuggestions([]);
      setScore({
        overall: 0,
        readability: 0,
        relevance: 0,
        tokenUsage: 0,
      });
    }
  }, [blogContent, cursorPosition]);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setBlogContent(e.target.value);
    setCursorPosition(e.target.selectionStart);
  };

  const insertSuggestion = (suggestion: string) => {
    const beforeCursor = blogContent.substring(0, cursorPosition);
    const afterCursor = blogContent.substring(cursorPosition);
    const newContent = beforeCursor + suggestion + " " + afterCursor;
    setBlogContent(newContent);
  };

  const handleSaveDraft = async () => {
    if (!title.trim() || !blogContent.trim()) {
      alert("Please enter both title and content before saving draft.");
      return;
    }

    try {
      const draft: Draft = {
        title: title.trim(),
        content: blogContent.trim(),
      };

      const result = await saveDraft(draft);
      alert(`Draft saved successfully! Draft ID: ${result.draft_id}`);
    } catch (error) {
      console.error("Error saving draft:", error);
      alert("Failed to save draft. Please try again.");
    }
  };

  const handlePublishBlog = async () => {
    if (!title.trim() || !blogContent.trim()) {
      alert("Please enter both title and content before publishing.");
      return;
    }

    try {
      const blog: BlogPost = {
        title: title.trim(),
        content: blogContent.trim(),
      };

      const result = await publishBlog(blog);
      alert(`Blog published successfully! Blog ID: ${result.blog_id}`);

      // Reset form after successful publish
      setTitle("");
      setBlogContent("");
    } catch (error) {
      console.error("Error publishing blog:", error);
      alert("Failed to publish blog. Please try again.");
    }
  };

  return (
    <div className="blog-editor">
      <div className="editor-header">
        <input
          type="text"
          placeholder="Enter blog title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="title-input"
        />
        <div className="editor-actions">
          <button onClick={handleSaveDraft} className="btn-secondary">
            Save Draft
          </button>
          <button onClick={handlePublishBlog} className="btn-primary">
            Publish
          </button>
        </div>
      </div>

      <div className="editor-content">
        <div className="editor-main">
          <textarea
            value={blogContent}
            onChange={handleContentChange}
            placeholder="Start writing your blog post..."
            className="content-editor"
            onSelect={(e) =>
              setCursorPosition(
                (e.target as HTMLTextAreaElement).selectionStart
              )
            }
          />
        </div>

        <div className="editor-sidebar">
          <div className="score-panel">
            <h3>Blog Score</h3>
            <div className="score-item">
              <span>Overall: </span>
              <span className="score-value">{score.overall}/100</span>
            </div>
            <div className="score-item">
              <span>Readability: </span>
              <span className="score-value">{score.readability}/100</span>
            </div>
            <div className="score-item">
              <span>Relevance: </span>
              <span className="score-value">{score.relevance}/100</span>
            </div>
            <div className="score-item">
              <span>Tokens Used: </span>
              <span className="score-value">{score.tokenUsage}</span>
            </div>
          </div>

          <div className="suggestions-panel">
            <h3>Keyword Suggestions</h3>
            {isAnalyzing ? (
              <div className="analyzing">Analyzing...</div>
            ) : (
              <div className="suggestions-list">
                {suggestions.map((suggestion, index) => (
                  <div key={index} className="suggestion-item">
                    <button
                      onClick={() => insertSuggestion(suggestion.word)}
                      className="suggestion-btn"
                    >
                      {suggestion.word}
                    </button>
                    <span className="relevance">
                      {Math.round(suggestion.relevance * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BlogEditor;
