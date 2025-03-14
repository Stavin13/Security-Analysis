const express = require('express');
const path = require('path');
const cors = require('cors');
const axios = require('axios');
const { TwitterApi } = require('twitter-api-v2');
const sentiment = require('sentiment'); // For sentiment analysis
const NodeCache = require('node-cache'); // Cache module
const app = express();

// Enable CORS for all origins (adjust for production environment as necessary)
app.use(cors());

// Middleware to parse JSON request bodies
app.use(express.json());

// Serve static files from the React app (ensure the frontend is built first)
app.use(express.static(path.join(__dirname, '../frontend/build')));

// Root endpoint for backend confirmation
app.get('/', (req, res) => {
  res.send('Hello, this is the backend!');
});

// --- Initialize Cache ---
const cache = new NodeCache({ stdTTL: 300, checkperiod: 60 }); // Cache TTL = 5 minutes

// --- Twitter API Integration ---
const twitterClient = new TwitterApi({
  appKey: 'mrP1wtcZ297V3ZDmjuj5yPPwG',            // Replace with your actual API Key
  appSecret: '4Wy3s5bUJS0Kwk7bjqRjE9JhvdJSJfS64W9IW7KMoKNURftVSx', // Replace with your actual API Secret Key
  accessToken: '1358611690309357569-DtONsf89by3k7EyzpNAuSBJme3yFTV', // Replace with your actual Access Token
  accessSecret: '7KiMGWSHtK8aEb6iWDfHSNQPKPgrK1NSrmU4eiqdDwYYb', // Replace with your actual Access Secret
});

// Fetch tweets with rate limit handling and caching
async function fetchTweets(keyword, totalCount = 10, retryCount = 3) {
  // Check cache first
  const cachedTweets = cache.get(keyword);
  if (cachedTweets) {
    console.log(`Cache hit for keyword: "${keyword}"`);
    return cachedTweets;
  }

  try {
    const { data } = await twitterClient.v2.search(keyword, { max_results: totalCount });
    const tweets = data.data;

    // Store tweets in cache
    cache.set(keyword, tweets);
    return tweets;
  } catch (error) {
    if (error.code === 429) {
      const resetTime = error.rateLimit?.reset || Math.floor(Date.now() / 1000) + 60; // Retry after reset
      const retryAfter = resetTime - Math.floor(Date.now() / 1000);
      console.warn(`Rate limit exceeded. Retrying after ${retryAfter} seconds.`);

      if (retryCount > 0) {
        await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
        return fetchTweets(keyword, totalCount, retryCount - 1);
      } else {
        throw new Error('Rate limit exceeded and retries exhausted.');
      }
    } else {
      console.error('Error fetching tweets:', error);
      throw new Error('Failed to fetch tweets');
    }
  }
}

// --- Helper Functions ---
function analyzeSentiment(text) {
  const sentimentAnalyzer = new sentiment();
  return sentimentAnalyzer.analyze(text);
}

async function detectFakeNews(text) {
  try {
    const response = await axios.post(
      'https://api-inference.huggingface.co/models/nlptown/bert-base-multilingual-uncased-sentiment',
      { inputs: text },
      {
        headers: {
          Authorization: 'Bearer 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', // Hugging Face API Key
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error detecting fake news:', error.response?.data || error.message);
    return { label: 'UNKNOWN', score: 0 };
  }
}

// --- API Routes ---
app.post('/analyze', async (req, res) => {
  try {
    const { keyword, num_tweets = 10 } = req.body;

    if (!keyword) {
      return res.status(400).json({ error: 'No keyword provided' });
    }

    // Fetch tweets with rate limiting and caching
    const tweets = await fetchTweets(keyword, num_tweets);

    // Process tweets: Sentiment analysis, fake news detection, URL extraction
    const analyzedTweets = [];
    for (const tweet of tweets) {
      const sentimentResult = analyzeSentiment(tweet.text);
      const fakeNewsResult = await detectFakeNews(tweet.text);
      const urls = tweet.text.match(/https?:\/\/[^\s]+/g) || [];

      analyzedTweets.push({
        text: tweet.text,
        author_id: tweet.author_id,
        created_at: tweet.created_at,
        sentiment: sentimentResult,
        fake_news: fakeNewsResult,
        urls: urls,
      });
    }

    return res.json({ tweets: analyzedTweets });
  } catch (error) {
    console.error('Error analyzing tweets:', error);
    return res.status(500).json({ error: error.message });
  }
});

// Catch-all handler for non-API requests to serve the React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/public', 'index.html'));
});

// Set the backend to listen on a dynamic or default port (5000)
const PORT = 5000; // Port directly integrated
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
