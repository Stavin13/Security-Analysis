import React from 'react';
import PieChart from './Piechart';

// Export the analyze function for use in other components
export const analyzeTweets = async (query) => {
  try {
    const response = await fetch('http://localhost:5000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, count: 10 }),
    });

    const data = await response.json();
    console.log('Analysis Results:', {
      totalTweets: data.tweets.length,
      falsePositives: data.analysis_summary.false_positives,
      falsePositiveTweets: data.tweets.filter(t => t.is_false_positive)
    });
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};

const AnalysisResults = ({ results, isLoading, error }) => {
  if (isLoading) {
    return <div className="loading">Analyzing tweets...</div>;
  }

  if (error) {
    return <div className="error">Error: {error.message}</div>;
  }

  if (!results || !results.tweets || !results.tweets.length) {
    return <div>No results found</div>;
  }

  const formatSentimentData = (sentiment) => {
    return [
      (sentiment.pos || 0) * 100,
      (sentiment.neu || 0) * 100,
      (sentiment.neg || 0) * 100
    ];
  };

  return (
    <div className="analysis-results">
      {/* Display Tweets */}
      <div className="tweets-container">
        {results.tweets.map((tweet, index) => (
          <div 
            key={index} 
            className={`tweet-card ${tweet.is_false_positive ? 'false-positive' : ''}`}
            style={{
              border: tweet.is_false_positive ? '2px solid red' : '1px solid gray',
              margin: '10px',
              padding: '10px'
            }}
          >
            <p>{tweet.text}</p>
            <div className="tweet-metrics">
              <PieChart data={formatSentimentData(tweet.sentiment)} />
              <div className="fake-news-score">
                {tweet.fake_news?.error ? (
                  <span className="error-message">
                    Error analyzing: {tweet.fake_news.error}
                  </span>
                ) : (
                  `Fake News Probability: ${(tweet.fake_news?.score || 0).toFixed(2)}`
                )}
              </div>
              {tweet.is_false_positive && (
                <p style={{color: 'red', fontWeight: 'bold'}}>
                  ⚠️ This tweet was marked as a false positive
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AnalysisResults;