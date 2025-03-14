import os
from dotenv import load_dotenv
import tweepy
import time

def test_twitter_connection():
    load_dotenv()
    
    # Get token
    token = os.getenv('TWITTER_BEARER_TOKEN')
    if not token:
        print("Error: TWITTER_BEARER_TOKEN not found in .env file")
        return False
    
    try:
        # Setup API v2 client
        client = tweepy.Client(bearer_token=token)
        
        # Test connection with API v2
        # Note: min value for max_results is 10
        response = client.search_recent_tweets(
            query="test",
            max_results=10,  # Changed from 1 to 10 (minimum allowed)
            tweet_fields=['created_at', 'author_id']
        )
        
        if response.data:
            print(f"Success! Found {len(response.data)} tweets")
            # Print first tweet as example
            print(f"Example tweet: {response.data[0].text[:100]}...")
            return True
        else:
            print("No tweets found")
            return False
            
    except tweepy.TooManyRequests:
        print("Rate limit exceeded. Please wait 15 minutes and try again.")
        return False
    except tweepy.HTTPException as e:
        print(f"Twitter API HTTP error: {e}")
        return False
    except Exception as e:
        print(f"Error connecting to Twitter API: {e}")
        return False

if __name__ == "__main__":
    test_twitter_connection()