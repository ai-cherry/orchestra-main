import React from "react";
import { Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar, Box } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import PeopleIcon from "@mui/icons-material/People";
import StorageIcon from "@mui/icons-material/Storage";
import ExtensionIcon from "@mui/icons-material/Extension";
import BuildIcon from "@mui/icons-material/Build";
import FaceIcon from "@mui/icons-material/Face";
import ListAltIcon from "@mui/icons-material/ListAlt";
import SettingsIcon from "@mui/icons-material/Settings";
import { Link, useLocation } from "react-router-dom";

const drawerWidth = 220;

const navItems = [
  { label: "Dashboard", icon: <DashboardIcon />, path: "/" },
  { label: "Agents", icon: <PeopleIcon />, path: "/agents" },
  { label: "Resources", icon: <StorageIcon />, path: "/resources" },
  { label: "Integrations", icon: <ExtensionIcon />, path: "/integrations" },
  { label: "Workflows", icon: <BuildIcon />, path: "/workflows" },
  { label: "Personas", icon: <FaceIcon />, path: "/personas" },
  { label: "Logs", icon: <ListAltIcon />, path: "/logs" },
  { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
];

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: "border-box",
          background: "linear-gradient(180deg, #1b1b3a 60%, #d72660 100%)",
          color: "#fff",
        },
      }}
    >
      <Toolbar>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            width: "100%",
            justifyContent: "center",
            py: 1,
          }}
        >
          {/* Cherry logo placeholder */}
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              background: "#d72660",
              mr: 1,
              boxShadow: "0 2px 8px rgba(215,38,96,0.3)",
            }}
          />
          <span style={{ fontWeight: 700, fontSize: 20, letterSpacing: 1 }}>
            cherruy-ai
          </span>
        </Box>
      </Toolbar>
      <List>
        {navItems.map((item) => (
          <ListItem
            button
            key={item.label}
            component={Link}
            to={item.path}
            selected={location.pathname === item.path}
            sx={{
              "&.Mui-selected": {
                background: "rgba(255,255,255,0.08)",
                borderLeft: "4px solid #fff",
              },
              "&:hover": {
                background: "rgba(255,255,255,0.12)",
              },
            }}
          >
            <ListItemIcon sx={{ color: "#fff" }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;