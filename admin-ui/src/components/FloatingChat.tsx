import React from "react";

const FloatingChat: React.FC = () => (
  <div
    style={{
      position: "fixed",
      bottom: "2rem",
      right: "2rem",
      background: "#fff",
      border: "1px solid #eee",
      borderRadius: "50%",
      width: "56px",
      height: "56px",
      boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 1000,
    }}
  >
    <span role="img" aria-label="Chat">
      💬
    </span>
  </div>
);

export default FloatingChat;
