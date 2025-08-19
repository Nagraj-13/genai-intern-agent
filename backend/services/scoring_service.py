import re
import math
import logging
from typing import Dict, List, Optional, Any
from collections import Counter
import asyncio
from datetime import datetime

from models import UserProfile, ScoreBreakdown

logger = logging.getLogger(__name__)

class BlogScoringService:
    """
    Comprehensive blog scoring system that combines multiple factors:
    1. Keyword relevance (semantic similarity and frequency)
    2. Readability metric (Flesch-Kincaid equivalent)
    3. User profile factors (preferred topics, reading level)
    4. Content structure and SEO optimization
    5. Engagement potential
    
    Score range: 0-100
    """
    
    def __init__(self):
        self.common_words = self._load_common_words()
        self.readability_weights = {
            "sentence_length": 0.3,
            "syllable_complexity": 0.25,
            "word_frequency": 0.2,
            "punctuation_usage": 0.15,
            "paragraph_structure": 0.1
        }
        
        logger.info("Blog Scoring Service initialized")
    
    def _load_common_words(self) -> set:
        """Load common English words for analysis"""
        # Common stop words and frequent words
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        return common_words
    
    async def calculate_comprehensive_score(
        self, 
        content: str, 
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive score for blog content"""
        try:
            logger.info("Calculating comprehensive blog score")
            
            # Calculate individual components
            keyword_score = await self._calculate_keyword_relevance(content, user_profile)
            readability_score = await self._calculate_readability_score(content, user_profile)
            profile_score = await self._calculate_user_profile_alignment(content, user_profile)
            structure_score = await self._calculate_content_structure_score(content)
            seo_score = await self._calculate_seo_score(content)
            engagement_score = await self._calculate_engagement_score(content)
            
            # Create score breakdown
            breakdown = ScoreBreakdown(
                keyword_relevance=keyword_score,
                readability=readability_score,
                user_profile_alignment=profile_score,
                content_structure=structure_score,
                seo_optimization=seo_score,
                engagement_potential=engagement_score
            )
            
            weights = {
                "keyword_relevance": 0.25,
                "readability": 0.20,
                "user_profile_alignment": 0.15,
                "content_structure": 0.15,
                "seo_optimization": 0.15,
                "engagement_potential": 0.10
            }
            
            overall_score = sum(
                getattr(breakdown, field) * weight
                for field, weight in weights.items()
            )
            
            recommendations = self._generate_recommendations(breakdown, content, user_profile)
            
            result = {
                "overall_score": round(overall_score, 2),
                "breakdown": breakdown.dict(),
                "recommendations": recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Score calculated: {overall_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive score: {str(e)}")
            raise
    
    async def _calculate_keyword_relevance(self, content: str, user_profile: Optional[UserProfile]) -> float:
        """Calculate keyword relevance score (0-100)"""
        try:
            words = self._extract_words(content)
            word_freq = Counter(words)
            total_words = len(words)
            
            if total_words == 0:
                return 0.0
            
            # Base keyword density score
            content_keywords = self._extract_potential_keywords(content)
            keyword_density = len(content_keywords) / total_words * 100
            
            density_score = 100 * (1 - abs(keyword_density - 2) / 10)
            density_score = max(0, min(100, density_score))
            
            # Keyword variety score
            unique_keywords = len(set(content_keywords))
            variety_score = min(100, unique_keywords * 5)  # Up to 20 unique keywords = 100
            
            # User profile relevance
            profile_relevance = 50  # Default neutral score
            if user_profile and user_profile.preferred_topics:
                content_lower = content.lower()
                topic_matches = sum(
                    1 for topic in user_profile.preferred_topics
                    if topic.lower() in content_lower
                )
                profile_relevance = min(100, topic_matches * 25)  # Up to 4 topics = 100
            
            # Combined keyword relevance score
            keyword_score = (density_score * 0.4 + variety_score * 0.35 + profile_relevance * 0.25)
            
            return round(keyword_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating keyword relevance: {str(e)}")
            return 50.0  # Default neutral score
    
    async def _calculate_readability_score(self, content: str, user_profile: Optional[UserProfile]) -> float:
        """Calculate readability score using Flesch-Kincaid equivalent (0-100)"""
        try:
            sentences = self._count_sentences(content)
            words = self._extract_words(content)
            syllables = sum(self._count_syllables(word) for word in words)
            
            if sentences == 0 or len(words) == 0:
                return 0.0
            
            # Flesch Reading Ease formula adaptation
            avg_sentence_length = len(words) / sentences
            avg_syllables_per_word = syllables / len(words)
            
            # Modified Flesch formula (higher = more readable)
            flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
            
            # Normalize to 0-100 scale
            flesch_score = max(0, min(100, flesch_score))
            
            # Additional readability factors
            paragraph_score = self._calculate_paragraph_structure_score(content)
            punctuation_score = self._calculate_punctuation_score(content)
            word_complexity_score = self._calculate_word_complexity_score(words)
            
            # User profile adjustment
            target_adjustment = 0
            if user_profile and user_profile.reading_level:
                if user_profile.reading_level == "beginner" and flesch_score < 60:
                    target_adjustment = (60 - flesch_score) * 0.5  # Boost for beginner-friendly content
                elif user_profile.reading_level == "advanced" and flesch_score > 40:
                    target_adjustment = (flesch_score - 40) * 0.3  # Reward complexity for advanced readers
            
            # Combined readability score
            readability_score = (
                flesch_score * 0.5 +
                paragraph_score * 0.2 +
                punctuation_score * 0.15 +
                word_complexity_score * 0.15 +
                target_adjustment
            )
            
            return round(max(0, min(100, readability_score)), 2)
            
        except Exception as e:
            logger.error(f"Error calculating readability score: {str(e)}")
            return 50.0
    
    async def _calculate_user_profile_alignment(self, content: str, user_profile: Optional[UserProfile]) -> float:
        """Calculate alignment with user profile (0-100)"""
        try:
            if not user_profile:
                return 50.0  # Neutral score when no profile
            
            alignment_scores = []
            
            # Topic alignment
            if user_profile.preferred_topics:
                content_lower = content.lower()
                topic_matches = sum(
                    1 for topic in user_profile.preferred_topics
                    if topic.lower() in content_lower
                )
                topic_score = min(100, (topic_matches / len(user_profile.preferred_topics)) * 100)
                alignment_scores.append(topic_score)
            
            # Writing style alignment
            style_score = self._calculate_style_alignment(content, user_profile.writing_style)
            alignment_scores.append(style_score)
            
            # Expertise area alignment
            if user_profile.expertise_areas:
                content_lower = content.lower()
                expertise_matches = sum(
                    1 for area in user_profile.expertise_areas
                    if area.lower() in content_lower
                )
                expertise_score = min(100, (expertise_matches / len(user_profile.expertise_areas)) * 100)
                alignment_scores.append(expertise_score)
            
            # Target audience alignment
            if user_profile.target_audience:
                audience_score = self._calculate_audience_alignment(content, user_profile.target_audience)
                alignment_scores.append(audience_score)
            
            # Average alignment score
            if alignment_scores:
                return round(sum(alignment_scores) / len(alignment_scores), 2)
            else:
                return 50.0
                
        except Exception as e:
            logger.error(f"Error calculating user profile alignment: {str(e)}")
            return 50.0
    
    async def _calculate_content_structure_score(self, content: str) -> float:
        """Calculate content structure and organization score (0-100)"""
        try:
            structure_scores = []
            
            # Paragraph distribution
            paragraphs = content.split('\n\n')
            paragraph_count = len([p for p in paragraphs if p.strip()])
            
            # Ideal: 3-8 paragraphs for most content
            if 3 <= paragraph_count <= 8:
                para_score = 100
            elif paragraph_count < 3:
                para_score = max(0, paragraph_count * 33.3)
            else:
                para_score = max(0, 100 - (paragraph_count - 8) * 10)
            
            structure_scores.append(para_score)
            
            # Sentence variety
            sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
            if sentences:
                sentence_lengths = [len(s.split()) for s in sentences]
                avg_length = sum(sentence_lengths) / len(sentence_lengths)
                length_variety = len(set(sentence_lengths)) / len(sentence_lengths)
                
                # Good average: 15-25 words per sentence
                length_score = 100 * (1 - abs(avg_length - 20) / 20)
                length_score = max(0, min(100, length_score))
                
                variety_score = length_variety * 100
                
                structure_scores.extend([length_score, variety_score])
            
            # Heading structure (simple detection)
            heading_indicators = len(re.findall(r'\n[A-Z][^.\n]*\n', content))
            heading_score = min(100, heading_indicators * 25)  # Up to 4 headings = 100
            structure_scores.append(heading_score)
            
            return round(sum(structure_scores) / len(structure_scores), 2)
            
        except Exception as e:
            logger.error(f"Error calculating content structure score: {str(e)}")
            return 50.0
    
    async def _calculate_seo_score(self, content: str) -> float:
        """Calculate SEO optimization score (0-100)"""
        try:
            seo_factors = []
            
            # Content length (800-2000 words is optimal for SEO)
            word_count = len(self._extract_words(content))
            if 800 <= word_count <= 2000:
                length_score = 100
            elif word_count < 800:
                length_score = (word_count / 800) * 100
            else:
                length_score = max(0, 100 - (word_count - 2000) / 100)
            
            seo_factors.append(length_score)
            
            # Keyword density (1-3% is optimal)
            keywords = self._extract_potential_keywords(content)
            keyword_density = (len(keywords) / max(1, word_count)) * 100
            
            if 1 <= keyword_density <= 3:
                density_score = 100
            else:
                density_score = max(0, 100 - abs(keyword_density - 2) * 25)
            
            seo_factors.append(density_score)
            
            # Meta content indicators
            has_title_like = bool(re.match(r'^.{10,60}$', content.split('\n')[0]))
            has_intro = len(content.split('\n\n')[0]) > 100 if '\n\n' in content else False
            has_conclusion = 'conclusion' in content.lower() or 'summary' in content.lower()
            
            meta_score = sum([has_title_like, has_intro, has_conclusion]) * 33.3
            seo_factors.append(meta_score)
            
            # Internal structure
            has_lists = bool(re.search(r'^\s*[\-\*\d+\.]\s+', content, re.MULTILINE))
            has_emphasis = bool(re.search(r'\*\*.*?\*\*|__.*?__|_.*?_|\*.*?\*', content))
            
            structure_score = sum([has_lists, has_emphasis]) * 50
            seo_factors.append(structure_score)
            
            return round(sum(seo_factors) / len(seo_factors), 2)
            
        except Exception as e:
            logger.error(f"Error calculating SEO score: {str(e)}")
            return 50.0
    
    async def _calculate_engagement_score(self, content: str) -> float:
        """Calculate potential engagement score (0-100)"""
        try:
            engagement_factors = []
            
            # Question usage (encourages interaction)
            question_count = len(re.findall(r'\?', content))
            word_count = len(self._extract_words(content))
            question_ratio = question_count / max(1, word_count / 100)  # Questions per 100 words
            
            question_score = min(100, question_ratio * 50)  # Optimal: 2 questions per 100 words
            engagement_factors.append(question_score)
            
            # Call-to-action indicators
            cta_patterns = [
                r'\bshare\b', r'\bcomment\b', r'\bsubscribe\b', r'\bfollow\b',
                r'\btry\b', r'\bstart\b', r'\blearn more\b', r'\bclick here\b'
            ]
            cta_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in cta_patterns)
            cta_score = min(100, cta_count * 25)
            engagement_factors.append(cta_score)
            
            # Emotional language
            positive_words = [
                'amazing', 'excellent', 'fantastic', 'great', 'wonderful',
                'inspiring', 'motivating', 'exciting', 'incredible', 'outstanding'
            ]
            negative_words = [
                'problem', 'challenge', 'difficult', 'struggle', 'issue',
                'mistake', 'error', 'failure', 'wrong', 'bad'
            ]
            
            content_lower = content.lower()
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            emotional_score = min(100, (positive_count + negative_count) * 10)
            engagement_factors.append(emotional_score)
            
            # Personal pronouns (creates connection)
            personal_pronouns = ['you', 'your', 'we', 'our', 'us', 'i', 'my']
            pronoun_count = sum(len(re.findall(rf'\b{pronoun}\b', content, re.IGNORECASE)) for pronoun in personal_pronouns)
            pronoun_score = min(100, pronoun_count * 5)
            engagement_factors.append(pronoun_score)
            
            return round(sum(engagement_factors) / len(engagement_factors), 2)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {str(e)}")
            return 50.0
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text"""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return [word for word in words if word not in self.common_words]
    
    def _extract_potential_keywords(self, text: str) -> List[str]:
        """Extract potential keywords (non-common words with length > 3)"""
        words = self._extract_words(text)
        return [word for word in words if len(word) > 3]
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text"""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_char_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_char_was_vowel:
                syllable_count += 1
            prev_char_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _calculate_paragraph_structure_score(self, content: str) -> float:
        """Calculate paragraph structure score"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return 0.0
        
        # Ideal paragraph length: 3-8 sentences
        scores = []
        for para in paragraphs:
            sentence_count = self._count_sentences(para)
            if 3 <= sentence_count <= 8:
                scores.append(100)
            elif sentence_count < 3:
                scores.append(sentence_count * 33.3)
            else:
                scores.append(max(0, 100 - (sentence_count - 8) * 10))
        
        return sum(scores) / len(scores)
    
    def _calculate_punctuation_score(self, content: str) -> float:
        """Calculate punctuation usage score"""
        punctuation_marks = ['.', ',', ';', ':', '!', '?']
        word_count = len(self._extract_words(content))
        
        if word_count == 0:
            return 0.0
        
        punct_count = sum(content.count(mark) for mark in punctuation_marks)
        punct_ratio = punct_count / word_count
        
        # Optimal punctuation ratio: 0.1 to 0.3
        if 0.1 <= punct_ratio <= 0.3:
            return 100.0
        elif punct_ratio < 0.1:
            return (punct_ratio / 0.1) * 100
        else:
            return max(0, 100 - (punct_ratio - 0.3) * 200)
    
    def _calculate_word_complexity_score(self, words: List[str]) -> float:
        """Calculate word complexity score"""
        if not words:
            return 0.0
        
        # Average word length
        avg_length = sum(len(word) for word in words) / len(words)
        
        # Optimal average word length: 4-7 characters
        if 4 <= avg_length <= 7:
            return 100.0
        elif avg_length < 4:
            return (avg_length / 4) * 100
        else:
            return max(0, 100 - (avg_length - 7) * 20)
    
    def _calculate_style_alignment(self, content: str, writing_style: str) -> float:
        """Calculate writing style alignment score"""
        content_lower = content.lower()
        
        if writing_style == "formal":
            # Look for formal indicators
            formal_indicators = ['therefore', 'furthermore', 'however', 'moreover', 'consequently']
            informal_indicators = ["don't", "won't", "can't", "it's", "we're"]
            
            formal_count = sum(1 for indicator in formal_indicators if indicator in content_lower)
            informal_count = sum(1 for indicator in informal_indicators if indicator in content_lower)
            
            return max(0, 50 + formal_count * 10 - informal_count * 5)
            
        elif writing_style == "casual":
            # Look for casual indicators
            casual_indicators = ["don't", "won't", "can't", "it's", "we're", "you'll", "i'll"]
            formal_indicators = ['therefore', 'furthermore', 'however', 'moreover']
            
            casual_count = sum(1 for indicator in casual_indicators if indicator in content_lower)
            formal_count = sum(1 for indicator in formal_indicators if indicator in content_lower)
            
            return max(0, 50 + casual_count * 8 - formal_count * 5)
            
        elif writing_style == "technical":
            # Look for technical indicators
            tech_indicators = ['algorithm', 'implementation', 'methodology', 'analysis', 'optimization']
            tech_count = sum(1 for indicator in tech_indicators if indicator in content_lower)
            
            return min(100, 50 + tech_count * 15)
            
        elif writing_style == "creative":
            # Look for creative indicators
            creative_indicators = ['imagine', 'picture', 'story', 'metaphor', 'analogy']
            creative_count = sum(1 for indicator in creative_indicators if indicator in content_lower)
            
            return min(100, 50 + creative_count * 12)
        
        return 50.0  # Default neutral score
    
    def _calculate_audience_alignment(self, content: str, target_audience: str) -> float:
        """Calculate target audience alignment score"""
        # Simple audience alignment based on vocabulary and tone
        content_lower = content.lower()
        
        audience_keywords = {
            'beginner': ['learn', 'start', 'basic', 'simple', 'easy', 'introduction'],
            'professional': ['strategy', 'business', 'professional', 'industry', 'market'],
            'technical': ['technical', 'system', 'implementation', 'configuration', 'development'],
            'academic': ['research', 'study', 'analysis', 'theory', 'methodology'],
            'general': ['help', 'guide', 'tips', 'advice', 'useful']
        }
        
        # Find best matching audience category
        best_match_score = 0
        for audience_type, keywords in audience_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            match_score = min(100, matches * 20)
            
            if target_audience.lower() in audience_type:
                best_match_score = max(best_match_score, match_score)
            elif audience_type == 'general':
                best_match_score = max(best_match_score, match_score * 0.7)
        
        return best_match_score
    
    def _generate_recommendations(self, breakdown: ScoreBreakdown, content: str, user_profile: Optional[UserProfile]) -> List[str]:
        """Generate actionable recommendations based on scores"""
        recommendations = []
        
        # Keyword relevance recommendations
        if breakdown.keyword_relevance < 60:
            recommendations.append("Consider adding more relevant keywords related to your main topic")
            if user_profile and user_profile.preferred_topics:
                recommendations.append(f"Include keywords related to: {', '.join(user_profile.preferred_topics[:3])}")
        
        # Readability recommendations
        if breakdown.readability < 60:
            recommendations.append("Improve readability by using shorter sentences and simpler words")
            recommendations.append("Break up long paragraphs into smaller, more digestible chunks")
        
        # Structure recommendations
        if breakdown.content_structure < 60:
            recommendations.append("Improve content structure with clear headings and logical flow")
            recommendations.append("Ensure paragraphs are 3-8 sentences long for optimal readability")
        
        # SEO recommendations
        if breakdown.seo_optimization < 60:
            word_count = len(self._extract_words(content))
            if word_count < 800:
                recommendations.append("Consider expanding content to 800-2000 words for better SEO")
            recommendations.append("Add meta descriptions, headings, and optimize keyword density")
        
        # Engagement recommendations
        if breakdown.engagement_potential < 60:
            recommendations.append("Add questions to encourage reader engagement")
            recommendations.append("Include calls-to-action to drive user interaction")
            recommendations.append("Use more personal pronouns (you, we, us) to connect with readers")
        
        # User profile specific recommendations
        if user_profile:
            if breakdown.user_profile_alignment < 60:
                if user_profile.writing_style == "formal":
                    recommendations.append("Use more formal language and avoid contractions")
                elif user_profile.writing_style == "casual":
                    recommendations.append("Adopt a more conversational tone with contractions and informal language")
                
                if user_profile.reading_level == "beginner":
                    recommendations.append("Simplify vocabulary and explain technical terms")
                elif user_profile.reading_level == "advanced":
                    recommendations.append("Include more sophisticated vocabulary and complex concepts")
        
        return recommendations[:8]  # Return top 8 recommendations
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for scoring service"""
        return {
            "status": "healthy",
            "components_loaded": bool(self.common_words),
            "weights_configured": bool(self.readability_weights),
            "last_check": datetime.utcnow().isoformat()
        }