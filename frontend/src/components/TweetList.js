import React from "react";
import {
  List,
  ListItem,
  ListItemText,
  Typography,
  CircularProgress,
  Box,
} from "@mui/material";

const TweetList = ({ tweets, loading }) => {
  const getSentimentColor = (score) => {
    if (score > 0.33) return "green";
    if (score < -0.33) return "red";
    return "orange";
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  const getFakeNewsLabel = (analysis) => {
    if (!analysis) return "N/A";
    // Convert small decimal to percentage by multiplying by 1000
    const percentage = (analysis.fake_news_probability * 1000).toFixed(1);
    return `${analysis.label} (${percentage}% probability)`;
  };

  return (
    <List>
      {tweets.map((tweet, index) => {
        return (
          <ListItem key={tweet.id || index} divider>
            <ListItemText
              primary={tweet.text}
              secondary={
                <React.Fragment>
                  <Typography
                    component="span"
                    variant="body2"
                    color={getSentimentColor(tweet.sentiment?.compound_score || 0)}
                  >
                    Sentiment Score: {(tweet.sentiment?.compound_score || 0).toFixed(2)}
                    {tweet.sentiment?.confidence && 
                      ` (Confidence: ${(tweet.sentiment.confidence * 100).toFixed(1)}%)`}
                  </Typography>
                  <br />
                  <Typography
                    component="span"
                    variant="body2"
                    color={tweet.fake_news?.fake_news_probability > 0.06 ? "error" : "success"}
                  >
                    Fake News Analysis: {getFakeNewsLabel(tweet.fake_news)}
                    {tweet.fake_news?.confidence && 
                      ` (Confidence: ${(tweet.fake_news.confidence * 100).toFixed(1)}%)`}
                  </Typography>
                  {tweet.fake_news?.is_false_positive && (
                    <Typography component="span" variant="body2" color="warning">
                      <br />⚠️ This tweet was flagged for review
                    </Typography>
                  )}
                </React.Fragment>
              }
            />
          </ListItem>
        );
      })}
    </List>
  );
};

export default TweetList; 