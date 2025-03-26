import React, { useEffect, useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import '../styles/MuiTable.css';
import config from '../config/config';
import SearchBar from './SearchBar';

const Queries = () => {
  const navigate = useNavigate();
  const [emails, setEmails] = useState([]);
  const [filteredEmails, setFilteredEmails] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUnreadEmails = async () => {
      try {
        const response = await fetch(`${config.API_URL}/api/unread-emails/`);
        if (!response.ok) {
          throw new Error('Failed to fetch unread emails');
        }
        const result = await response.json();
        setEmails(result.emails || []);
        setFilteredEmails(result.emails || []);
      } catch (error) {
        console.error('Error fetching unread emails:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUnreadEmails();
  }, []);

  useEffect(() => {
    const filtered = emails.filter((email) =>
      email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.customer__email.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredEmails(filtered);
  }, [searchTerm, emails]);

  const handleRowClick = (id) => {
    navigate(`/details/${id}`);
  };

  if (loading) {
    return <div className="table-container">Loading...</div>;
  }

  return (
    <div>
      <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
      <TableContainer component={Paper} className="table-container">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Sender</TableCell>
              <TableCell>Subject</TableCell>
              <TableCell>Received At</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredEmails.map((email) => (
              <TableRow
                key={email.id}
                onClick={() => handleRowClick(email.id)}
                className="table-row"
              >
                <TableCell>{email.id}</TableCell>
                <TableCell>{email.customer__email}</TableCell>
                <TableCell>{email.subject}</TableCell>
                <TableCell>{email.received_at || 'N/A'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
};

export default Queries;