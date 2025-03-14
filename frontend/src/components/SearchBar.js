import React, { useState } from "react";
import {
  Paper,
  InputBase,
  IconButton,
  CircularProgress,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";

const SearchBar = ({ onSearch, loading }) => {
  const [keyword, setKeyword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (keyword.trim()) {
      onSearch(keyword.trim());
    }
  };

  return (
    <Paper
      component="form"
      onSubmit={handleSubmit}
      sx={{
        p: "2px 4px",
        display: "flex",
        alignItems: "center",
        width: "100%",
        maxWidth: 600,
        mx: "auto",
      }}
    >
      <InputBase
        sx={{ ml: 1, flex: 1 }}
        placeholder="Enter keyword to analyze tweets..."
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        disabled={loading}
      />
      <IconButton type="submit" disabled={loading}>
        {loading ? <CircularProgress size={24} /> : <SearchIcon />}
      </IconButton>
    </Paper>
  );
};

export default SearchBar; 