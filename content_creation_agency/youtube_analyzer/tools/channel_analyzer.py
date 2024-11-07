from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pandas as pd

load_dotenv()

CHANNEL_ID = "UCSv4qL8vmoSH7GaPjuqRiCQ"

class ChannelAnalyzer(BaseTool):
    """
    Analyzes YouTube channel performance and demographics, including video metrics,
    engagement rates, and performance trends.
    """
    days_back: int = Field(
        default=30,
        description="Number of days back to analyze"
    )
    include_comments: bool = Field(
        default=True,
        description="Whether to include comment analysis"
    )

    def run(self):
        """
        Analyzes channel performance using YouTube Data API with enhanced metrics
        """
        youtube = build('youtube', 'v3', 
                       developerKey=os.getenv('YOUTUBE_API_KEY'))
        
        # Get channel statistics and details
        channel_response = youtube.channels().list(
            part='statistics,snippet,brandingSettings,contentDetails',
            id=CHANNEL_ID
        ).execute()
        
        # Get recent videos
        date_threshold = (datetime.now() - timedelta(days=self.days_back)).isoformat() + 'Z'
        
        videos_response = youtube.search().list(
            part='id,snippet',
            channelId=CHANNEL_ID,
            order='date',
            type='video',
            publishedAfter=date_threshold,
            maxResults=50
        ).execute()

        # Get detailed video statistics
        video_stats = []
        for video in videos_response.get('items', []):
            video_id = video['id']['videoId']
            stats = youtube.videos().list(
                part='statistics,contentDetails',
                id=video_id
            ).execute()
            
            if stats['items']:
                video_stats.append({
                    'title': video['snippet']['title'],
                    'published_at': video['snippet']['publishedAt'],
                    'video_id': video_id,
                    'views': int(stats['items'][0]['statistics'].get('viewCount', 0)),
                    'likes': int(stats['items'][0]['statistics'].get('likeCount', 0)),
                    'comments': int(stats['items'][0]['statistics'].get('commentCount', 0)),
                    'duration': stats['items'][0]['contentDetails']['duration']
                })

                # Add comment analysis if requested
                if self.include_comments:
                    comments = youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=100,
                        order='relevance'
                    ).execute()
                    
                    video_stats[-1]['top_comments'] = [
                        {
                            'text': comment['snippet']['topLevelComment']['snippet']['textDisplay'],
                            'likes': comment['snippet']['topLevelComment']['snippet']['likeCount']
                        }
                        for comment in comments.get('items', [])[:5]
                    ]

        # Calculate engagement metrics
        df = pd.DataFrame(video_stats)
        if not df.empty:
            df['engagement_rate'] = ((df['likes'] + df['comments']) / df['views'] * 100).round(2)
            df['avg_views_per_day'] = (df['views'] / 
                ((datetime.now() - pd.to_datetime(df['published_at'])).dt.total_seconds() / 86400)).round(2)

        # Compile comprehensive results
        results = {
            'channel_stats': {
                'total_subscribers': int(channel_response['items'][0]['statistics']['subscriberCount']),
                'total_views': int(channel_response['items'][0]['statistics']['viewCount']),
                'total_videos': int(channel_response['items'][0]['statistics']['videoCount']),
                'channel_description': channel_response['items'][0]['snippet']['description']
            },
            'performance_metrics': {
                'avg_views_per_video': df['views'].mean() if not df.empty else 0,
                'avg_engagement_rate': df['engagement_rate'].mean() if not df.empty else 0,
                'best_performing_video': df.loc[df['views'].idxmax()].to_dict() if not df.empty else None,
                'recent_videos': df.to_dict('records') if not df.empty else []
            }
        }
        
        return results

if __name__ == "__main__":
    tool = ChannelAnalyzer(days_back=30, include_comments=True)
    print(tool.run()) 