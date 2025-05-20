import React from 'react';
import { Box, Typography, Button, Stack } from '@mui/material';
import Whatsapp from '../assets/svgs/Whatsapp';
import Ticket from '../assets/svgs/Ticket';
import Email from '../assets/svgs/Email';
import Teams from '../assets/svgs/Teams';
import Schedule from '../assets/svgs/Schedule';



const ActionPanel = () => {
  return (
    <Box
      sx={{
        position: 'relative',
        height: '100vh',
        minWidth: 280,
        maxWidth: 280,
        bgcolor: '#1e1e1e',
        p: 2,
        borderLeft: '1px solid #333',
        color: '#fff',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {/* Context Section */}
      <Box
        sx={{
          bgcolor: '#2a2a2a',
          p: 2,
          borderRadius: 2,
        }}
      >
        <Typography
          variant="subtitle2"
          color="#aaa"
          fontWeight="bold"
          gutterBottom
        >


          Context
        </Typography>
        <Typography variant="body2">
          Customer asking about recent order status
        </Typography>
      </Box>

      {/* Actions Section */}
      <Box>
        <Typography
          variant="subtitle2"
          color="#aaa"
          fontWeight="bold"
          gutterBottom
        >
          Actions
        </Typography>
        <Stack spacing={1}>
          <Button
            fullWidth
            sx={actionButtonStyles}
            startIcon={<Whatsapp width={20} height={20} />}
          >
            Send WhatsApp Message
          </Button>

          <Button
            fullWidth
            sx={actionButtonStyles}
            startIcon={<Teams width={20} height={20} />}
          >
            Schedule Teams Meeting
          </Button>

          <Button
            fullWidth
            sx={actionButtonStyles}
            startIcon={<Email width={20} height={20} />}
          >
            Reply via Email
          </Button>

          <Button
            fullWidth
            sx={actionButtonStyles}
            startIcon={<Ticket width={20} height={20} fill= "white"/>}
          >
            Create Follow-Up Ticket
          </Button>
        </Stack>
      </Box>
    </Box>
  );
};

const actionButtonStyles = {
  justifyContent: 'flex-start',
  bgcolor: '#2a2a2a',
  color: '#fff',
  textTransform: 'none',
  borderRadius: 2,
  px: 2,
  py: 1.5,
  '&:hover': {
    bgcolor: '#333',
  },
};

export default ActionPanel;
