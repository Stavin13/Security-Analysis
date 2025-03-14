import React from "react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { theme } from "./theme.js";
import Dashboard from "./components/Dashboard.js";
import Navbar from "./components/Navbar.js";
import { SnackbarProvider } from "notistack";

const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SnackbarProvider maxSnack={3}>
        <div className="app">
          <Navbar />
          <Dashboard />
        </div>
      </SnackbarProvider>
    </ThemeProvider>
  );
};

export default App;
