import { useState } from "react";
import "./BlogAnalysis.css";
import { analyzeBlogPosts } from "../services/api"; // <-- import your API function

interface BlogAnalysisResult {
  id: string;
  title: string;
  content: string;
  sentiment: {
    positive: number;
    negative: number;
    neutral: number;
    overall: "positive" | "negative" | "neutral";
  };
  keyTopics: string[];
  keywordSuggestions: string[];
  tokenCount: number;
}

const BlogAnalysis = () => {
  const [blogTexts, setBlogTexts] = useState<string>("");
  const [analysisResults, setAnalysisResults] = useState<BlogAnalysisResult[]>(
    []
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const analyzeBlogTexts = async () => {
    if (!blogTexts.trim()) {
      alert("Please enter blog texts to analyze");
      return;
    }

    setIsAnalyzing(true);

    try {
      // Split input into blog posts (your UI expects "---" separator)
      const blogs = blogTexts.split("\n---\n").filter((blog) => blog.trim());

      // Call your backend API
      const apiResponse = await analyzeBlogPosts({
        blog_posts: blogs.map((content, i) => {
          const lines = content.trim().split("\n");
          return {
            title: lines[0] || `Blog Post ${i + 1}`,
            content: lines.slice(1).join("\n") || content,
          };
        }),
      });

      // Map API results to your UI format
      const formattedResults: BlogAnalysisResult[] = apiResponse.results.map(
        (r: any, idx: number) => {
          const content = blogs[idx] || "";
          const lines = content.trim().split("\n");
          const title = lines[0] || `Blog Post ${idx + 1}`;
          const body = lines.slice(1).join("\n") || content;

          return {
            id: r.blog_id || `blog-${idx + 1}`,
            title,
            content: body,
            sentiment: {
              positive: r.sentiment.positive_score,
              negative: r.sentiment.negative_score,
              neutral: r.sentiment.neutral_score,
              overall: r.sentiment.sentiment,
            },
            keyTopics: r.key_topics.map((t: any) => t.topic),
            keywordSuggestions: r.keyword_suggestions.map(
              (k: any) => k.keyword
            ),
            tokenCount:
              r.token_usage?.total_tokens ?? Math.floor(body.length / 4),
          };
        }
      );

      setAnalysisResults(formattedResults);
    } catch (error) {
      console.error("Error analyzing blogs:", error);
      alert("Failed to analyze blogs. Please check the console.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const clearResults = () => {
    setAnalysisResults([]);
    setBlogTexts("");
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "#28a745";
      case "negative":
        return "#dc3545";
      default:
        return "#6c757d";
    }
  };

  return (
    <div className="blog-analysis">
      <div className="analysis-header">
        <h2>Blog Analysis</h2>
        <p>
          Analyze existing blog posts for sentiment, key topics, and keyword
          suggestions
        </p>
      </div>

      <div className="input-section">
        <label htmlFor="blog-texts">
          Enter Blog Texts (separate multiple blogs with "---"):
        </label>
        <textarea
          id="blog-texts"
          value={blogTexts}
          onChange={(e) => setBlogTexts(e.target.value)}
          placeholder="Blog Title 1&#10;Blog content goes here...&#10;&#10;---&#10;&#10;Blog Title 2&#10;Another blog content..."
          className="blog-input"
          rows={10}
        />

        <div className="input-actions">
          <button
            onClick={analyzeBlogTexts}
            disabled={isAnalyzing}
            className="btn-primary"
          >
            {isAnalyzing ? "Analyzing..." : "Analyze Blogs"}
          </button>
          {analysisResults.length > 0 && (
            <button onClick={clearResults} className="btn-secondary">
              Clear Results
            </button>
          )}
        </div>
      </div>

      {analysisResults.length > 0 && (
        <div className="results-section">
          <h3>Analysis Results</h3>
          <div className="results-grid">
            {analysisResults.map((result) => (
              <div key={result.id} className="result-card">
                <div className="result-header">
                  <h4>{result.title}</h4>
                  <div
                    className="sentiment-badge"
                    style={{
                      backgroundColor: getSentimentColor(
                        result.sentiment.overall
                      ),
                    }}
                  >
                    {result.sentiment.overall}
                  </div>
                </div>

                <div className="result-content">
                  <div className="content-preview">
                    {result.content.substring(0, 150)}
                    {result.content.length > 150 && "..."}
                  </div>

                  <div className="metrics-section">
                    <div className="metric-group">
                      <h5>Sentiment Breakdown</h5>
                      <div className="sentiment-bars">
                        <div className="sentiment-bar">
                          <span>Positive:</span>
                          <div className="bar">
                            <div
                              className="bar-fill positive"
                              style={{
                                width: `${result.sentiment.positive * 100}%`,
                              }}
                            ></div>
                          </div>
                          <span>
                            {Math.round(result.sentiment.positive * 100)}%
                          </span>
                        </div>
                        <div className="sentiment-bar">
                          <span>Negative:</span>
                          <div className="bar">
                            <div
                              className="bar-fill negative"
                              style={{
                                width: `${result.sentiment.negative * 100}%`,
                              }}
                            ></div>
                          </div>
                          <span>
                            {Math.round(result.sentiment.negative * 100)}%
                          </span>
                        </div>
                        <div className="sentiment-bar">
                          <span>Neutral:</span>
                          <div className="bar">
                            <div
                              className="bar-fill neutral"
                              style={{
                                width: `${result.sentiment.neutral * 100}%`,
                              }}
                            ></div>
                          </div>
                          <span>
                            {Math.round(result.sentiment.neutral * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="metric-group">
                      <h5>Key Topics</h5>
                      <div className="topics-list">
                        {result.keyTopics.map((topic, index) => (
                          <span key={index} className="topic-tag">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="metric-group">
                      <h5>Keyword Suggestions</h5>
                      <div className="keywords-list">
                        {result.keywordSuggestions.map((keyword, index) => (
                          <span key={index} className="keyword-tag">
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="metric-group">
                      <h5>Token Count</h5>
                      <span className="token-count">
                        {result.tokenCount} tokens
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BlogAnalysis;
