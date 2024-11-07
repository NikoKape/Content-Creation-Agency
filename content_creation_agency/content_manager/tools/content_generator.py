from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
import openai
import json

load_dotenv()

class ContentGenerator(BaseTool):
    """
    Generates content ideas using OpenAI's latest GPT-4 Turbo preview model with enhanced
    prompt engineering and structured output.
    """
    trends_data: dict = Field(
        ..., 
        description="Dictionary containing trend analysis data"
    )
    youtube_data: dict = Field(
        ..., 
        description="Dictionary containing YouTube analytics data"
    )
    num_ideas: int = Field(
        default=5,
        description="Number of content ideas to generate"
    )

    def run(self):
        """
        Generates content ideas using OpenAI's API with structured prompting
        """
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        system_prompt = """You are an expert AI content strategist specializing in creating engaging 
        educational content about artificial intelligence and technology. Your task is to generate 
        unique content ideas that:
        1. Align with current trends and audience interests
        2. Fill identified content gaps
        3. Have high potential for engagement
        4. Build upon successful past content
        5. Offer unique perspectives or insights

        Format your response as a JSON object with the following structure:
        {
            "content_ideas": [
                {
                    "title": "Engaging title",
                    "hook": "Attention-grabbing opening hook",
                    "key_points": ["point1", "point2", "point3"],
                    "target_audience": "Description of target audience",
                    "estimated_engagement": "High/Medium/Low with reasoning",
                    "trend_alignment": "How it aligns with current trends",
                    "differentiation": "What makes this unique"
                }
            ]
        }"""

        prompt = f"""Based on the following data:

        Trends Analysis: {json.dumps(self.trends_data, indent=2)}
        YouTube Performance: {json.dumps(self.youtube_data, indent=2)}

        Generate {self.num_ideas} unique content ideas that leverage these insights and fill identified gaps.
        Focus on topics that show high trend potential but aren't oversaturated."""
        
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content

if __name__ == "__main__":
    test_trends = {
        "trending_topics": ["AI Ethics", "Machine Learning"],
        "interest_over_time": {"AI": [80, 85, 90]}
    }
    test_youtube = {
        "best_performing_video": {"title": "AI Basics", "views": 10000},
        "avg_engagement_rate": 8.5
    }
    
    tool = ContentGenerator(
        trends_data=test_trends,
        youtube_data=test_youtube,
        num_ideas=3
    )
    print(tool.run()) 