import React, { useEffect, useState, useCallback, useRef } from "react";
import axios from "axios";
import { useParams } from "react-router-dom";
import {
  Container,
  Typography,
  CircularProgress,
  Grid,
  Box,
  Alert,
  Avatar,
  Fab,
  Slide,
  Skeleton,
  TextField,
  IconButton,
  Tooltip,
} from "@mui/material";
import { styled, keyframes } from "@mui/system";
import config from "../config/config";

import { formatTime } from "../utils/formatTime";
import KeyboardArrowUp from "../assets/svgs/KeyboardArrowUp";
import Person from "../assets/svgs/Person";
import Refresh from "../assets/svgs/Refresh";
import Send from "../assets/svgs/Send"; // Assuming you have this
import { formatReplyContent } from "../utils/formatReplyContent";
import Sidebar2 from "./Sidebar2";

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const spinAnimation = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

const ScrollTopButton = styled(Fab)({
  position: "fixed",
  bottom: 32,
  right: 32,
  backgroundColor: "#007bff",
  color: "#ffffff",
  "&:hover": {
    backgroundColor: "#0056b3",
    transform: "scale(1.1)",
  },
});

const MessageBubble = styled(Box)(({ isfromme }) => ({
  maxWidth: "75%",
  padding: "12px 16px",
  borderRadius: isfromme ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
  backgroundColor: isfromme ? "#dcf8c6" : "#ffffff",
  color: "#000000",
  boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
  position: "relative",
  animation: `${fadeIn} 0.3s ease`,
  wordBreak: "break-word",
}));

const WhatsAppChatDetails = () => {
  const { chatId, customer_name } = useParams();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [replyContent, setReplyContent] = useState("");
  const messagesEndRef = useRef(null);

  const fetchChatDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${config.API_URL}/api/whatsapp/control_fetch/`,
        { chatId, limit: 50 }
      );
      if (response.data.status === "success") {
        const data = response.data.data.data.data;
        setMessages(Array.isArray(data) ? data : []);
      } else {
        setError(response.data.error || "Unknown error occurred");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [chatId]);

  useEffect(() => {
    fetchChatDetails();
  }, [fetchChatDetails]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleReply = useCallback(async () => {
    if (!replyContent.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post(
        `${config.API_URL}/api/whatsapp/send_custom_message/`,
        { chatId, replyContent }
      );
      if (response.data.status === "success") {
        setReplyContent("");
        fetchChatDetails(); // Refresh chat
      } else {
        setError(response.data.error || "Failed to send message");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [chatId, replyContent, fetchChatDetails]);

  return (
    <Container
      maxWidth="md"
      sx={{
        position: "relative",
        pt: 10,
        pb: 12,
        backgroundColor: "#1a1a1a",
        minHeight: "100vh",
        borderRadius: 4,
        mt: 4,
        overflow: "hidden",
      }}
    >
      {/* Chat Header */}
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 2,
          backgroundColor: "#1a1a1a",
          px: 3,
          py: 2,
          borderBottom: "1px solid #333",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Typography
          variant="h6"
          color="white"
          fontWeight="bold"
          sx={{ display: "flex", alignItems: "center", gap: 1 }}
        >
          <Person width="28" height="28" fill="white" />
          Chat: {customer_name}
        </Typography>
        <IconButton onClick={fetchChatDetails} disabled={loading}>
          <Refresh
            style={{
              width: 24,
              height: 24,
              fill: loading ? "#999" : "#00b0ff",
              animation: loading ? `${spinAnimation} 1s linear infinite` : "none",
            }}
          />
        </IconButton>
      </Box>

      {/* Message List */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column-reverse", // Inverted
          gap: 2,
          px: 2,
          mt: 2,
        }}
      >
        {[...messages].reverse().map((item, index) => {
          const message = item.message;
          const isFromMe = message.fromMe;

          return (
            <Box
              key={index}
              sx={{
                display: "flex",
                flexDirection: isFromMe ? "row-reverse" : "row",
                alignItems: "flex-end",
                gap: 1.5,
              }}
            >
              {!isFromMe && (
                <Avatar sx={{ backgroundColor: "#007bff", color: "#fff" }}>
                  {message.from[0]}
                </Avatar>
              )}
              <MessageBubble isfromme={isFromMe}>
                <Typography
                  variant="body1"
                  component="div"
                  dangerouslySetInnerHTML={{
                    __html: formatReplyContent(message.body),
                  }}
                />
                <Typography
                  variant="caption"
                  sx={{ display: "block", textAlign: "right", color: "#999", mt: 0.5 }}
                >
                  {formatTime(message.timestamp)}
                </Typography>
              </MessageBubble>
            </Box>
          );
        })}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Box - Fixed at Bottom */}
      <Box
        sx={{
          position: "fixed",
          bottom: 0,
          left: 0,
          right: 0,
          p: 2,
          backgroundColor: "#1a1a1a",
          borderTop: "1px solid #333",
          zIndex: 3,
        }}
      >
        <Box display="flex" gap={1} alignItems="center">
          <Avatar sx={{ width: 40, height: 40 }}>
            {customer_name[0]?.toUpperCase() || "C"}
          </Avatar>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Type a message..."
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleReply();
              }
            }}
            sx={{
              "& .MuiOutlinedInput-root": {
                backgroundColor: "#2c2c2c",
                color: "white",
                "& fieldset": {
                  borderColor: "#444",
                },
                "&:hover fieldset": {
                  borderColor: "#666",
                },
              },
            }}
          />
          <Tooltip title="Send">
            <IconButton
              onClick={handleReply}
              disabled={!replyContent.trim()}
              color="primary"
            >
              <Send width="28" height="28" fill="white" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
    </Container>
  );
};


export default WhatsAppChatDetails;
