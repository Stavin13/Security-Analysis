import React from 'react';
import { Paper, Typography, Box } from '@mui/material';

const AnalyticsSummary = ({ tweets }) => {
  const calculateAnalytics = () => {
    if (!tweets || tweets.length === 0) {
      return {
        positive: 0,
        negative: 0,
        neutral: 0,
        fakeNews: 0
      };
    }

    let totals = {
      positive: 0,
      negative: 0,
      neutral: 0,
      fakeNews: 0
    };

    tweets.forEach(tweet => {
      // Calculate sentiment distributions
      const score = tweet.sentiment?.compound_score || 0;
      if (score > 0.33) totals.positive++;
      else if (score < -0.33) totals.negative++;
      else totals.neutral++;

      // Add fake news score
      totals.fakeNews += tweet.fake_news?.fake_news_probability || 0;
    });

    const count = tweets.length;
    return {
      positive: ((totals.positive / count) * 100).toFixed(1),
      negative: ((totals.negative / count) * 100).toFixed(1),
      neutral: ((totals.neutral / count) * 100).toFixed(1),
      fakeNews: ((totals.fakeNews / count) * 100).toFixed(1) // Multiply by 1000 for percentage
    };
  };

  const analytics = calculateAnalytics();

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Analysis Summary
      </Typography>
      <Box sx={{ mt: 2 }}>
        <Typography variant="body1">
          Positive Sentiment: {analytics.positive}%
        </Typography>
        <Typography variant="body1">
          Negative Sentiment: {analytics.negative}%
        </Typography>
        <Typography variant="body1">
          Neutral Sentiment: {analytics.neutral}%
        </Typography>
        <Typography variant="body1">
          Fake News Score: {analytics.fakeNews}%
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Based on {tweets.length} tweets
        </Typography>
      </Box>
    </Paper>
  );
};

export default AnalyticsSummary;