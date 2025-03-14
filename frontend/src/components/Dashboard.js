import React, { useState } from "react";
import {
  Container,
  Grid,
  Paper,
  Typography,
} from "@mui/material";
import SearchBar from "./SearchBar";
import TweetList from "./TweetList";
import AnalyticsSummary from "./AnalyticsSummary";
import { useSnackbar } from "notistack";
import { fetchTweetAnalysis } from "../utils/api";

const Dashboard = () => {
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { enqueueSnackbar } = useSnackbar();

  const handleSearch = async (keyword) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchTweetAnalysis(keyword);
      console.log('Received tweets:', response.tweets);
      setTweets(response.tweets || []);
      enqueueSnackbar("Analysis completed successfully", { variant: "success" });
    } catch (error) {
      setError(error.message);
      console.error('Search error:', error);
      enqueueSnackbar(error.message || "An error occurred", { variant: "error" });
      setTweets([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <SearchBar onSearch={handleSearch} loading={loading} />
        </Grid>
        
        {error && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2, bgcolor: 'error.light' }}>
              <Typography color="error.dark">
                Error: {error}
              </Typography>
            </Paper>
          </Grid>
        )}
        
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: "100%" }}>
            <TweetList tweets={tweets || []} loading={loading} />
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <AnalyticsSummary tweets={tweets || []} />
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;