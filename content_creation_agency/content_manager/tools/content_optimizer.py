from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import openai
from typing import Dict, List
import pandas as pd
from datetime import datetime
import json
from textblob import TextBlob
import re
from collections import Counter

load_dotenv()

class ContentOptimizer(BaseTool):
    """
    Optimizes content for SEO, engagement, and platform-specific best practices
    """
    content: Dict = Field(
        ..., 
        description="Content to optimize (title, description, tags, script)"
    )
    platform: str = Field(
        default="youtube",
        description="Target platform (youtube, twitter, etc.)"
    )
    competitor_data: Dict = Field(
        default={},
        description="Optional competitor analysis data"
    )
    performance_data: Dict = Field(
        default={},
        description="Optional historical performance data"
    )

    def run(self):
        """
        Optimizes content using multiple optimization strategies
        """
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        results = {
            "optimized_content": {},
            "seo_analysis": {},
            "engagement_predictions": {},
            "recommendations": {},
            "metadata": {}
        }
        
        # 1. SEO Optimization
        seo_results = self._optimize_seo(self.content)
        results["seo_analysis"] = seo_results
        
        # 2. Title Optimization
        if "title" in self.content:
            optimized_title = self._optimize_title(
                self.content["title"],
                seo_results,
                self.competitor_data
            )
            results["optimized_content"]["title"] = optimized_title
        
        # 3. Description Optimization
        if "description" in self.content:
            optimized_description = self._optimize_description(
                self.content["description"],
                seo_results
            )
            results["optimized_content"]["description"] = optimized_description
        
        # 4. Tag Optimization
        if "tags" in self.content:
            optimized_tags = self._optimize_tags(
                self.content["tags"],
                seo_results,
                self.competitor_data
            )
            results["optimized_content"]["tags"] = optimized_tags
        
        # 5. Script Optimization
        if "script" in self.content:
            optimized_script = self._optimize_script(
                self.content["script"],
                self.platform
            )
            results["optimized_content"]["script"] = optimized_script
        
        # 6. Engagement Prediction
        results["engagement_predictions"] = self._predict_engagement(
            results["optimized_content"],
            self.performance_data
        )
        
        # 7. Generate Recommendations
        results["recommendations"] = self._generate_recommendations(
            results["seo_analysis"],
            results["engagement_predictions"]
        )
        
        # 8. Add Metadata
        results["metadata"] = {
            "optimization_timestamp": datetime.now().isoformat(),
            "platform": self.platform,
            "optimization_version": "1.0"
        }
        
        return results
    
    def _optimize_seo(self, content):
        """Analyzes and optimizes content for SEO"""
        seo_analysis = {
            "keyword_density": {},
            "readability_score": 0,
            "seo_score": 0,
            "improvement_areas": []
        }
        
        # Combine all text content for analysis
        all_text = " ".join([
            content.get("title", ""),
            content.get("description", ""),
            content.get("script", "")
        ])
        
        # Calculate keyword density
        words = re.findall(r'\w+', all_text.lower())
        word_freq = Counter(words)
        total_words = len(words)
        
        seo_analysis["keyword_density"] = {
            word: count/total_words * 100
            for word, count in word_freq.most_common(10)
        }
        
        # Calculate readability
        blob = TextBlob(all_text)
        seo_analysis["readability_score"] = self._calculate_readability(blob)
        
        # Calculate SEO score and identify improvements
        seo_score = 0
        improvements = []
        
        # Title analysis
        if "title" in content:
            title_length = len(content["title"])
            if title_length < 30:
                improvements.append("Title is too short (< 30 characters)")
            elif title_length > 60:
                improvements.append("Title is too long (> 60 characters)")
            else:
                seo_score += 25
        
        # Description analysis
        if "description" in content:
            desc_length = len(content["description"])
            if desc_length < 100:
                improvements.append("Description is too short (< 100 characters)")
            elif desc_length > 5000:
                improvements.append("Description is too long (> 5000 characters)")
            else:
                seo_score += 25
        
        # Tags analysis
        if "tags" in content:
            if len(content["tags"]) < 5:
                improvements.append("Add more tags (minimum 5 recommended)")
            else:
                seo_score += 25
        
        # Keyword usage analysis
        if seo_analysis["keyword_density"]:
            max_density = max(seo_analysis["keyword_density"].values())
            if max_density > 5:
                improvements.append("Keyword stuffing detected (density > 5%)")
            elif max_density < 0.5:
                improvements.append("Main keyword usage is too low (< 0.5%)")
            else:
                seo_score += 25
        
        seo_analysis["seo_score"] = seo_score
        seo_analysis["improvement_areas"] = improvements
        
        return seo_analysis
    
    def _optimize_title(self, title, seo_results, competitor_data):
        """Optimizes title based on SEO and competitor analysis"""
        # Implementation details...
        return title
    
    def _optimize_description(self, description, seo_results):
        """Optimizes description for better engagement and SEO"""
        # Implementation details...
        return description
    
    def _optimize_tags(self, tags, seo_results, competitor_data):
        """Optimizes tags based on SEO and competitor analysis"""
        # Implementation details...
        return tags
    
    def _optimize_script(self, script, platform):
        """Optimizes script for the target platform"""
        # Implementation details...
        return script
    
    def _predict_engagement(self, optimized_content, performance_data):
        """Predicts engagement metrics for the optimized content"""
        # Implementation details...
        return {}
    
    def _generate_recommendations(self, seo_analysis, engagement_predictions):
        """Generates actionable recommendations for content improvement"""
        # Implementation details...
        return {}
    
    def _calculate_readability(self, blob):
        """Calculates readability score using TextBlob"""
        sentences = len(blob.sentences)
        words = len(blob.words)
        syllables = sum(self._count_syllables(word) for word in blob.words)
        
        if sentences == 0 or words == 0:
            return 0
        
        # Calculate Flesch Reading Ease score
        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        return min(max(score, 0), 100)  # Clamp between 0 and 100
    
    def _count_syllables(self, word):
        """Counts syllables in a word"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        prev_char_is_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_char_is_vowel:
                count += 1
            prev_char_is_vowel = is_vowel
        
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count = 1
        return count

if __name__ == "__main__":
    test_content = {
        "title": "10 Amazing AI Tools You Need to Try",
        "description": "Discover the most powerful AI tools that are revolutionizing...",
        "tags": ["AI", "Technology", "Tools"],
        "script": "Hello everyone, today we're exploring..."
    }
    
    tool = ContentOptimizer(
        content=test_content,
        platform="youtube",
        competitor_data={},
        performance_data={}
    )
    print(tool.run()) 