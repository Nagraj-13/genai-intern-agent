# LawVriksh Blog Platform - Frontend

This is a basic React frontend for the GenAI Assignment blog platform. The frontend is ready for backend integration and provides all the necessary interfaces for the agentic blog support system.

## Features

### 1. Blog Editor
- Rich text editor for writing blog posts
- Real-time keyword suggestions display
- Blog scoring metrics (Overall, Readability, Relevance, Token Usage)
- Draft saving and publishing functionality
- Cursor position tracking for contextual recommendations

### 2. Blog Analysis
- Interface to analyze existing blog posts
- Displays sentiment metrics (positive, negative, neutral)
- Shows extracted key topics
- Presents keyword suggestions
- Token count tracking

### 3. User Profile Management
- User preferences configuration
- Preferred topics and specializations
- Reading level and writing style settings
- JSON export/import for API integration

## Getting Started

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn

### Installation
```bash
npm install
```

### Development
```bash
npm run dev
```

### Build
```bash
npm run build
```

## Backend Integration

### API Endpoints to Implement

The frontend is designed to work with these backend endpoints:

#### 1. POST /api/analyze-blogs
**Request:**
```json
{
  "blogs": ["blog content 1", "blog content 2"]
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "blog-1",
      "sentiment": {
        "positive": 0.7,
        "negative": 0.1,
        "neutral": 0.2,
        "overall": "positive"
      },
      "keyTopics": ["Legal Technology", "Compliance"],
      "keywordSuggestions": ["legal tech", "compliance"],
      "tokenCount": 150
    }
  ]
}
```

#### 2. POST /api/recommend-keywords
**Request:**
```json
{
  "draftText": "Current blog draft content...",
  "cursorContext": "optional cursor context",
  "userProfile": {
    "name": "User Name",
    "preferredTopics": ["Legal Tech"],
    "readingLevel": "intermediate",
    "writingStyle": "formal"
  }
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "word": "legal framework",
      "relevance": 0.9,
      "position": 45
    }
  ],
  "readabilityScore": 85,
  "relevanceScore": 78,
  "tokenUsage": 120
}
```

### Integration Points

1. **API Service File**: `src/services/api.ts`
   - Contains all API function templates
   - Update `API_BASE_URL` and `API_KEY` constants
   - Implement the actual API calls replacing mock functions

2. **Authentication**: 
   - Currently set up for Bearer JWT or API Key authentication
   - Update headers in `api.ts` as needed

3. **Error Handling**:
   - Retry logic with exponential backoff is provided
   - Customize error handling as needed

4. **Real-time Features**:
   - BlogEditor component has useEffect hooks for real-time analysis
   - Replace mock implementations with actual API calls

## File Structure

```
src/
├── components/
│   ├── BlogEditor.tsx       # Main blog writing interface
│   ├── BlogEditor.css
│   ├── BlogAnalysis.tsx     # Blog analysis interface
│   ├── BlogAnalysis.css
│   ├── UserProfile.tsx      # User profile management
│   └── UserProfile.css
├── services/
│   └── api.ts              # API integration layer
├── App.tsx                 # Main application component
├── App.css
├── index.css               # Global styles
└── main.tsx               # Application entry point
```

## Key Features for Backend Integration

### 1. Real-time Keyword Suggestions
- Triggers API calls as user types (with debouncing)
- Displays suggestions in sidebar
- Allows insertion of suggestions at cursor position

### 2. Blog Scoring System
- Real-time scoring updates
- Displays multiple metrics (0-100 scale)
- Token usage tracking

### 3. User Profile Integration
- JSON export for API requests
- Configurable preferences
- Profile-based recommendations

### 4. Agentic Workflow Support
- Cursor context tracking
- Real-time analysis triggers
- Weak section highlighting (ready for implementation)

## Mock Data

The frontend currently uses mock data for development. Replace these with actual API calls:

- `mockAnalyzeBlogPosts()` in `api.ts`
- `mockGetKeywordRecommendations()` in `api.ts`
- Mock scoring logic in `BlogEditor.tsx`

## Styling

- Clean, professional design
- Responsive layout
- Consistent color scheme
- Accessible form controls
- Mobile-friendly interface

## Notes for Candidates

1. **Focus on Backend**: This frontend is provided so you can focus on building the backend APIs and agentic systems.

2. **API Integration**: Update the `src/services/api.ts` file with your backend URL and implement the actual API calls.

3. **Authentication**: Implement your chosen authentication method (API Key or JWT) in the API service.

4. **Testing**: Use this frontend to test your backend endpoints and agentic workflow.

5. **Customization**: Feel free to modify the frontend if needed for your specific implementation.

## Assignment Requirements Covered

✅ Blog writing interface with real-time suggestions  
✅ Blog analysis for existing posts  
✅ User profile management  
✅ API integration points for both required endpoints  
✅ Real-time scoring display  
✅ Token usage tracking  
✅ Cursor context for recommendations  
✅ Authentication ready  
✅ Error handling and retry logic  

The frontend is designed to showcase all the features mentioned in the assignment requirements. Focus your development efforts on the backend APIs, LLM integration, and agentic workflow implementation.
