export const formatTime = (isoString) => {
    if (!isoString) return 'Date not available';
  
    try {
      const date = new Date(isoString);
      if (isNaN(date.getTime())) throw new Error('Invalid date');
      
      const now = new Date();
      const diffInSeconds = Math.floor((now - date) / 1000);
      const userLocale = navigator.language || 'en-US';
  
      // Relative time formatting for recent dates
      if (diffInSeconds < 60) {
        return 'Just now';
      }
      if (diffInSeconds < 3600) {
        return `${Math.floor(diffInSeconds / 60)} minutes ago`;
      }
      if (diffInSeconds < 86400) {
        return `${Math.floor(diffInSeconds / 3600)} hours ago`;
      }
  
      // Formatting options based on recency
      const options = {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      };
  
      if (date.getFullYear() !== now.getFullYear()) {
        options.year = 'numeric';
      }
      
      if (diffInSeconds < 604800) { // Within 1 week
        options.weekday = 'short';
      } else {
        options.month = 'short';
        options.day = 'numeric';
      }
  
      // Format with relative day indication
      const dayDifference = Math.floor(diffInSeconds / 86400);
      let relativeDay = '';
      
      if (dayDifference === 1) {
        relativeDay = 'Yesterday';
      } else if (dayDifference < 7) {
        relativeDay = 'This week';
      }
  
      const formattedDate = new Intl.DateTimeFormat(userLocale, options).format(date);
      return relativeDay 
        ? `${relativeDay}, ${formattedDate}` 
        : formattedDate;
  
    } catch (error) {
      console.warn('Date formatting error:', error.message);
      return 'Invalid date format';
    }
  };