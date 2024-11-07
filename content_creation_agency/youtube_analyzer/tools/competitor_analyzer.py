from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import List

load_dotenv()

class CompetitorAnalyzer(BaseTool):
    """
    Analyzes competitor YouTube channels and their content strategies
    """
    competitor_channels: List[str] = Field(
        ..., 
        description="List of competitor channel IDs to analyze"
    )
    days_back: int = Field(
        default=90,
        description="Number of days back to analyze"
    )
    min_views: int = Field(
        default=1000,
        description="Minimum views threshold for video analysis"
    )

    def run(self):
        """
        Performs comprehensive competitor analysis using YouTube Data API
        """
        youtube = build('youtube', 'v3', 
                       developerKey=os.getenv('YOUTUBE_API_KEY'))
        
        results = {
            "channel_comparisons": {},
            "content_analysis": {},
            "top_performing_content": {},
            "upload_patterns": {},
            "engagement_metrics": {},
            "growth_metrics": {}
        }
        
        for channel_id in self.competitor_channels:
            try:
                # Get channel details
                channel_response = youtube.channels().list(
                    part='statistics,snippet,brandingSettings,contentDetails',
                    id=channel_id
                ).execute()
                
                if not channel_response['items']:
                    continue
                
                channel_data = channel_response['items'][0]
                
                # Get recent videos
                date_threshold = (datetime.now() - timedelta(days=self.days_back)).isoformat() + 'Z'
                
                videos_response = youtube.search().list(
                    part='id,snippet',
                    channelId=channel_id,
                    order='date',
                    type='video',
                    publishedAfter=date_threshold,
                    maxResults=50
                ).execute()
                
                # Analyze videos
                video_data = []
                for video in videos_response.get('items', []):
                    video_id = video['id']['videoId']
                    stats = youtube.videos().list(
                        part='statistics,contentDetails,snippet',
                        id=video_id
                    ).execute()
                    
                    if stats['items']:
                        video_stats = stats['items'][0]
                        if int(video_stats['statistics'].get('viewCount', 0)) >= self.min_views:
                            video_data.append({
                                'title': video['snippet']['title'],
                                'description': video['snippet']['description'],
                                'published_at': video['snippet']['publishedAt'],
                                'views': int(video_stats['statistics'].get('viewCount', 0)),
                                'likes': int(video_stats['statistics'].get('likeCount', 0)),
                                'comments': int(video_stats['statistics'].get('commentCount', 0)),
                                'duration': video_stats['contentDetails']['duration'],
                                'tags': video_stats['snippet'].get('tags', [])
                            })
                
                # Convert to DataFrame for analysis
                df = pd.DataFrame(video_data)
                if not df.empty:
                    df['published_at'] = pd.to_datetime(df['published_at'])
                    df['engagement_rate'] = ((df['likes'] + df['comments']) / df['views'] * 100).round(2)
                    
                    # Analyze upload patterns
                    df['day_of_week'] = df['published_at'].dt.day_name()
                    df['hour_of_day'] = df['published_at'].dt.hour
                    
                    # Store results
                    results["channel_comparisons"][channel_id] = {
                        'name': channel_data['snippet']['title'],
                        'subscribers': int(channel_data['statistics']['subscriberCount']),
                        'total_views': int(channel_data['statistics']['viewCount']),
                        'total_videos': int(channel_data['statistics']['videoCount']),
                        'avg_views_per_video': int(df['views'].mean()),
                        'avg_engagement_rate': float(df['engagement_rate'].mean())
                    }
                    
                    results["content_analysis"][channel_id] = {
                        'common_tags': self._analyze_tags(df),
                        'title_patterns': self._analyze_titles(df),
                        'description_patterns': self._analyze_descriptions(df)
                    }
                    
                    results["top_performing_content"][channel_id] = df.nlargest(
                        5, 'views'
                    )[['title', 'views', 'engagement_rate']].to_dict('records')
                    
                    results["upload_patterns"][channel_id] = {
                        'best_days': df.groupby('day_of_week')['views'].mean().nlargest(3).to_dict(),
                        'best_hours': df.groupby('hour_of_day')['views'].mean().nlargest(3).to_dict(),
                        'upload_frequency': f"{len(df) / (self.days_back / 30):.1f} videos per month"
                    }
                    
                    results["engagement_metrics"][channel_id] = {
                        'avg_likes_per_view': (df['likes'] / df['views']).mean(),
                        'avg_comments_per_view': (df['comments'] / df['views']).mean(),
                        'engagement_trend': df.sort_values('published_at')
                            .set_index('published_at')['engagement_rate'].rolling('30D').mean().to_dict()
                    }
                    
            except Exception as e:
                results["errors"] = results.get("errors", {})
                results["errors"][channel_id] = str(e)
        
        return results
    
    def _analyze_tags(self, df):
        """Analyzes common tags and their performance"""
        all_tags = []
        for tags in df['tags']:
            all_tags.extend(tags)
        
        tag_counts = Counter(all_tags)
        return dict(tag_counts.most_common(10))
    
    def _analyze_titles(self, df):
        """Analyzes title patterns and their effectiveness"""
        title_words = []
        for title in df['title']:
            title_words.extend(title.lower().split())
        
        word_counts = Counter(title_words)
        return dict(word_counts.most_common(10))
    
    def _analyze_descriptions(self, df):
        """Analyzes description patterns"""
        desc_words = []
        for desc in df['description']:
            desc_words.extend(desc.lower().split())
        
        word_counts = Counter(desc_words)
        return dict(word_counts.most_common(10))

if __name__ == "__main__":
    tool = CompetitorAnalyzer(
        competitor_channels=["example_channel_id1", "example_channel_id2"],
        days_back=90,
        min_views=1000
    )
    print(tool.run()) 