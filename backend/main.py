import os
# Set protobuf implementation before importing TensorFlow
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import re
import requests
from transformers import pipeline, AutoTokenizer, TFAutoModelForSequenceClassification
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from nltk import download
from dotenv import load_dotenv
import tweepy
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from models import db, Tweet, Search
from datetime import datetime, timedelta
import sys
import time
from functools import lru_cache, wraps
from newsapi import NewsApiClient
import random  # Add this import at the top
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import signal


# Download required NLTK data
download("vader_lexicon")

# Load environment variables
load_dotenv()
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
VT_API_KEY = os.getenv('VT_API_KEY')
HF_TOKEN = os.getenv('hf_token')  # Get Hugging Face token
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # Get News API key

# Initialize News API client
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Initialize all models
try:
    model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
    roberta_pipeline = pipeline("text-classification", model=model_name, tokenizer=model_name)
except Exception as e:
    print(f"Warning: RoBERTa initialization failed: {e}")
    roberta_pipeline = None

# Initialize VADER
sia = SentimentIntensityAnalyzer()

# Authenticate with Twitter API v2
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Check for Twitter token
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
if not TWITTER_BEARER_TOKEN:
    raise ValueError("TWITTER_BEARER_TOKEN not found in environment variables")

# Initialize Twitter client without testing
client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tweets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Initialize tokenizer and model
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
model = TFAutoModelForSequenceClassification.from_pretrained('bert-base-uncased')

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# --- Helper Functions ---
def scan_url(url, api_key):
    """Check a URL for malicious content using VirusTotal API."""
    headers = {"x-apikey": api_key}
    try:
        response = requests.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data={"url": url},
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"VirusTotal API error: {response.status_code}"}
    except requests.RequestException as e:
        return {"error": f"Request error: {str(e)}"}

def detect_fake_news(text, force_false_positive=False):
    """
    Detect fake news using multiple approaches.
    Parameters:
        text (str): The text to analyze
        force_false_positive (bool): If True, forces this to be a false positive
    """
    results = {
        "fake_news_probability": 0,
        "analysis_methods": []
    }

    # If forcing false positive, skip regular analysis
    if force_false_positive:
        return {
            "fake_news_probability": random.uniform(0.7, 0.9),
            "label": "POTENTIALLY_FAKE",
            "confidence": random.uniform(0.6, 0.8),
            "analysis_methods": ["forced_false_positive"],
            "is_false_positive": True
        }

    # Regular analysis (your existing code)
    print(f"\nAnalyzing text for fake news: {text[:100]}...")
    
    # 1. RoBERTa analysis (if available)
    if roberta_pipeline:
        try:
            roberta_result = roberta_pipeline(text)[0]
            results["roberta"] = {
                "score": roberta_result["score"],
                "label": roberta_result["label"]
            }
            results["analysis_methods"].append("roberta")
            results["fake_news_probability"] += roberta_result["score"] * 0.5
            print(f"RoBERTa fake news detection successful: {results['roberta']}")
        except Exception as e:
            print(f"RoBERTa fake news detection failed: {e}")

    # 2. VADER sentiment extremity check
    try:
        vader_scores = sia.polarity_scores(text)
        extremity = abs(vader_scores["compound"])
        results["vader"] = {
            "extremity": extremity,
            "scores": vader_scores
        }
        results["analysis_methods"].append("vader")
        results["fake_news_probability"] += (extremity * 0.3)
        print(f"VADER extremity check successful: {results['vader']}")
    except Exception as e:
        print(f"VADER analysis failed: {e}")

    # 3. TextBlob subjectivity analysis
    try:
        blob = TextBlob(text)
        results["textblob"] = {
            "subjectivity": blob.sentiment.subjectivity,
            "polarity": blob.sentiment.polarity
        }
        results["analysis_methods"].append("textblob")
        results["fake_news_probability"] += (blob.sentiment.subjectivity * 0.2)
        print(f"TextBlob analysis successful: {results['textblob']}")
    except Exception as e:
        print(f"TextBlob analysis failed: {e}")

    # Normalize and add confidence
    if results["analysis_methods"]:
        results["fake_news_probability"] /= len(results["analysis_methods"])
        results["confidence"] = len(results["analysis_methods"]) / 3.0
        results["label"] = "POTENTIALLY_FAKE" if results["fake_news_probability"] > 0.6 else "LIKELY_REAL"
        print(f"Final fake news probability: {results['fake_news_probability']}")
        print(f"Confidence: {results['confidence']}")
        print(f"Label: {results['label']}")
    else:
        print("Warning: No analysis methods succeeded")

    return results

def analyze_sentiment(text):
    """
    Perform sentiment analysis using all three models.
    Returns combined results with fallback mechanisms.
    """
    results = {
        "compound_score": 0,
        "analysis_methods": []
    }

    # Add debug logging
    print(f"\nAnalyzing text: {text[:100]}...")  # Print first 100 chars

    # 1. Try RoBERTa (most sophisticated)
    if roberta_pipeline:
        try:
            roberta_result = roberta_pipeline(text)[0]
            results["roberta"] = {
                "label": roberta_result["label"],
                "score": roberta_result["score"]
            }
            results["analysis_methods"].append("roberta")
            results["compound_score"] += roberta_result["score"] * 0.5  # 50% weight
            print(f"RoBERTa analysis successful: {results['roberta']}")
        except Exception as e:
            print(f"RoBERTa analysis failed: {e}")

    # 2. Use VADER (good for social media)
    try:
        vader_scores = sia.polarity_scores(text)
        results["vader"] = vader_scores
        results["analysis_methods"].append("vader")
        results["compound_score"] += vader_scores["compound"] * 0.3  # 30% weight
        print(f"VADER analysis successful: {vader_scores}")
    except Exception as e:
        print(f"VADER analysis failed: {e}")

    # 3. Use TextBlob (simple but reliable)
    try:
        blob = TextBlob(text)
        textblob_results = {
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity
        }
        results["textblob"] = textblob_results
        results["analysis_methods"].append("textblob")
        results["compound_score"] += blob.sentiment.polarity * 0.2  # 20% weight
        print(f"TextBlob analysis successful: {textblob_results}")
    except Exception as e:
        print(f"TextBlob analysis failed: {e}")

    # Normalize compound score and add confidence
    if results["analysis_methods"]:
        results["compound_score"] /= len(results["analysis_methods"])
        results["confidence"] = len(results["analysis_methods"]) / 3.0
        print(f"Final compound score: {results['compound_score']}")
        print(f"Confidence: {results['confidence']}")
    else:
        print("Warning: No analysis methods succeeded")

    return results

def extract_urls(text):
    """Extract URLs from the given text."""
    return re.findall(r'https?://\S+', text)

def fetch_tweets_v2(keyword, total_count=10):
    """Fetch tweets using the Twitter API v2."""
    tweets = []
    next_token = None  # For pagination

    while len(tweets) < total_count:
        try:
            response = client.search_recent_tweets(
                query=keyword,
                max_results=min(100, total_count - len(tweets)),
                tweet_fields=["created_at", "author_id", "text"],
                next_token=next_token,
            )

            if not response.data:
                break  # No more tweets available

            tweets.extend(response.data)
            next_token = response.meta.get("next_token")  # Get next_token for pagination
            if not next_token:
                break  # Stop if there's no next page
        except tweepy.TweepyException as e:
            print(f"An error occurred while fetching tweets: {e}")
            break

    return tweets[:total_count]  # Return the limited number of tweets

def process_tweets(tweets):
    """Analyze tweets for sentiment and fake news detection."""
    analyzed_tweets = []
    
    # Always select exactly 3 tweets for false positives
    # If we have less than 3 tweets, duplicate some indices
    total_tweets = len(tweets)
    if total_tweets == 0:
        return []
    
    # Generate 3 indices, allowing duplicates if necessary
    false_positive_indices = []
    while len(false_positive_indices) < 3:
        # If we have less than 3 tweets, we'll reuse some indices
        index = random.randint(0, total_tweets - 1)
        false_positive_indices.append(index)
    
    print(f"\n=== Processing {total_tweets} tweets ===")
    print(f"Selected indices for false positives: {false_positive_indices}")
    
    for idx, tweet in enumerate(tweets):
        try:
            # Regular sentiment analysis
            sentiment_analysis = cached_analyze_sentiment(tweet.text)
            if idx in false_positive_indices:
                fake_news_analysis = detect_fake_news(tweet.text, force_false_positive=True)
            else:
                fake_news_analysis = detect_fake_news(tweet.text)
            
            # Count how many times this index appears in false_positive_indices
            false_positive_count = false_positive_indices.count(idx)
            
            # If this tweet index is selected as false positive (maybe multiple times)
            if idx in false_positive_indices:
                print(f"\nMarking tweet {idx} as false positive")
                fake_news_analysis = {
                    "fake_news_probability": random.uniform(0.7, 0.9),
                    "label": "POTENTIALLY_FAKE",
                    "confidence": random.uniform(0.6, 0.8),
                    "analysis_methods": fake_news_analysis.get("analysis_methods", [])
                }
            
            tweet_data = {
                "text": tweet.text,
                "author_id": tweet.author_id,
                "created_at": str(tweet.created_at),
                "sentiment": sentiment_analysis,
                "fake_news": fake_news_analysis,
                "is_false_positive": idx in false_positive_indices,  # Mark as false positive if selected
                "false_positive_count": false_positive_count  # Add count for debugging
            }

            # Analyze URLs in the tweet
            urls = extract_urls(tweet.text)
            tweet_data["urls"] = urls

            # Scan URLs if VT_API_KEY is available
            if VT_API_KEY:
                scanned_urls = []
                for url in urls:
                    scan_result = scan_url(url, VT_API_KEY)
                    scanned_urls.append({"url": url, "scan_result": scan_result})
                tweet_data["scanned_urls"] = scanned_urls

            analyzed_tweets.append(tweet_data)
            
            # Debug print for each tweet
            print(f"\nTweet {idx}:")
            print(f"Text: {tweet.text[:100]}...")  # Print first 100 chars of tweet
            print(f"Is false positive: {idx in false_positive_indices}")
            print(f"Fake news probability: {fake_news_analysis.get('fake_news_probability')}")
            
        except Exception as e:
            print(f"Error processing tweet {idx}: {e}")
            continue

    # Print summary
    print("\n=== Processing Summary ===")
    print(f"Total tweets processed: {len(analyzed_tweets)}")
    false_positives = sum(1 for t in analyzed_tweets if t.get('is_false_positive'))
    print(f"False positives generated: {false_positives}")
    print(f"False positive indices: {false_positive_indices}")
    print("============================\n")
    
    return analyzed_tweets

# Add model initialization with error handling
def initialize_models():
    try:
        global roberta_pipeline, sia
        model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
        roberta_pipeline = pipeline("text-classification", 
                                   model=model_name, 
                                   tokenizer=model_name,
                                   token=HF_TOKEN)
        sia = SentimentIntensityAnalyzer()
        download("vader_lexicon")
        return True
    except Exception as e:
        print(f"Error initializing models: {e}")
        return False

# Initialize at startup
if not initialize_models():
    raise RuntimeError("Failed to initialize models")

# Add these functions before the route definitions

def cached_analyze_sentiment(text):
    """Cached version of sentiment analysis"""
    return analyze_sentiment(text)

def cached_detect_fake_news(text):
    """Cached version of fake news detection"""
    return detect_fake_news(text)

# Add caching decorator
@lru_cache(maxsize=100)
def cached_twitter_search(keyword, num_tweets):
    return client.search_recent_tweets(
        query=keyword,
        max_results=num_tweets,
        tweet_fields=['created_at', 'author_id', 'text']
    )

# Cache for storing recent searches
tweet_cache = {}
CACHE_DURATION = timedelta(minutes=15)
RATE_LIMIT_WINDOW = timedelta(minutes=15)
last_request_time = datetime.now() - RATE_LIMIT_WINDOW

# Rate limiting variables
RATE_LIMIT_WINDOW = timedelta(minutes=15)
REQUESTS_PER_WINDOW = 180  # Twitter's rate limit
request_timestamps = []

def can_make_request():
    """Check if we can make a new request within rate limits"""
    global request_timestamps
    now = datetime.now()
    
    # Remove timestamps older than the window
    request_timestamps = [ts for ts in request_timestamps if now - ts < RATE_LIMIT_WINDOW]
    
    # Check if we're within limits
    if len(request_timestamps) < REQUESTS_PER_WINDOW:
        request_timestamps.append(now)
        return True
    return False

# --- Flask Routes ---
@app.route('/')
def home():
    return "Welcome to the Tweet Analysis API!"

@app.route('/api/endpoint', methods=['GET'])
def api_endpoint():
    return {"message": "Hello from the backend!"}

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "Backend is working!"}), 200

def verify_with_news(text, keyword):
    """Verify tweet content against news sources."""
    try:
        # Search news articles related to the tweet content
        news_response = newsapi.get_everything(
            q=keyword,
            language='en',
            sort_by='relevancy',
            page_size=5  # Limit to top 5 relevant articles
        )
        
        if not news_response['articles']:
            return {
                "verified": False,
                "confidence": 0,
                "sources": []
            }
        
        # Compare tweet content with news articles
        sources = []
        similarity_scores = []
        
        for article in news_response['articles']:
            title = article['title'].lower()
            description = article['description'].lower() if article['description'] else ""
            tweet_text = text.lower()
            
            # Calculate simple similarity score
            words_in_tweet = set(tweet_text.split())
            words_in_article = set((title + " " + description).split())
            
            common_words = words_in_tweet.intersection(words_in_article)
            similarity = len(common_words) / len(words_in_tweet) if words_in_tweet else 0
            
            if similarity > 0.2:  # If there's meaningful similarity
                sources.append({
                    "title": article['title'],
                    "url": article['url'],
                    "source": article['source']['name'],
                    "similarity_score": similarity
                })
                similarity_scores.append(similarity)
        
        # Calculate overall confidence
        confidence = max(similarity_scores) if similarity_scores else 0
        
        return {
            "verified": confidence > 0.3,  # Consider verified if confidence > 30%
            "confidence": confidence,
            "sources": sources
        }
    except Exception as e:
        print(f"Error in news verification: {e}")
        return {
            "verified": False,
            "confidence": 0,
            "sources": [],
            "error": str(e)
        }

@app.route('/analyze', methods=['POST'])
@limiter.limit("10 per minute")  # Adjust these values as needed
def analyze():
    try:
        print("Starting analyze endpoint")
        data = request.get_json()
        print("Received data:", data)
        
        if not data or 'keyword' not in data:
            return jsonify({"error": "No keyword provided"}), 400
        
        keyword = data['keyword']
        print(f"Searching for keyword: {keyword}")
        
        # Save search
        new_search = Search(keyword=keyword)
        db.session.add(new_search)
        db.session.commit()
        
        try:
            response = client.search_recent_tweets(
                query=keyword,
                max_results=10,
                tweet_fields=['created_at', 'author_id', 'text']
            )
            
            if not response.data:
                return jsonify({"tweets": []}), 200
            
            tweets = []
            for tweet in response.data:
                # Create Tweet object
                new_tweet = Tweet(
                    tweet_id=str(tweet.id),
                    text=tweet.text,
                    author_id=tweet.author_id,
                    created_at=tweet.created_at,
                    search_keyword=keyword,
                    analyzed_at=datetime.utcnow()
                )
                db.session.add(new_tweet)
                
                # Analyze tweet content
                sentiment_analysis = analyze_sentiment(tweet.text)
                fake_news_analysis = detect_fake_news(tweet.text)
                news_verification = verify_with_news(tweet.text, keyword)
                
                # Extract and scan URLs
                urls = extract_urls(tweet.text)
                scanned_urls = []
                if VT_API_KEY and urls:
                    for url in urls:
                        scan_result = scan_url(url, VT_API_KEY)
                        scanned_urls.append({"url": url, "scan_result": scan_result})
                
                # Compile tweet data with all analyses
                tweet_data = {
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "created_at": str(tweet.created_at),
                    "keyword": keyword,
                    "sentiment": sentiment_analysis,
                    "fake_news": fake_news_analysis,
                    "news_verification": news_verification,
                    "urls": urls,
                    "scanned_urls": scanned_urls if scanned_urls else None
                }
                tweets.append(tweet_data)
            
            # Commit all tweets to database
            db.session.commit()
            
            return jsonify({
                "tweets": tweets,
                "total": len(tweets)
            }), 200

        except tweepy.TooManyRequests:
            print("Twitter API rate limit exceeded")
            return jsonify({
                "error": "Twitter API rate limit exceeded",
                "retry_after": "15 minutes"
            }), 429
            
        except Exception as e:
            print(f"Twitter API error: {str(e)}")
            return jsonify({"error": "Failed to fetch tweets"}), 500

    except Exception as e:
        print(f"Error in analyze endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add new endpoint to get tweet history
@app.route('/history', methods=['GET'])
def get_history():
    try:
        keyword = request.args.get('keyword')
        days = int(request.args.get('days', 7))
        
        query = Tweet.query
        if keyword:
            query = query.filter_by(search_keyword=keyword)
        
        tweets = query.filter(
            Tweet.analyzed_at >= datetime.utcnow() - timedelta(days=days)
        ).order_by(Tweet.analyzed_at.desc()).all()
        
        return jsonify({
            "tweets": [tweet.to_dict() for tweet in tweets]
        }), 200
        
    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/search-history', methods=['GET'])
def get_search_history():
    try:
        searches = Search.query.order_by(Search.searched_at.desc()).limit(10).all()
        return jsonify({
            "searches": [search.to_dict() for search in searches]
        }), 200
    except Exception as e:
        print(f"Error fetching search history: {e}")
        return jsonify({"error": str(e)}), 500

# Clean up old cache entries periodically
def cleanup_cache():
    current_time = datetime.now()
    expired_keys = [
        key for key, (cache_time, _) in tweet_cache.items()
        if current_time - cache_time > CACHE_DURATION
    ]
    for key in expired_keys:
        del tweet_cache[key]

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/news', methods=['GET'])
def get_news():
    try:
        # Get query parametersx
        keyword = request.args.get('keyword', '')
        days = int(request.args.get('days', '7'))
        
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        # Get news articles
        news_response = newsapi.get_everything(
            q=keyword,
            from_param=from_date.strftime('%Y-%m-%d'),
            to=to_date.strftime('%Y-%m-%d'),
            language='en',
            sort_by='relevancy'
        )
        
        # Process articles and analyze sentiment
        articles = []
        for article in news_response['articles']:
            # Analyze sentiment of title and description
            title_sentiment = analyze_sentiment(article['title'])
            description_sentiment = analyze_sentiment(article['description']) if article['description'] else None
            
            # Check for fake news
            fake_news_score = detect_fake_news(article['title'] + ' ' + (article['description'] or ''))
            
            # Add processed article to list
            articles.append({
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'publishedAt': article['publishedAt'],
                'source': article['source']['name'],
                'sentiment': {
                    'title': title_sentiment,
                    'description': description_sentiment
                },
                'fake_news_probability': fake_news_score['fake_news_probability'] if fake_news_score else None
            })
        
        return jsonify({
            'status': 'success',
            'total_results': len(articles),
            'articles': articles
        }), 200
        
    except Exception as e:
        print(f"Error fetching news: {e}")
        return jsonify({"error": str(e)}), 500

def initialize_app():
    # Initialize models
    if not initialize_models():
        raise RuntimeError("Failed to initialize models")
    return app

# Add this before app.run()
@app.before_first_request
def initialize():
    # Add a small delay to ensure everything is loaded
    time.sleep(2)
    print("Flask app fully initialized and ready to accept requests")

def signal_handler(sig, frame):
    print('Gracefully shutting down...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        print(f"Error starting the application: {e}")
        sys.exit(1)
