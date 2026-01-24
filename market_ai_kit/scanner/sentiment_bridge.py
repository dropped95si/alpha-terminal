"""
📰 SENTIMENT BRIDGE - THE COMMON SENSE FILTER
Fetches headlines and converts them to a numerical probability weight.
"""
from textblob import TextBlob # Lightweight NLP
import requests
import os

def get_ticker_sentiment(ticker, api_key):
    # 1. Fetch Headlines (Using a free tier like Finnhub or NewsAPI)
    url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
    response = requests.get(url).json()
    
    # 2. Filter for Ticker-specific news
    relevant_headlines = [n['headline'] for n in response if ticker in n['headline']]
    
    if not relevant_headlines:
        return 0.0 # Return Neutral if no news
    
    # 3. Score Sentiment
    scores = []
    for text in relevant_headlines:
        analysis = TextBlob(text)
        scores.append(analysis.sentiment.polarity) # -1.0 to 1.0
        
    avg_sentiment = sum(scores) / len(scores)
    return round(avg_sentiment, 2)