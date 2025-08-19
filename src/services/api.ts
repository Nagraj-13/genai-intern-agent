// API Service for Backend Integration
// Candidates should implement these functions to connect to their backend APIs

const API_BASE_URL = 'http://localhost:8000/api' // Update with your backend URL
const API_KEY = 'dev-api-key-genai-blog-system' // Update with your API key

// Blog and User Profile Types
export interface BlogPost {
  id?: number
  title: string
  content: string
  user_id?: number
  author_name?: string
  author_email?: string
  created_at?: string
  updated_at?: string
}

export interface UserProfile {
  name: string
  email: string
  user_id: string
  preferredTopics: string[]
  readingLevel: 'beginner' | 'intermediate' | 'advanced'
  writingStyle: 'formal' | 'casual' | 'technical'
  targetAudience: string
  specializations: string[]
}

export interface Draft {
  id?: number
  title: string
  content: string
  user_id?: number
  author_name?: string
  author_email?: string
  created_at?: string
  updated_at?: string
}

// Types for API requests and responses
export interface BlogAnalysisRequest {
  blog_posts: {
    title: string
    content: string
  }[]
}


export interface BlogAnalysisResponse {
  results: Array<{
    id: string
    sentiment: {
      positive: number
      negative: number
      neutral: number
      overall: 'positive' | 'negative' | 'neutral'
    }
    keyTopics: string[]
    keywordSuggestions: string[]
    tokenCount: number
  }>
}

export interface KeywordRecommendationRequest {
  current_draft: string
  cursor_context: string
  user_profile: object
}

export interface KeywordRecommendationResponse {
  suggestions: Array<{
    word: string
    relevance: number
    position?: number
  }>
  readabilityScore: number
  relevanceScore: number
  tokenUsage: number
}



// services/api.ts (partial — add/replace the below)

export interface RawKeywordItem {
  keyword: string
  relevance_score?: number
  position_suggestion?: number
  context?: string
  semantic_similarity?: number
}

export interface RawWeakSection {
  start_position: number
  end_position: number
  issue_type: string
  severity: string
  suggestion: string
  confidence?: number
}

export interface RawTokenUsage {
  prompt_tokens?: number
  completion_tokens?: number
  total_tokens?: number
  cost_estimate?: number
  model_used?: string
}

export interface RawKeywordRecommendationResponse {
  // the primary items you showed
  keywords?: RawKeywordItem[]
  realtime_score?: {
    overall_score?: number
    readability_score?: number
    relevance_score?: number
    engagement_score?: number
    seo_score?: number
  }
  weak_sections?: RawWeakSection[]
  token_usage?: RawTokenUsage
  suggestions_context?: string
  timestamp?: string

  // ALSO accept the canonical form if backend already returns it:
  // suggestions: [{ word, relevance, position? }], readabilityScore, relevanceScore, tokenUsage
  suggestions?: Array<{ word: string; relevance: number; position?: number }>
  readabilityScore?: number
  relevanceScore?: number
  tokenUsage?: number
}

// Canonical shape your UI expects
export interface KeywordRecommendationResponse {
  suggestions: Array<{
    word: string
    relevance: number
    position?: number
  }>
  readabilityScore: number
  relevanceScore: number
  tokenUsage: number
}

/**
 * Normalizer: convert whatever backend returns into KeywordRecommendationResponse
 */
const normalizeKeywordResponse = (raw: RawKeywordRecommendationResponse): KeywordRecommendationResponse => {
  // If backend already returned canonical shape, use it
  if (raw.suggestions && Array.isArray(raw.suggestions)) {
    return {
      suggestions: raw.suggestions.map(s => ({
        word: s.word,
        relevance: typeof s.relevance === 'number' ? s.relevance : 0,
        position: s.position
      })),
      readabilityScore: Math.round(raw.readabilityScore ?? 0),
      relevanceScore: Math.round(raw.relevanceScore ?? 0),
      tokenUsage: raw.tokenUsage ?? 0
    }
  }

  // Otherwise map the raw 'keywords' + 'realtime_score' shape to canonical
  const keywords = Array.isArray(raw.keywords) ? raw.keywords : []

  const suggestions = keywords.map(k => ({
    word: k.keyword,
    relevance: typeof k.relevance_score === 'number' ? k.relevance_score : 0,
    position: k.position_suggestion
  }))

  const realtime = raw.realtime_score ?? {}
  const tokenUsage = raw.token_usage?.total_tokens ?? raw.tokenUsage ?? 0

  return {
    suggestions,
    readabilityScore: Math.round(realtime.readability_score ?? 0),
    relevanceScore: Math.round(realtime.relevance_score ?? 0),
    tokenUsage: tokenUsage
  }
}
// API Functions - Candidates should implement these

/**
 * Analyze multiple blog posts for sentiment, topics, and keywords
 * POST /api/analyze-blogs
 */
export const analyzeBlogPosts = async (request: BlogAnalysisRequest): Promise<BlogAnalysisResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze-blogs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`, // or 'X-API-Key': API_KEY
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error analyzing blog posts:', error)
    throw error
  }
}

/**
 * Get keyword recommendations for current draft
 * POST /api/recommend-keywords
 */
export const getKeywordRecommendations = async (request: KeywordRecommendationRequest): Promise<KeywordRecommendationResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/recommend-keywords`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`, // or 'X-API-Key': API_KEY
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const raw: RawKeywordRecommendationResponse = await response.json()
    return normalizeKeywordResponse(raw)
  } catch (error) {
    console.error('Error getting keyword recommendations:', error)
    throw error
  }
}

/**
 * Retry logic with exponential backoff
 * Candidates should implement this for handling intermittent failures
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: Error

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error

      if (attempt === maxRetries) {
        break
      }

      // Exponential backoff: 1s, 2s, 4s
      const delay = baseDelay * Math.pow(2, attempt)
      console.log(`Attempt ${attempt + 1} failed, retrying in ${delay}ms...`)

      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError!
}

/**
 * Example usage with retry logic:
 * 
 * const analyzeWithRetry = () => retryWithBackoff(() => 
 *   analyzeBlogPosts({ blogs: ['blog content'] })
 * )
 * 
 * const recommendWithRetry = () => retryWithBackoff(() => 
 *   getKeywordRecommendations({ 
 *     draftText: 'current draft', 
 *     userProfile: {} 
 *   })
 * )
 */

// Mock implementations for development (remove when backend is ready)
export const mockAnalyzeBlogPosts = async (
  request: BlogAnalysisRequest
): Promise<BlogAnalysisResponse> => {
  await new Promise(resolve => setTimeout(resolve, 1500))

  return {
    results: request.blog_posts.map((blog, index) => ({
      id: `blog-${index + 1}`,
      sentiment: {
        positive: Math.random() * 0.6 + 0.2,
        negative: Math.random() * 0.3,
        neutral: Math.random() * 0.4 + 0.1,
        overall: Math.random() > 0.5 ? 'positive' : 'neutral'
      },
      keyTopics: ['Legal Technology', 'Compliance', 'Digital Transformation'],
      keywordSuggestions: ['legal tech', 'compliance', 'digital law'],
      tokenCount: Math.floor(blog.content.length / 4)
    }))
  }
}

export const mockGetKeywordRecommendations = async (request: KeywordRecommendationRequest): Promise<KeywordRecommendationResponse> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 800))

  return {
    suggestions: [
      { word: 'legal framework', relevance: 0.9 },
      { word: 'compliance', relevance: 0.8 },
      { word: 'regulatory', relevance: 0.7 }
    ],
    readabilityScore: Math.min(90, request.current_draft.length / 8),
    relevanceScore: Math.min(80, request.current_draft.length / 12),
    tokenUsage: Math.floor(request.current_draft.length / 4)
  }
}

// =============================================================================
// BLOG AND USER PROFILE API FUNCTIONS
// =============================================================================

/**
 * User Profile API Functions
 */

export const saveUserProfile = async (profile: UserProfile): Promise<{ message: string; user_id: number }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profile),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error saving user profile:', error)
    throw error
  }
}

export const getUserProfile = async (email: string): Promise<UserProfile> => {
  try {
    const response = await fetch(`${API_BASE_URL}/users/${encodeURIComponent(email)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error getting user profile:', error)
    throw error
  }
}

/**
 * Blog API Functions
 */

export const publishBlog = async (blog: BlogPost): Promise<{ message: string; blog_id: number }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/blogs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(blog),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error publishing blog:', error)
    throw error
  }
}

export const getAllBlogs = async (): Promise<{ blogs: BlogPost[]; total: number }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/blogs`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error getting blogs:', error)
    throw error
  }
}

export const getBlog = async (blogId: number): Promise<BlogPost> => {
  try {
    const response = await fetch(`${API_BASE_URL}/blogs/${blogId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error getting blog:', error)
    throw error
  }
}

export const updateBlog = async (blogId: number, blog: Partial<BlogPost>): Promise<{ message: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/blogs/${blogId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(blog),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error updating blog:', error)
    throw error
  }
}

export const deleteBlog = async (blogId: number): Promise<{ message: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/blogs/${blogId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error deleting blog:', error)
    throw error
  }
}

/**
 * Draft API Functions
 */

export const saveDraft = async (draft: Draft): Promise<{ message: string; draft_id: number }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/drafts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(draft),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error saving draft:', error)
    throw error
  }
}

export const getAllDrafts = async (userId?: number): Promise<{ drafts: Draft[]; total: number }> => {
  try {
    const url = userId
      ? `${API_BASE_URL}/drafts?user_id=${userId}`
      : `${API_BASE_URL}/drafts`

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error getting drafts:', error)
    throw error
  }
}

/**
 * Health Check
 */

export const checkBackendHealth = async (): Promise<{ status: string; message: string; timestamp: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Error checking backend health:', error)
    throw error
  }
}
