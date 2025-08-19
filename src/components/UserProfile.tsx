import { useState, useEffect } from 'react'
import './UserProfile.css'
import { saveUserProfile, getUserProfile } from '../services/api'
import type { UserProfile as UserProfileType } from '../services/api'

interface UserProfileData {
  name: string
  email: string
  preferredTopics: string[]
  readingLevel: 'beginner' | 'intermediate' | 'advanced'
  writingStyle: 'formal' | 'casual' | 'technical'
  targetAudience: string
  specializations: string[]
}

const UserProfile = () => {
  const [profile, setProfile] = useState<UserProfileData>({
    name: '',
    email: '',
    preferredTopics: [],
    readingLevel: 'intermediate',
    writingStyle: 'formal',
    targetAudience: '',
    specializations: []
  })
  
  const [newTopic, setNewTopic] = useState('')
  const [newSpecialization, setNewSpecialization] = useState('')
  const [profileJson, setProfileJson] = useState('')
  const [showJson, setShowJson] = useState(false)

  // Update JSON when profile changes
  useEffect(() => {
    setProfileJson(JSON.stringify(profile, null, 2))
  }, [profile])

  const handleInputChange = (field: keyof UserProfileData, value: string) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const addTopic = () => {
    if (newTopic.trim() && !profile.preferredTopics.includes(newTopic.trim())) {
      setProfile(prev => ({
        ...prev,
        preferredTopics: [...prev.preferredTopics, newTopic.trim()]
      }))
      setNewTopic('')
    }
  }

  const removeTopic = (topic: string) => {
    setProfile(prev => ({
      ...prev,
      preferredTopics: prev.preferredTopics.filter(t => t !== topic)
    }))
  }

  const addSpecialization = () => {
    if (newSpecialization.trim() && !profile.specializations.includes(newSpecialization.trim())) {
      setProfile(prev => ({
        ...prev,
        specializations: [...prev.specializations, newSpecialization.trim()]
      }))
      setNewSpecialization('')
    }
  }

  const removeSpecialization = (specialization: string) => {
    setProfile(prev => ({
      ...prev,
      specializations: prev.specializations.filter(s => s !== specialization)
    }))
  }

  const handleSaveProfile = async () => {
    if (!profile.name.trim() || !profile.email.trim()) {
      alert('Please enter both name and email before saving.')
      return
    }

    try {
      const userProfile: UserProfileType = {
        user_id: Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15),
        name: profile.name.trim(),
        email: profile.email.trim(),
        preferredTopics: profile.preferredTopics,
        readingLevel: profile.readingLevel,
        writingStyle: profile.writingStyle,
        targetAudience: profile.targetAudience.trim(),
        specializations: profile.specializations
      }
      
      const result = await saveUserProfile(userProfile)
      localStorage.setItem('user', JSON.stringify(userProfile))
      alert(`Profile saved successfully! User ID: ${result.user_id}`)
    } catch (error) {
      console.error('Error saving profile:', error)
      alert('Failed to save profile. Please try again.')
    }
  }

  const handleLoadProfile = async () => {
    if (!profile.email.trim()) {
      alert('Please enter an email address to load profile.')
      return
    }

    try {
      const loadedProfile = await getUserProfile(profile.email.trim())
      setProfile({
        name: loadedProfile.name,
        email: loadedProfile.email,
        preferredTopics: loadedProfile.preferredTopics,
        readingLevel: loadedProfile.readingLevel,
        writingStyle: loadedProfile.writingStyle,
        targetAudience: loadedProfile.targetAudience,
        specializations: loadedProfile.specializations
      })
      alert('Profile loaded successfully!')
    } catch (error) {
      console.error('Error loading profile:', error)
      alert('Failed to load profile. User might not exist.')
    }
  }

  const loadFromJson = () => {
    try {
      const parsedProfile = JSON.parse(profileJson)
      setProfile(parsedProfile)
      alert('Profile loaded from JSON!')
    } catch (error) {
      alert('Invalid JSON format. Please check your JSON syntax.')
    }
  }

  const resetProfile = () => {
    setProfile({
      name: '',
      email: '',
      preferredTopics: [],
      readingLevel: 'intermediate',
      writingStyle: 'formal',
      targetAudience: '',
      specializations: []
    })
  }

  return (
    <div className="user-profile">
      <div className="profile-header">
        <h2>User Profile</h2>
        <p>Configure your preferences for personalized blog recommendations</p>
      </div>

      <div className="profile-content">
        <div className="profile-form">
          <div className="form-section">
            <h3>Basic Information</h3>
            
            <div className="form-group">
              <label htmlFor="name">Name:</label>
              <input
                type="text"
                id="name"
                value={profile.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="Enter your name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input
                type="email"
                id="email"
                value={profile.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                placeholder="Enter your email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="target-audience">Target Audience:</label>
              <input
                type="text"
                id="target-audience"
                value={profile.targetAudience}
                onChange={(e) => handleInputChange('targetAudience', e.target.value)}
                placeholder="e.g., Legal professionals, Students, General public"
              />
            </div>
          </div>

          <div className="form-section">
            <h3>Writing Preferences</h3>
            
            <div className="form-group">
              <label htmlFor="reading-level">Reading Level:</label>
              <select
                id="reading-level"
                value={profile.readingLevel}
                onChange={(e) => handleInputChange('readingLevel', e.target.value)}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="writing-style">Writing Style:</label>
              <select
                id="writing-style"
                value={profile.writingStyle}
                onChange={(e) => handleInputChange('writingStyle', e.target.value)}
              >
                <option value="formal">Formal</option>
                <option value="casual">Casual</option>
                <option value="technical">Technical</option>
              </select>
            </div>
          </div>

          <div className="form-section">
            <h3>Preferred Topics</h3>
            <div className="topic-input">
              <input
                type="text"
                value={newTopic}
                onChange={(e) => setNewTopic(e.target.value)}
                placeholder="Add a preferred topic"
                onKeyPress={(e) => e.key === 'Enter' && addTopic()}
              />
              <button onClick={addTopic} className="btn-add">Add</button>
            </div>
            <div className="tags-list">
              {profile.preferredTopics.map((topic, index) => (
                <span key={index} className="tag">
                  {topic}
                  <button onClick={() => removeTopic(topic)} className="tag-remove">×</button>
                </span>
              ))}
            </div>
          </div>

          <div className="form-section">
            <h3>Specializations</h3>
            <div className="specialization-input">
              <input
                type="text"
                value={newSpecialization}
                onChange={(e) => setNewSpecialization(e.target.value)}
                placeholder="Add a specialization"
                onKeyPress={(e) => e.key === 'Enter' && addSpecialization()}
              />
              <button onClick={addSpecialization} className="btn-add">Add</button>
            </div>
            <div className="tags-list">
              {profile.specializations.map((spec, index) => (
                <span key={index} className="tag specialization-tag">
                  {spec}
                  <button onClick={() => removeSpecialization(spec)} className="tag-remove">×</button>
                </span>
              ))}
            </div>
          </div>

          <div className="form-actions">
            <button onClick={handleSaveProfile} className="btn-primary">
              Save Profile
            </button>
            <button onClick={handleLoadProfile} className="btn-secondary">
              Load Profile
            </button>
            <button onClick={resetProfile} className="btn-secondary">
              Reset
            </button>
            <button 
              onClick={() => setShowJson(!showJson)} 
              className="btn-secondary"
            >
              {showJson ? 'Hide' : 'Show'} JSON
            </button>
          </div>
        </div>

        {showJson && (
          <div className="json-section">
            <h3>Profile JSON</h3>
            <p className="json-description">
              This JSON will be sent to the backend APIs for personalized recommendations
            </p>
            <textarea
              value={profileJson}
              onChange={(e) => setProfileJson(e.target.value)}
              className="json-editor"
              rows={15}
            />
            <div className="json-actions">
              <button onClick={loadFromJson} className="btn-primary">
                Load from JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default UserProfile
