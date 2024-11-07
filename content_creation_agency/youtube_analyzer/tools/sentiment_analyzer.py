from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from textblob import TextBlob
import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline
from collections import Counter
import pandas as pd

load_dotenv()

class SentimentAnalyzer(BaseTool):
    """
    Analyzes sentiment and key themes in YouTube comments using advanced NLP techniques
    """
    video_id: str = Field(..., description="YouTube video ID to analyze comments from")
    max_comments: int = Field(
        default=100,
        description="Maximum number of comments to analyze"
    )
    include_replies: bool = Field(
        default=True,
        description="Whether to include reply comments in analysis"
    )

    def run(self):
        """
        Analyzes YouTube comments using sentiment analysis and topic extraction
        """
        youtube = build('youtube', 'v3', 
                       developerKey=os.getenv('YOUTUBE_API_KEY'))
        
        # Initialize sentiment analyzer
        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1  # Use CPU
        )
        
        # Get comments
        comments_data = []
        next_page_token = None
        
        while len(comments_data) < self.max_comments:
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=self.video_id,
                maxResults=min(100, self.max_comments - len(comments_data)),
                pageToken=next_page_token,
                textFormat="plainText"
            )
            
            try:
                response = request.execute()
            except Exception as e:
                return f"Error fetching comments: {str(e)}"
            
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments_data.append({
                    'text': comment['textDisplay'],
                    'likes': comment['likeCount'],
                    'published_at': comment['publishedAt']
                })
                
                # Include replies if requested
                if self.include_replies and item.get('replies'):
                    for reply in item['replies']['comments']:
                        reply_snippet = reply['snippet']
                        comments_data.append({
                            'text': reply_snippet['textDisplay'],
                            'likes': reply_snippet['likeCount'],
                            'published_at': reply_snippet['publishedAt'],
                            'is_reply': True
                        })
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(comments_data)
        
        # Analyze sentiment
        sentiments = []
        for text in df['text']:
            # TextBlob analysis for polarity and subjectivity
            blob = TextBlob(text)
            
            # Transformer-based sentiment analysis
            transformer_sentiment = sentiment_analyzer(text[:512])[0]  # Limit text length
            
            sentiments.append({
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity,
                'label': transformer_sentiment['label'],
                'score': transformer_sentiment['score']
            })
        
        sentiment_df = pd.DataFrame(sentiments)
        
        # Extract key themes and topics
        all_sentences = []
        for text in df['text']:
            all_sentences.extend(sent_tokenize(text))
        
        # Download required NLTK data
        nltk.download('punkt', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        
        # Extract noun phrases as topics
        topics = []
        for sentence in all_sentences:
            tokens = nltk.word_tokenize(sentence)
            tagged = nltk.pos_tag(tokens)
            
            current_topic = []
            for word, tag in tagged:
                if tag.startswith(('NN', 'JJ')):  # Nouns and adjectives
                    current_topic.append(word)
                elif current_topic:
                    topics.append(' '.join(current_topic))
                    current_topic = []
            
            if current_topic:
                topics.append(' '.join(current_topic))
        
        # Compile results
        results = {
            'overall_sentiment': {
                'average_polarity': sentiment_df['polarity'].mean(),
                'average_subjectivity': sentiment_df['subjectivity'].mean(),
                'positive_percentage': (sentiment_df['label'] == 'POSITIVE').mean() * 100,
                'sentiment_distribution': sentiment_df['label'].value_counts().to_dict()
            },
            'engagement_metrics': {
                'total_comments': len(df),
                'total_likes': df['likes'].sum(),
                'avg_likes_per_comment': df['likes'].mean()
            },
            'key_themes': {
                'top_topics': dict(Counter(topics).most_common(10)),
                'topic_sentiment': {}  # Sentiment by topic
            },
            'temporal_analysis': {
                'sentiment_trend': df.assign(
                    date=pd.to_datetime(df['published_at']).dt.date
                ).groupby('date')['likes'].mean().to_dict()
            }
        }
        
        # Add sentiment by topic
        for topic in results['key_themes']['top_topics']:
            topic_comments = df[df['text'].str.contains(topic, case=False)]
            if not topic_comments.empty:
                topic_sentiments = [TextBlob(text).sentiment.polarity 
                                  for text in topic_comments['text']]
                results['key_themes']['topic_sentiment'][topic] = sum(topic_sentiments) / len(topic_sentiments)
        
        return results

if __name__ == "__main__":
    tool = SentimentAnalyzer(
        video_id="example_video_id",
        max_comments=100,
        include_replies=True
    )
    print(tool.run()) 