import axios from 'axios';

const API_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export const fetchTweetAnalysis = async (keyword) => {
  try {
    console.log('Sending request to:', `${API_URL}/analyze`);
    const response = await api.post('/analyze', { 
      keyword,
      num_tweets: 10 // Add number of tweets to fetch
    });
    
    // Add response data logging
    console.log('Response data structure:', {
      sentiment: response.data.tweets[0]?.sentiment,
      fakeNews: response.data.tweets[0]?.fake_news,
      methods: response.data.tweets[0]?.analysis_methods
    });
    
    return response.data;
  } catch (error) {
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    });
    throw error;
  }
};
