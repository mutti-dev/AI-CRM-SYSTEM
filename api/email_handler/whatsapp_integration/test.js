const apiToken = "KTxb7FPE7hr49xPM6WGXnHBSDCMUvQaxWNdchtNM3eb5ef46";
const instanceId = "58199"; // Replace with your actual instance ID
 
app.post("/whatsapp/send-message", async (req, res) => {
  const { chatId, message, mentions, replyToMessageId, previewLink } = req.body;
 
  const options = {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiToken}`,
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      chatId,
      message,
      mentions,
      replyToMessageId,
      previewLink,
    }),
  };
 
  try {
    const response = await fetch(
      `https://waapi.app/api/v1/instances/${instanceId}/client/action/send-message`,
      options
    );
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error("Error sending WhatsApp message:", error);
    res.status(500).json({ error: "Failed to send WhatsApp message" });
  }
});
 
app.post("/whatsapp/send-location", async (req, res) => {
  const { chatId, latitude, longitude, options } = req.body;
 
  const requestBody = {
    chatId,
    latitude,
    longitude,
    options,
  };
 
  const requestOptions = {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiToken}`,
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  };
 
  try {
    const response = await fetch(
      `https://waapi.app/api/v1/instances/${instanceId}/client/action/send-location`,
      requestOptions
    );
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error("Error sending WhatsApp location:", error);
    res.status(500).json({ error: "Failed to send WhatsApp location" });
  }
});
 
app.post("/whatsapp/fetch-messages", async (req, res) => {
  const { chatId, limit, fromMe, includeMedia } = req.body;
 
  const options = {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiToken}`,
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      chatId,
      limit: limit || 100,
      fromMe: fromMe || null,
      includeMedia: includeMedia || false,
    }),
  };
 
  try {
    const response = await fetch(
      `https://waapi.app/api/v1/instances/${instanceId}/client/action/fetch-messages`,
      options
    );
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error("Error fetching messages:", error);
    res.status(500).json({ error: "Failed to fetch messages" });
  }
});
 
app.post("/whatsapp/create-poll", async (req, res) => {
  const { chatId, caption, options, multipleAnswers } = req.body;
 
  // Validate request body
  if (!chatId || !caption || !Array.isArray(options) || options.length < 2 || options.length > 12) {
    return res.status(400).json({
      status: "error",
      message: "Invalid request. Ensure chatId, caption, and options (2-12 items) are provided.",
    });
  }
 
  const requestBody = {
    chatId,
    caption,
    options,
    multipleAnswers: multipleAnswers || false,
  };
 
  const requestOptions = {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiToken}`,
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestBody),
  };
 
  try {
    const response = await fetch(
      `https://waapi.app/api/v1/instances/${instanceId}/client/action/create-poll`,
      requestOptions
    );
 
    if (!response.ok) {
      const errorResponse = await response.text();
      throw new Error(`Request failed with status code ${response.status}: ${errorResponse}`);
    }
 
    const data = await response.json();
    console.log("Raw API Response:", data); // Log the raw response
 
    // Construct the desired response structure
    const formattedResponse = {
      status: "success",
      instanceId: instanceId,
      data: {
        id: data.data?.id || null,
        ack: data.data?.ack || null,
        hasMedia: data.data?.hasMedia || null,
        body: data.data?.body || null,
        type: data.data?.type || null,
        timestamp: data.data?.timestamp || null,
        from: data.data?.from || null,
        to: data.data?.to || null,
        pollName: data.data?.pollName || null,
        pollOptions: data.data?.pollOptions || [],
        allowMultipleAnswers: data.data?.allowMultipleAnswers || false,
      },
      links: {
        self: `https://waapi.app/api/v1/instances/${instanceId}/client/action/create-poll`,
      },
    };
 
    console.log("Poll created successfully:", formattedResponse);
    res.status(200).json(formattedResponse);
  } catch (error) {
    console.error("Error creating poll:", error.message || error);
    res.status(500).json({ status: "error", message: "Failed to create poll", details: error.message });
  }
});