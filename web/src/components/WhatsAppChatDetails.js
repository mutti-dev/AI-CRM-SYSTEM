import React, { useEffect, useState, useCallback } from "react";
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
  console.log("Chat ID:", chatId);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [replyContent, setReplyContent] = useState("");
  console.log("Reply Content", replyContent);

  const fetchChatDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${config.API_URL}/api/whatsapp/control_fetch/`,
        { chatId, limit: 15 } // removed fromMe & includeMedia to fetch all messages
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
    const handleScroll = () => {
      setShowScrollButton(window.pageYOffset > 100);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    fetchChatDetails();
    // Removed polling to stop auto-refresh
    // const intervalId = setInterval(fetchChatDetails, 5000);
    // return () => clearInterval(intervalId);
  }, [fetchChatDetails]);

  const handleReply = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${config.API_URL}/api/whatsapp/send_custom_message/`,
        { chatId, replyContent }
      );
      if (response.data.status === "success") {
        setReplyContent("");
      } else {
        setError(response.data.error || "Unknown error occurred");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [chatId, replyContent]);

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ p: 3, mt: 4 }}>
        {Array.from(new Array(5)).map((_, index) => (
          <Box key={index} sx={{ display: "flex", gap: 2, mb: 3 }}>
            <Skeleton variant="circular" width="40px" height="40px" />
            <Skeleton variant="rounded" width="70%" height="80px" />
          </Box>
        ))}
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert
          severity="error"
          sx={{
            borderRadius: 2,
            boxShadow: 1,
            backgroundColor: "#f8d7da",
            color: "#721c24",
            border: "1px solid #f5c6cb",
          }}
        >
          <Typography variant="body1" fontWeight="bold">
            Failed to load messages:
          </Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Container>
    );
  }

  return (
    <Container
      maxWidth="md"
      sx={{
        p: 3,
        backgroundColor: "#1a1a1a",
        minHeight: "100vh",
        borderRadius: 8,
        mt: 4,
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
      }}
    >
      <Box
        sx={{
          position: "sticky",
          top: 0,
          backgroundColor: "#1a1a1a",
          py: 2,
          mb: 3,
          borderRadius: 6,
          boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
          zIndex: 1,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          px: 2,
        }}
      >
        <Typography
          variant="h5"
          fontWeight="bold"
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1.5,
          }}
        >
          <Person width="28" height="28" fill="white" />
          Chat Session: {customer_name}
        </Typography>
        <Refresh
          style={{
            width: "30px",
            height: "30px",
            fill: loading ? "#ccc" : "#0084ff",
            animation: loading ? `${spinAnimation} 1s linear infinite` : "none",
            cursor: "pointer",
          }}
          onClick={fetchChatDetails}
        />
      </Box>

      <Grid container spacing={2}>
        {messages.map((item, index) => {
          const message = item.message;
          // Updated to use the new message property "fromMe"
          const isFromMe = message.fromMe;

          return (
            <Grid item xs={12} key={index}>
              <Box
                sx={{
                  display: "flex",
                  flexDirection: isFromMe ? "row-reverse" : "row",
                  alignItems: "flex-end",
                  gap: 1.5,
                }}
              >
                {!isFromMe && (
                  <Avatar
                    sx={{
                      width: 40,
                      height: 40,
                      backgroundColor: "#007bff",
                      color: "#fff",
                      fontWeight: "bold",
                    }}
                  >
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
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "flex-end",
                      mt: 0.5,
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{ fontSize: "0.75rem", color: "#555" }}
                    >
                      {formatTime(message.timestamp)}
                    </Typography>
                  </Box>
                </MessageBubble>
              </Box>
            </Grid>
          );
        })}
      </Grid>

      {/* Reply Input Section */}
      <Box mt={4} p={2} bgcolor="#2d2d2d" borderRadius={2}>
        <Box display="flex" gap={1} alignItems="center">
          <Avatar sx={{ width: 40, height: 40 }}>
            {customer_name[0]?.toUpperCase() || "C"}
          </Avatar>
          <TextField
            fullWidth
            multiline
            minRows={1}
            maxRows={5}
            variant="outlined"
            placeholder="Type your reply..."
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            onKeyPress={(e) =>
              e.key === "Enter" && !e.shiftKey && handleReply()
            }
            sx={{
              "& .MuiOutlinedInput-root": {
                backgroundColor: "#1a1a1a",
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
          <Tooltip title="Send reply">
            <IconButton
              color="primary"
              onClick={handleReply}
              disabled={!replyContent.trim()}
            >
              <Send width="28" height="28" fill="white" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Slide in={showScrollButton} direction="up">
        <ScrollTopButton
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          <KeyboardArrowUp />
        </ScrollTopButton>
      </Slide>
    </Container>
  );
};

export default WhatsAppChatDetails;
