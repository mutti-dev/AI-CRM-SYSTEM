export const formatReplyContent = (content) => {
    let formatted = content;
  
    // Remove subject line if present
    if (formatted.startsWith("Subject:")) {
      const match = formatted.match(/\n[ \t]*\n/); // Match two newlines with optional spaces/tabs
      if (match) {
        const index = match.index + match[0].length;
        formatted = formatted.substring(index);
      }
    }
  
    // Convert \n to <br /> tags for HTML rendering
    return formatted.replace(/\n/g, "<br />");
  };
  