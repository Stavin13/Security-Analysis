import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App'; // Import your main component
import './App.css';     // Import global styles if any

// Create the root element
const root = ReactDOM.createRoot(document.getElementById('root'));

// Render the root React component into the DOM using JSX
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);