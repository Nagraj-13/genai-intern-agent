import { useState } from 'react'
import './App.css'
import BlogEditor from './components/BlogEditor'
import BlogAnalysis from './components/BlogAnalysis'
import UserProfile from './components/UserProfile'
import BlogList from './components/BlogList'

function App() {
  const [activeTab, setActiveTab] = useState<'editor' | 'analysis' | 'profile' | 'blogs'>('editor')

  return (
    <div className="app">
      <header className="app-header">
        <h1>LawVriksh Blog Platform</h1>
        <nav className="nav-tabs">
          <button
            className={activeTab === 'editor' ? 'active' : ''}
            onClick={() => setActiveTab('editor')}
          >
            Blog Editor
          </button>
          <button
            className={activeTab === 'analysis' ? 'active' : ''}
            onClick={() => setActiveTab('analysis')}
          >
            Blog Analysis
          </button>
          <button
            className={activeTab === 'blogs' ? 'active' : ''}
            onClick={() => setActiveTab('blogs')}
          >
            Published Blogs
          </button>
          <button
            className={activeTab === 'profile' ? 'active' : ''}
            onClick={() => setActiveTab('profile')}
          >
            User Profile
          </button>
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'editor' && <BlogEditor />}
        {activeTab === 'analysis' && <BlogAnalysis />}
        {activeTab === 'blogs' && <BlogList />}
        {activeTab === 'profile' && <UserProfile />}
      </main>
    </div>
  )
}

export default App
