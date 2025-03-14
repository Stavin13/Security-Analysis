from main import app, db
from models import Tweet, Search
from datetime import datetime

def check_database():
    with app.app_context():
        try:
            print("\n=== All Searches ===")
            searches = Search.query.order_by(Search.searched_at.desc()).all()
            if searches:
                for search in searches:
                    print(f"Keyword: {search.keyword}")
                    print(f"Searched at: {search.searched_at}")
                    print("---")
            else:
                print("No searches found")

            print("\n=== All Tweets ===")
            tweets = Tweet.query.order_by(Tweet.created_at.desc()).all()
            if tweets:
                for tweet in tweets:
                    print("\nTweet Details:")
                    print(f"ID: {tweet.tweet_id}")
                    print(f"Text: {tweet.text}")
                    print(f"Author: {tweet.author_id}")
                    print(f"Created: {tweet.created_at}")
                    print(f"Keyword: {tweet.search_keyword}")
                    print(f"Analyzed: {tweet.analyzed_at}")
                    print("---")
            else:
                print("No tweets found")

            print("\n=== Database Stats ===")
            tweet_count = Tweet.query.count()
            search_count = Search.query.count()
            print(f"Total Tweets: {tweet_count}")
            print(f"Total Searches: {search_count}")
            print(f"Last checked: {datetime.now()}")

        except Exception as e:
            print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_database() 