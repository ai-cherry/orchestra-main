import React from "react"; export default function MessageBubble({ message, className = "" }) { return <div className={className}>Message from {message.persona}: {message.content}</div>; }
