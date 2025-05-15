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
import "../styles/Queries.css";
import "../styles/FetchEmailsButton.css";
import config from "../config/config";

import TicketTabs from "./TicketTabs";
import { formatTime } from "../utils/formatTime";
import Sidebar from "./Sidebar";

const Queries = () => {
  const navigate = useNavigate();
  const [emails, setEmails] = useState([]);
  const [filteredEmails, setFilteredEmails] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCustomer, setSelectedCustomer] = useState("");
  const [selectedTimeRange, setSelectedTimeRange] = useState("");
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const emailsPerPage = 10;

  const fetchUnreadEmails = async () => {
    try {
      const response = await fetch(`${config.API_URL}/api/emails/unread-emails/`);
      if (!response.ok) {
        throw new Error("Failed to fetch unread emails");
      }
      const result = await response.json();
      setEmails(result.emails || []);
      setFilteredEmails(result.emails || []);
    } catch (error) {
      console.error("Error fetching unread emails:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnreadEmails();
  }, []);

  useEffect(() => {
    let filtered = emails;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(
        (email) =>
          email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
          email.customer__email.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by customer
    if (selectedCustomer) {
      filtered = filtered.filter(
        (email) => email.customer__name === selectedCustomer
      );
    }

    // Filter by time range
    if (selectedTimeRange) {
      const now = new Date();
      filtered = filtered.filter((email) => {
        const receivedAt = new Date(email.received_at);
        if (selectedTimeRange === "last1Hours") {
          return now - receivedAt <= 1 * 60 * 60 * 1000; // Last 1 hour
        } else if (selectedTimeRange === "last24Hours") {
          return now - receivedAt <= 24 * 60 * 60 * 1000; // Last 24 hours
        } else if (selectedTimeRange === "last7Days") {
          return now - receivedAt <= 7 * 24 * 60 * 60 * 1000; // Last 7 days
        } else if (selectedTimeRange === "last30Days") {
          return now - receivedAt <= 30 * 24 * 60 * 60 * 1000; // Last 30 days
        }
        return true;
      });
    }

    setFilteredEmails(filtered);
    setCurrentPage(1); // Reset to the first page when filters change
  }, [searchTerm, selectedCustomer, selectedTimeRange, emails]);

  const handleRowClick = (id) => {
    navigate(`/details/${id}`);
  };

 
  const uniqueCustomers = [
    ...new Set(emails.map((email) => email.customer__name)),
  ];

  // Pagination logic
  const indexOfLastEmail = currentPage * emailsPerPage;
  const indexOfFirstEmail = indexOfLastEmail - emailsPerPage;
  const currentEmails = filteredEmails.slice(
    indexOfFirstEmail,
    indexOfLastEmail
  );

  const handleNextPage = () => {
    setCurrentPage((prevPage) => prevPage + 1);
  };

  const handlePreviousPage = () => {
    setCurrentPage((prevPage) => Math.max(prevPage - 1, 1));
  };

  if (loading) {
    return <div className="table-container">Loading...</div>;
  }

  return (
    <div>
      <div className="queries-header">
        <TicketTabs />

      </div>

      <div className="filters-container">
        <TextField
          label="Search"
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ flex: 2 }}
          InputProps={{
            style: {
              color: "#fff",
              borderColor: "rgba(255, 255, 255, 0.3)",
            },
          }}
          InputLabelProps={{
            style: { color: "rgba(255, 255, 255, 0.7)" },
          }}
          fullWidth
        />
        <TextField
          label="Filter by Customer"
          variant="outlined"
          size="small"
          select
          value={selectedCustomer}
          onChange={(e) => setSelectedCustomer(e.target.value)}
          sx={{ flex: 2 }}
          InputProps={{
            style: {
              color: "#fff",
              borderColor: "rgba(255, 255, 255, 0.3)",
            },
          }}
          InputLabelProps={{
            style: { color: "rgba(255, 255, 255, 0.7)" },
          }}
          fullWidth
        >
          <MenuItem value="">All Customers</MenuItem>
          {uniqueCustomers.map((customer) => (
            <MenuItem key={customer} value={customer}>
              {customer}
            </MenuItem>
          ))}
        </TextField>

        <TextField
          label="Filter by Time"
          variant="outlined"
          size="small"
          select
          value={selectedTimeRange}
          onChange={(e) => setSelectedTimeRange(e.target.value)}
          sx={{ flex: 2 }}
          InputProps={{
            style: {
              color: "#fff",
              borderColor: "rgba(255, 255, 255, 0.3)",
            },
          }}
          InputLabelProps={{
            style: { color: "rgba(255, 255, 255, 0.7)" },
          }}
          fullWidth
        >
          <MenuItem value="">All Time</MenuItem>
          <MenuItem value="last1Hours">Last 1 hr</MenuItem>
          <MenuItem value="last24Hours">Last 24 Hours</MenuItem>
          <MenuItem value="last7Days">Last 7 Days</MenuItem>
          <MenuItem value="last30Days">Last 30 Days</MenuItem>
        </TextField>
      </div>
      <TableContainer component={Paper} className="table-container">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Ticket Id</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Subject</TableCell>
              <TableCell>Received At</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[...currentEmails]
              .sort((a, b) => b.id - a.id) // Descending order by ID
              .map((email) => (
                <TableRow
                  key={email.id}
                  onClick={() => handleRowClick(email.id)}
                  className="table-row"
                >
                  <TableCell>{email.id}</TableCell>
                  <TableCell>{email.customer__name}</TableCell>
                  <TableCell>{email.subject}</TableCell>
                  <TableCell>
                    {formatTime(email.received_at) || "N/A"}
                  </TableCell>
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
          disabled={indexOfLastEmail >= filteredEmails.length}
        >
          Next
        </Button>
      </div>
    </div>
  );
};

export default Queries;
