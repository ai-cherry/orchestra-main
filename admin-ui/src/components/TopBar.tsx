import React from "react";
import { AppBar, Toolbar, IconButton, Typography } from "@mui/material";
import Brightness4Icon from "@mui/icons-material/Brightness4";
import Brightness7Icon from "@mui/icons-material/Brightness7";

interface TopBarProps {
  toggleMode: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ toggleMode }) => (
  <AppBar position="static" color="default" elevation={0}>
    <Toolbar>
      <Typography variant="h6" sx={{ flexGrow: 1 }}>
        Cherry Admin UI
      </Typography>
      <IconButton onClick={toggleMode} color="inherit">
        <Brightness4Icon />
      </IconButton>
    </Toolbar>
  </AppBar>
);

export default TopBar;