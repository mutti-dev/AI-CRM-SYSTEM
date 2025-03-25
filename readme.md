# CRM System

This project is a Customer Relationship Management (CRM) system designed to handle customer queries via email, automate responses, and assign tasks to teams or agents. It integrates with the Gmail API for email handling and provides a dashboard for monitoring system performance.

---

## Features

### 1. **Customer**
- Unique customers are identified by their email addresses.
- Simplifies tracking conversations over time.

### 2. **FAQ**
- Stores FAQs with keyword-based matching for quick retrieval.
- Easily managed via the Django Admin panel.

### 3. **EmailQuery**
- Captures incoming emails from Gmail with sender, content, and thread ID for proper threading.
- Flags complex queries for manual intervention.
- Assignable to teams or agents.

### 4. **EmailReply**
- Stores automated or manual responses.
- Maintains Gmail Message ID for threading consistency.

### 5. **Task**
- Allows assigning tasks to teams or individual agents.
- Tracks progress and status.
- Integrated tightly with queries for streamlined management.

### 6. **EmailLog**
- Provides extensive logging and tracking capabilities for monitoring and debugging purposes.

---

## API Endpoints

### 1. **Fetch Unread Emails**
- **Endpoint**: `/api/fetch-emails/`
- **Method**: `POST`

#### **Purpose**:
Fetch unread emails from Gmail using the Gmail API and store them in the `EmailQuery` model.

#### **Flow**:
1. The Gmail API fetches unread emails from the user's inbox.
2. For each email:
   - Check if the `gmail_thread_id` already exists in the database.
   - If not, create a new `EmailQuery` entry with the email details.
3. Return the number of new emails fetched.

#### **Example Response**:
```json
{
    "status": "success",
    "emails_fetched": 5
}
```

---

### 2. **Process Queries**
- **Endpoint**: `/api/process-queries/`
- **Method**: `POST`

#### **Purpose**:
Process email queries stored in the `EmailQuery` model. Match queries with FAQs and send automated replies for matched queries. Mark unmatched queries as complex for manual intervention.

#### **Flow**:
1. Retrieve all email queries where `is_replied=False`.
2. For each query:
   - Match the query content with the `keywords` field in the `FAQ` model.
   - If a match is found:
     - Send an automated reply using the Gmail API.
     - Create an `EmailReply` entry.
     - Mark the query as `is_replied=True` and `is_complex=False`.
   - If no match is found:
     - Mark the query as `is_complex=True`.
3. Return the number of processed queries.

#### **Example Response**:
```json
{
    "status": "success",
    "processed_queries": 5
}
```

---

### 3. **Assign Tasks**
- **Endpoint**: `/api/assign-task/`
- **Method**: `POST`

#### **Purpose**:
Assign tasks to teams or agents for complex queries.

#### **Flow**:
1. Accept the following data in the request body:
   - `email_query_id`: The ID of the query for which the task is being created.
   - `title`: The title of the task.
   - `description`: A description of the task.
   - `assigned_team_id` (optional): The ID of the team to assign the task to.
   - `assigned_agent_id` (optional): The ID of the agent to assign the task to.
   - `due_date` (optional): The due date for the task.
2. Create a new `Task` entry in the database.
3. Return the ID of the created task.

#### **Example Request**:
```json
{
    "email_query_id": 1,
    "title": "Follow up on customer query",
    "description": "Customer requires detailed explanation.",
    "assigned_team_id": 2,
    "assigned_agent_id": 3,
    "due_date": "2025-03-30T12:00:00Z"
}
```

#### **Example Response**:
```json
{
    "status": "success",
    "task_id": 10
}
```

---

### 4. **Reply to Emails**
- **Endpoint**: `/api/reply-email/`
- **Method**: `POST`

#### **Purpose**:
Send a manual reply to an email query.

#### **Flow**:
1. Accept the following data in the request body:
   - `email_query_id`: The ID of the query to reply to.
   - `content`: The reply content.
2. Use the Gmail API to send the reply.
3. Create an `EmailReply` entry in the database.
4. Mark the query as `is_replied=True`.
5. Return the Gmail message ID of the sent reply.

#### **Example Request**:
```json
{
    "email_query_id": 1,
    "content": "Thank you for reaching out. We will get back to you shortly."
}
```

#### **Example Response**:
```json
{
    "status": "success",
    "gmail_message_id": "1789abcdef123456"
}
```

---

### 5. **Dashboard Data**
- **Endpoint**: `/api/dashboard-data/`
- **Method**: `GET`

#### **Purpose**:
Provide statistics for the admin dashboard.

#### **Flow**:
1. Count the following:
   - Total email queries (`queries`).
   - Replied queries (`replied_queries`).
   - Complex queries (`complex_queries`).
   - Total tasks (`tasks`).
   - Total email logs (`logs`).
2. Return the counts in a JSON response.

#### **Example Response**:
```json
{
    "queries": 10,
    "replied_queries": 7,
    "complex_queries": 3,
    "tasks": 5,
    "logs": 15
}
```

---

## Full Workflow

1. **Fetch Emails**:
   - Use `/api/fetch-emails/` to fetch unread emails and store them in the database.

2. **Process Queries**:
   - Use `/api/process-queries/` to process the fetched queries.
   - Automatically reply to simple queries and mark complex ones for manual intervention.

3. **Assign Tasks**:
   - Use `/api/assign-task/` to assign tasks for complex queries to teams or agents.

4. **Reply to Emails**:
   - Use `/api/reply-email/` to manually reply to queries that require human intervention.

5. **Monitor Dashboard**:
   - Use `/api/dashboard-data/` to monitor the system's performance and statistics.

---

## Installation and Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd CRM-SYSTEM
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the database in `settings.py`.

4. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

---

## License
This project is licensed under the MIT License.