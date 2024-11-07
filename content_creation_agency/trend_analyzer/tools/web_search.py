from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from tavily import TavilyClient
from datetime import datetime, timedelta

load_dotenv()

class WebSearch(BaseTool):
    """
    Advanced web search tool for AI trends using Tavily API with filtering and trend detection
    """
    query: str = Field(..., description="The search query for AI trends")
    days_back: int = Field(
        default=30,
        description="Number of days back to search"
    )
    include_sentiment: bool = Field(
        default=True,
        description="Whether to include sentiment analysis in results"
    )
    
    def run(self):
        """
        Performs an advanced web search with trend detection and filtering
        """
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Search with time filtering
        date_filter = (datetime.now() - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
        
        response = client.search(
            query=self.query,
            search_depth="advanced",
            include_answer=True,
            include_domains=["arxiv.org", "github.com", "paperswithcode.com", "huggingface.co"],
            exclude_domains=["wikipedia.org"],
            max_results=20,
            topic="technology",
            search_params={
                "date_published_after": date_filter,
                "include_sentiment": self.include_sentiment
            }
        )
        
        # Process and structure results
        structured_results = {
            "summary": response.get("answer", ""),
            "top_sources": [],
            "trending_topics": set(),
            "key_findings": []
        }
        
        for result in response.get("results", []):
            # Add to top sources
            structured_results["top_sources"].append({
                "title": result.get("title"),
                "url": result.get("url"),
                "published_date": result.get("published_date"),
                "relevance_score": result.get("relevance_score"),
                "sentiment": result.get("sentiment") if self.include_sentiment else None
            })
            
            # Extract potential trending topics from titles
            if "title" in result:
                topics = [topic.strip() for topic in result["title"].split() 
                         if len(topic) > 3 and topic.lower() not in {"the", "and", "for", "with"}]
                structured_results["trending_topics"].update(topics)
            
            # Add key findings
            if result.get("relevance_score", 0) > 0.7:
                structured_results["key_findings"].append(result.get("snippet"))
        
        # Convert trending_topics set to list
        structured_results["trending_topics"] = list(structured_results["trending_topics"])
        
        return structured_results

if __name__ == "__main__":
    tool = WebSearch(
        query="latest developments in artificial intelligence and machine learning",
        days_back=7,
        include_sentiment=True
    )
    print(tool.run())