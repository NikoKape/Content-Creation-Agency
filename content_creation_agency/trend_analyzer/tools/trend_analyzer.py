from agency_swarm.tools import BaseTool
from pydantic import Field
from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

class TrendAnalyzer(BaseTool):
    """
    Advanced trend analysis tool using Google Trends with statistical analysis
    and predictive insights
    """
    keywords: list = Field(..., description="List of keywords to analyze")
    timeframe: str = Field(
        default='today 3-m',
        description="Timeframe for analysis (today 3-m, today 12-m, etc.)"
    )
    geo: str = Field(
        default='',
        description="Geographic location to analyze (empty for worldwide)"
    )
    
    def run(self):
        """
        Analyzes trends using pytrends with advanced analytics
        """
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Initialize results dictionary
        results = {
            "trend_data": {},
            "related_topics": {},
            "related_queries": {},
            "regional_interest": {},
            "trend_analysis": {},
            "predictions": {}
        }
        
        # Analyze keywords in batches of 5 (Google Trends limit)
        for i in range(0, len(self.keywords), 5):
            batch_keywords = self.keywords[i:i+5]
            
            # Build payload
            pytrends.build_payload(
                batch_keywords,
                cat=0,
                timeframe=self.timeframe,
                geo=self.geo
            )
            
            # Get interest over time
            interest_df = pytrends.interest_over_time()
            
            if not interest_df.empty:
                # Store raw trend data
                for keyword in batch_keywords:
                    if keyword in interest_df.columns:
                        results["trend_data"][keyword] = interest_df[keyword].tolist()
                        
                        # Perform statistical analysis
                        trend_values = interest_df[keyword].values
                        results["trend_analysis"][keyword] = {
                            "mean": float(np.mean(trend_values)),
                            "median": float(np.median(trend_values)),
                            "std": float(np.std(trend_values)),
                            "min": float(np.min(trend_values)),
                            "max": float(np.max(trend_values)),
                            "trend_direction": self._calculate_trend_direction(trend_values),
                            "volatility": float(np.std(trend_values) / np.mean(trend_values)),
                            "momentum": self._calculate_momentum(trend_values)
                        }
                        
                        # Simple prediction for next 30 days
                        results["predictions"][keyword] = self._predict_trend(trend_values)
            
            # Get related topics and queries
            related_topics = pytrends.related_topics()
            related_queries = pytrends.related_queries()
            
            for keyword in batch_keywords:
                if keyword in related_topics:
                    results["related_topics"][keyword] = {
                        "rising": related_topics[keyword]['rising'].to_dict() if related_topics[keyword]['rising'] is not None else {},
                        "top": related_topics[keyword]['top'].to_dict() if related_topics[keyword]['top'] is not None else {}
                    }
                
                if keyword in related_queries:
                    results["related_queries"][keyword] = {
                        "rising": related_queries[keyword]['rising'].to_dict() if related_queries[keyword]['rising'] is not None else {},
                        "top": related_queries[keyword]['top'].to_dict() if related_queries[keyword]['top'] is not None else {}
                    }
            
            # Get regional interest if geo is specified
            if self.geo:
                regional_interest = pytrends.interest_by_region(resolution='COUNTRY')
                results["regional_interest"].update(regional_interest.to_dict())
        
        return results
    
    def _calculate_trend_direction(self, values):
        """Calculate the overall trend direction using linear regression"""
        x = np.arange(len(values))
        slope, _, r_value, _, _ = stats.linregress(x, values)
        
        if abs(r_value) < 0.3:
            return "stable"
        return "increasing" if slope > 0 else "decreasing"
    
    def _calculate_momentum(self, values):
        """Calculate trend momentum using rate of change"""
        if len(values) < 2:
            return 0
        return float(((values[-1] - values[0]) / values[0]) * 100)
    
    def _predict_trend(self, values):
        """Simple linear prediction for next 30 days"""
        x = np.arange(len(values))
        slope, intercept, _, _, _ = stats.linregress(x, values)
        
        future_x = np.arange(len(values), len(values) + 30)
        predictions = slope * future_x + intercept
        
        return predictions.tolist()

if __name__ == "__main__":
    tool = TrendAnalyzer(
        keywords=["artificial intelligence", "machine learning", "deep learning"],
        timeframe='today 3-m',
        geo='US'
    )
    print(tool.run()) 