import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

// Create axios instance with default config
const api = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchTweetAnalysis = async (keyword) => {
  try {
    const response = await api.post('/analyze', {
      keyword: keyword,
      num_tweets: 10
    });

    if (!response.data) {
      throw new Error('No data received from server');
    }

    return response.data;
  } catch (error) {
    console.error('Error fetching tweet analysis:', error);
    throw error;
  }
};

export const fetchSearchHistory = async () => {
  try {
    const response = await api.get('/search-history');
    return response.data;
  } catch (error) {
    console.error('Error fetching search history:', error);
    throw error;
  }
};

const api_methods = { fetchTweetAnalysis, fetchSearchHistory };
export default api_methods;
