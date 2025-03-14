from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.String(100), unique=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    search_keyword = db.Column(db.String(100))
    
    # Sentiment scores
    sentiment_pos = db.Column(db.Float)
    sentiment_neu = db.Column(db.Float)
    sentiment_neg = db.Column(db.Float)
    
    # Fake news score
    fake_news_score = db.Column(db.Float)
    
    # Metadata
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tweet_id': self.tweet_id,
            'text': self.text,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat(),
            'search_keyword': self.search_keyword,
            'sentiment': {
                'pos': self.sentiment_pos,
                'neu': self.sentiment_neu,
                'neg': self.sentiment_neg
            },
            'fake_news': {
                'score': self.fake_news_score
            },
            'analyzed_at': self.analyzed_at.isoformat()
        } 

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    searched_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(100), nullable=True)  # Optional: if you have user authentication
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'searched_at': self.searched_at.isoformat()
        } 