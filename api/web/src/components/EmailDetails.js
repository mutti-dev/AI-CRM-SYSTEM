import React, { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import {
  Box,
  Typography,
  Avatar,
  TextField,
  IconButton,
  Tooltip,
  useMediaQuery,
  Skeleton,
} from "@mui/material";
import { styled, keyframes } from "@mui/system";
import config from "../config/config";
import Sidebar2 from "./Sidebar2";
import { formatTime } from "../utils/formatTime";
import Send from "../assets/svgs/Send";
import ArrowBack from "../assets/svgs/ArrowBack";
import Error from "../assets/svgs/Error";
import Person from "../assets/svgs/Person";
import Schedule from "../assets/svgs/Schedule";
import { formatReplyContent } from "../utils/formatReplyContent";

const slideIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const MessageBubble = styled(Box)(({ sent }) => ({
  maxWidth: "75%",
  padding: "16px",
  borderRadius: sent ? "18px 18px 0 18px" : "18px 18px 18px 0",
  backgroundColor: sent ? "#0084ff" : "#2d2d2d",
  color: "white",
  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
  animation: `${slideIn} 0.3s ease`,
  wordBreak: "break-word",
  marginBottom: "16px",
}));

const DetailsScreen = () => {
  const { id } = useParams();
  const [email, setEmail] = useState(null);
  const [replies, setReplies] = useState([]);
  const [replyContent, setReplyContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const isMobile = useMediaQuery("(max-width:600px)");

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100); // Ensure it's after DOM render
  };

  useEffect(scrollToBottom, [replies]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [emailRes, repliesRes] = await Promise.all([
          fetch(`${config.API_URL}/api/email-details/${id}/`),
          fetch(`${config.API_URL}/api/email-replies/${id}/`),
        ]);

        if (!emailRes.ok || !repliesRes.ok)
          throw new Error("Failed to fetch data");

        const emailData = await emailRes.json();
        const repliesData = await repliesRes.json();

        setEmail(emailData.email);
        setReplies(repliesData.replies || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleReply = async () => {
    if (!replyContent.trim()) return;
    try {
      const response = await fetch(`${config.API_URL}/api/reply-email/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email_query_id: id, content: replyContent }),
      });

      if (!response.ok) throw new Error("Failed to send reply");

      const result = await response.json();
      setReplies((prev) => [...prev, result.reply]);
      setReplyContent("");
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <Box display="flex" height="100vh">
        <Box flex={1} p={3}>
          <Skeleton width={300} height={40} />
          <Skeleton width={200} />
          {[...Array(3)].map((_, i) => (
            <Box key={i} display="flex" gap={2} mb={3}>
              <Skeleton variant="circular" width={40} height={40} />
              <Skeleton width="70%" height={100} />
            </Box>
          ))}
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        display="flex"
        height="100vh"
        alignItems="center"
        justifyContent="center"
      >
        <Box textAlign="center">
          <Error width="28" height="28" fill="white" />
          <Typography variant="h5" gutterBottom color="white">
            Error Loading Email
          </Typography>
          <Typography color="textSecondary">{error}</Typography>
        </Box>
      </Box>
    );
  }

  if (!email) {
    return (
      <Box
        display="flex"
        height="100vh"
        alignItems="center"
        justifyContent="center"
      >
        <Typography variant="h5" color="white">
          Email Not Found
        </Typography>
      </Box>
    );
  }

  return (
    <Box display="flex" height="100vh" width="100vw" overflow="hidden">
      <Sidebar2 emailQueryId={id} />

      <Box
        flex={1}
        display="flex"
        flexDirection="column"
        height="100vh"
        overflow="hidden"
      >
        {/* Header */}
        <Box
          position="sticky"
          top={0}
          zIndex={2}
          p={isMobile ? 1 : 2}
          bgcolor="#2d2d2d"
          boxShadow={1}
        >
          <Box display="flex" alignItems="center" gap={2} mb={1}>
            <ArrowBack width="28" height="28" fill="white" />
            <Typography variant="h6" fontWeight="bold" color="white" noWrap>
              {email.subject}
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <Person width="20" height="20" fill="white" />
            <Typography variant="body2" color="white">
              From: {email.sender}
            </Typography>
          </Box>
        </Box>

        {/* Messages */}
        <Box
          flex={1}
          overflow="auto"
          p={isMobile ? 1 : 2}
          bgcolor="#1a1a1a"
          display="flex"
          flexDirection="column"
        >
          {/* Original email */}
          <Box display="flex" justifyContent="flex-start">
            <MessageBubble sent={false}>
              <Typography
                variant="body1"
                dangerouslySetInnerHTML={{
                  __html: formatReplyContent(email.body),
                }}
              />
              <Box display="flex" alignItems="center" gap={1} mt={1}>
                <Schedule width="16" height="16" fill="#aaa" />
                <Typography variant="caption" color="#aaa">
                  {formatTime(email.received_at)}
                </Typography>
              </Box>
            </MessageBubble>
          </Box>

          {/* Replies */}
          {replies.map((reply, index) => (
            <Box key={index} display="flex" justifyContent="flex-end">
              <MessageBubble sent>
                <Typography
                  variant="body1"
                  dangerouslySetInnerHTML={{
                    __html: formatReplyContent(reply.content),
                  }}
                />
                <Box
                  display="flex"
                  alignItems="center"
                  gap={1}
                  mt={1}
                  justifyContent="flex-end"
                >
                  <Schedule width="16" height="16" fill="#aaa" />
                  <Typography variant="caption" color="#aaa">
                    {formatTime(reply.sent_at)}
                  </Typography>
                </Box>
              </MessageBubble>
            </Box>
          ))}
          <div ref={messagesEndRef} />
        </Box>

        {/* Reply Input */}
        <Box
          position="sticky"
          bottom={0}
          zIndex={2}
          p={isMobile ? 1 : 2}
          bgcolor="#2d2d2d"
        >
          <Box display="flex" gap={1} alignItems="center">
            <Avatar sx={{ width: 40, height: 40 }}>
              {email.sender?.[0]?.toUpperCase() || "U"}
            </Avatar>
            <TextField
              fullWidth
              multiline
              minRows={1}
              maxRows={4}
              placeholder="Type your reply..."
              variant="outlined"
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
      </Box>
    </Box>
  );
};

export default DetailsScreen;
