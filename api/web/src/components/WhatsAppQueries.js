import React, { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  MenuItem,
  Button,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import "../styles/WhatsAppMessages.css";
import config from "../config/config";
import { formatTime } from "../utils/formatTime";
import axios from "axios";
import FetchEmailsButton from "./FetchEmailsButton";
import Refresh from "../assets/svgs/Refresh";



const WhatsAppMessages = () => {
  const [messages, setMessages] = useState([]);
  const [filteredMessages, setFilteredMessages] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedPhone, setSelectedPhone] = useState("");
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const messagesPerPage = 10;
  const navigate = useNavigate();

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${config.API_URL}/api/whatsapp/get_all_whatsapp_messages/`);
      const result = response.data;
      if (result.status === "success") {
        setMessages(result.messages || []);
        setFilteredMessages(result.messages || []);
      } else {
        throw new Error("Failed to fetch WhatsApp messages");
      }
    } catch (error) {
      console.error("Error fetching WhatsApp messages:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, []);

  useEffect(() => {
    let filtered = messages;
    if (searchTerm) {
      filtered = filtered.filter(
        (msg) =>
          msg.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
          msg.phone.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    if (selectedPhone) {
      filtered = filtered.filter((msg) => msg.phone === selectedPhone);
    }
    setFilteredMessages(filtered);
    setCurrentPage(1);
  }, [searchTerm, selectedPhone, messages]);

  const indexOfLast = currentPage * messagesPerPage;
  const indexOfFirst = indexOfLast - messagesPerPage;
  const currentMessages = filteredMessages.slice(indexOfFirst, indexOfLast);

  const uniquePhones = [...new Set(messages.map((msg) => msg.phone))];

  const handleNextPage = () => setCurrentPage((prev) => prev + 1);
  const handlePreviousPage = () =>
    setCurrentPage((prev) => Math.max(prev - 1, 1));

  const handleRowClick = (chatId,customer_name) => {
    navigate(`/whatsapp-chat/${chatId}/${customer_name}`);
  };

  if (loading) {
    return <div className="table-container">Loading...</div>;
  }

  return (
    <div className="whatsapp-messages-container">
      <div className="filters-container">
        <TextField
          label="Search"
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ flex: 2 }}
          fullWidth
        />
        <TextField
          label="Filter by Phone"
          variant="outlined"
          size="small"
          select
          value={selectedPhone}
          onChange={(e) => setSelectedPhone(e.target.value)}
          sx={{ flex: 2 }}
          fullWidth
        >
          <MenuItem value="">All Phones</MenuItem>
          {uniquePhones.map((phone) => (
            <MenuItem key={phone} value={phone}>
              {phone}
            </MenuItem>
          ))}
        </TextField>
      </div>
      <TableContainer component={Paper} className="table-container">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Provider Name</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Received At</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentMessages.map((msg, index) => (
              <TableRow 
                key={`${msg.phone}-${msg.received_at}-${index}`}
                className="table-row"
                onClick={() => handleRowClick(msg.whatsapp_message_id, msg.customer_name)}
                style={{ cursor: "pointer" }}
              >
                <TableCell>{msg.customer_name}</TableCell>
                <TableCell>{msg.phone}</TableCell>
                <TableCell>{formatTime(msg.received_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <div className="pagination-controls">
        <Button
          variant="contained"
          color="primary"
          onClick={handlePreviousPage}
          disabled={currentPage === 1}
        >
          Previous
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={handleNextPage}
          disabled={indexOfLast >= filteredMessages.length}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default WhatsAppMessages;
