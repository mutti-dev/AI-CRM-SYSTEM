<!-- # CRM System

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
This project is licensed under the MIT License. -->















# MaxRemind CRM Documentation

![MaxRemind Logo](https://private-us-east-1.manuscdn.com/sessionFile/8ElOglIYu1zKEzJyfOPBSn/sandbox/faA7CEymjdlB2ycieD6V2j-images_1744270657289_na1fn_L2hvbWUvdWJ1bnR1L2RvY3VtZW50YXRpb24vaW1hZ2VzL2xvZ28.svg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvOEVsT2dsSVl1MXpLRXpKeWZPUEJTbi9zYW5kYm94L2ZhQTdDRXltamRsQjJ5Y2llRDZWMmotaW1hZ2VzXzE3NDQyNzA2NTcyODlfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwyUnZZM1Z0Wlc1MFlYUnBiMjR2YVcxaFoyVnpMMnh2WjI4LnN2ZyIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc2NzIyNTYwMH19fV19&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=RfpTcC9HMzKeDY0H79YwfPCYRq4ThxlPxCBk7iXWAUENNw3HCqGhtb7Y~qUUh6Er6vUosiiQD4ABI~8bGJSDqFrYpuygy3~gKUSdqoSG2YKvAE8o~K~GP6bCG2G4ZR7RLroEMbh3-kar~JDS71AS5kt8ZCJj3GJeAm6vLF3Ubc99EoZZ40e5rZsIfy0fSU2EzBiiJ3O~cKUKq~KvUnKsm2DQoP1Dhs2Cg1WapkQH~2C6mto6YycouCUwCO8-GO8~ehgSIxu2YTpjhPKs0wdVRPCPuQQA6reqz060-jKAPjU0zhm7~v3vgIbkzN7bhltPwQfPss6ZP1pOzfV9SFZzoQ__)

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Introduction](#introduction)
   - [What is MaxRemind CRM?](#what-is-maxremind-crm)
   - [System Purpose and Goals](#system-purpose-and-goals)
   - [Key Features at a Glance](#key-features-at-a-glance)
3. [System Overview](#system-overview)
   - [Architecture Overview](#architecture-overview)
   - [Key Components](#key-components)
   - [Integration Ecosystem](#integration-ecosystem)
   - [Data Flow](#data-flow)
4. [User Interface](#user-interface)
   - [Navigation and Layout](#navigation-and-layout)
   - [Sidebar Navigation](#sidebar-navigation)
5. [Core Features](#core-features)
   - [Ticket Management](#ticket-management)
   - [Customer Management](#customer-management)
   - [Email Integration](#email-integration)
   - [AI-Powered Features](#ai-powered-features)
   - [Task Management](#task-management)
   - [Notification System](#notification-system)
6. [Additional Functionality](#additional-functionality)
   - [Data Upload](#data-upload)
   - [Settings and Configuration](#settings-and-configuration)
   - [Security Features](#security-features)
7. [User Workflows](#user-workflows)
   - [New Ticket Workflow](#new-ticket-workflow)
   - [Customer Inquiry Handling](#customer-inquiry-handling)
   - [Task Management Workflow](#task-management-workflow)
8. [Technical Documentation](#technical-documentation)
   - [System Architecture](#system-architecture)
   - [API Documentation](#api-documentation)
   - [Database Schema](#database-schema)
   - [Security Implementation](#security-implementation)
   - [Deployment Architecture](#deployment-architecture)
9. [Troubleshooting Guide](#troubleshooting-guide)
   - [Common Issues](#common-issues)
   - [Debugging Tools](#debugging-tools)

## Executive Summary

MaxRemind CRM is a comprehensive customer relationship management system designed to streamline ticket management and customer communication. Built with a modern technology stack, MaxRemind automates email processing, provides intelligent ticket organization, and offers powerful filtering capabilities to help businesses manage customer interactions efficiently.

The system integrates with Gmail for automatic email processing, leverages Gemini AI for intelligent analysis, and connects with Microsoft Teams for seamless notifications. With its intuitive interface and powerful backend, MaxRemind CRM helps businesses transform customer communications into organized, actionable tickets.

MaxRemind CRM is ideal for customer service teams, support departments, and any business that needs to track and manage customer communications effectively.

## Introduction

### What is MaxRemind CRM?

MaxRemind CRM is an automated customer relationship management system that transforms email communications into a structured ticket management workflow. The "Auto CRM System" specializes in capturing customer emails, converting them into trackable tickets, and providing tools to manage, respond to, and analyze customer interactions.

Unlike traditional CRM systems that require manual data entry, MaxRemind works in the background to automatically process incoming emails and create tickets, saving valuable time and reducing the risk of missed customer communications.

### System Purpose and Goals

The primary purpose of MaxRemind CRM is to simplify and automate customer communication management. The system aims to:

1. **Automate Email Processing**: Automatically capture emails from Gmail and convert them into trackable tickets without manual intervention.

2. **Centralize Customer Communications**: Provide a single platform where all customer interactions are stored, organized, and easily accessible.

3. **Enhance Response Efficiency**: Enable quick filtering, searching, and management of customer tickets to improve response times.

4. **Leverage AI for Insights**: Use Gemini AI capabilities to analyze ticket content and provide intelligent insights.

5. **Facilitate Team Collaboration**: Integrate with Microsoft Teams to keep team members informed about important customer interactions.

6. **Provide Actionable Data**: Organize customer communications in a way that makes it easy to track, prioritize, and act on customer needs.

### Key Features at a Glance

MaxRemind CRM offers a range of features designed to streamline customer relationship management:

- **Automated Ticket Creation**: Automatically converts emails into tickets with unique IDs
- **Intuitive Dashboard**: Provides an overview of ticket status and activity
- **Advanced Filtering**: Filter tickets by customer, time, and other parameters
- **Customer Management**: Track all communications with specific customers
- **Search Functionality**: Quickly find tickets using the search feature
- **Task Management**: Create and track tasks related to customer tickets
- **AI-Powered Analysis**: Leverage Gemini AI to gain insights from ticket content
- **Teams Integration**: Send notifications to Microsoft Teams channels
- **Responsive Design**: Access the system from various devices with a responsive interface

## System Overview

### Architecture Overview

MaxRemind CRM follows a modern client-server architecture with a clear separation between frontend and backend components:

- **Frontend**: Built with React.js, providing a responsive and interactive user interface
- **Backend**: Powered by Django (Python), handling data processing, API integrations, and business logic
- **Database**: Uses SQLite for data storage (with potential for scaling to larger databases)
- **External Integrations**: Connects with Google API (Gmail), Gemini AI, and Microsoft Teams

This architecture ensures a responsive user experience while providing powerful backend capabilities for email processing, data analysis, and integration with external services.

### Key Components

The system consists of several key components that work together to provide a complete CRM solution:

1. **User Interface Components**:
   - Dashboard for overview and metrics
   - Queries interface for ticket management
   - Tasks section for task tracking
   - Settings for system configuration
   - Ticket details screen for in-depth ticket information

2. **Backend Services**:
   - Email processing service (Gmail API integration)
   - Database management
   - Authentication and security
   - AI analysis service (Gemini API)
   - Notification service (Microsoft Teams webhook)

3. **Data Management**:
   - Customer records
   - Ticket storage and organization
   - Task tracking
   - User preferences and settings

### Integration Ecosystem

MaxRemind CRM integrates with several external services to enhance its capabilities:

1. **Google API Integration**:
   - Authenticates via OAuth 2.0
   - Accesses Gmail with the gmail.modify scope
   - Retrieves and processes emails automatically

2. **Gemini AI Integration**:
   - Analyzes ticket content for insights
   - Enhances ticket categorization and prioritization
   - Provides intelligent suggestions

3. **Microsoft Teams Integration**:
   - Sends notifications about important tickets
   - Alerts team members to customer issues
   - Facilitates team collaboration on customer communications

These integrations create a powerful ecosystem that automates many aspects of customer relationship management, reducing manual work and improving response times.

### Data Flow

The system follows a clear data flow process:

1. Emails are retrieved from Gmail via the Google API
2. The system processes these emails and creates tickets
3. Tickets are stored in the database with relevant metadata
4. The frontend displays tickets and allows filtering/searching
5. Users can interact with tickets, add notes, and create tasks
6. AI processing via Gemini API enhances ticket analysis
7. Notifications can be sent to Teams via webhook when needed

This streamlined data flow ensures that customer communications are captured, processed, and made available for action without manual intervention.

## User Interface

### Navigation and Layout

MaxRemind CRM features a clean, intuitive interface designed for efficiency and ease of use. The main layout consists of:

- **Left Sidebar**: Contains the main navigation menu with access to Dashboard, Queries, Tasks, and Settings
- **Main Content Area**: Displays the active section's content (ticket listings, details, dashboard metrics, etc.)
- **Top Bar**: Features global search functionality for finding tickets by ID

The interface follows a consistent design language throughout the application, with a dark theme that reduces eye strain during extended use. The responsive design ensures the system works well on various screen sizes.

![Queries Interface](https://private-us-east-1.manuscdn.com/sessionFile/8ElOglIYu1zKEzJyfOPBSn/sandbox/faA7CEymjdlB2ycieD6V2j-images_1744270657290_na1fn_L2hvbWUvdWJ1bnR1L2RvY3VtZW50YXRpb24vaW1hZ2VzL3F1ZXJpZXNfaW50ZXJmYWNl.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvOEVsT2dsSVl1MXpLRXpKeWZPUEJTbi9zYW5kYm94L2ZhQTdDRXltamRsQjJ5Y2llRDZWMmotaW1hZ2VzXzE3NDQyNzA2NTcyOTBfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwyUnZZM1Z0Wlc1MFlYUnBiMjR2YVcxaFoyVnpMM0YxWlhKcFpYTmZhVzUwWlhKbVlXTmwucG5nIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3MjI1NjAwfX19XX0_&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=gP5zy1trmuzr8SBMFO~HHuMLLoFi6R3NCb0sFQj8LDg~nrSl5S3iP6jRx3xVBs4M6o2-x5J39-Oe1NHB9mYO2vciWR6xNBaP32juMW0krJpqjC-mlrwGkw1NbuwWOJ~hPh5smNznUAd4q1qbIKv~b3TstWWnIX7lB3xHc~xP~TwM-n19acraBNdvsfHCMT4LtufF0dujrEgEWb~gc41rKydGtJnl94Y80OMScaDgndUmjGgSiYS5WlL-JaNaCW-YpjDqhKBuNYSPEiyAy6mlG1S-8kyZVilmbpxHewRBBwXJn3jnb7P8l0dLs0d91YMO~yX-D76s~TeVSiMdPTibwQ__)
*Figure 1: MaxRemind CRM Queries Interface showing ticket listing and filtering options*

### Sidebar Navigation

The sidebar serves as the primary navigation hub, allowing users to quickly switch between different sections of the application:

- **Dashboard**: Overview of system activity and key metrics
- **Queries**: Main ticket management interface
- **Tasks**: Task creation and tracking
- **Settings**: System configuration and user preferences

The sidebar can be collapsed to provide more screen space for the main content area, particularly useful when working with detailed ticket information or on smaller screens.

## Core Features

### Ticket Management

The ticket management system is the central feature of MaxRemind CRM, providing a comprehensive solution for handling customer communications:

#### Ticket Listing and Organization

- **Unique Ticket IDs**: Each ticket receives a unique numerical identifier for easy reference
- **Chronological Display**: Tickets are displayed in chronological order, with the most recent at the top
- **Subject Preview**: Shows a preview of the ticket subject for quick identification
- **Timestamp Information**: Displays when the ticket was received (e.g., "21 hours ago", "Yesterday, Wed 3:10 AM")
- **Customer Association**: Each ticket is linked to a specific customer

#### Filtering and Search

- **Customer Filtering**: Filter tickets by specific customer or view all customers
- **Time-based Filtering**: Filter tickets by time periods
- **Search Functionality**: Search for specific tickets by ID
- **Additional Search**: Search within ticket content (available in the search bar)

#### Ticket Details

When accessing a specific ticket, users can view:

- Complete message content
- Customer information
- Communication history
- Related tasks
- Response options

### Customer Management

MaxRemind CRM provides tools for managing customer information and tracking all interactions with each customer:

- **Customer Profiles**: Store essential customer information
- **Communication History**: View all tickets and interactions with a specific customer
- **Customer Filtering**: Easily filter tickets by customer name
- **Customer Dropdown**: Quick access to customer list for filtering

### Email Integration

The system's email integration capabilities form the foundation of its automated ticket creation:

- **Gmail API Connection**: Securely connects to Gmail using OAuth 2.0
- **Automatic Email Processing**: Monitors specified email accounts for new messages
- **Email to Ticket Conversion**: Automatically converts emails into tickets
- **Metadata Extraction**: Pulls sender information, subject, timestamp, and content
- **Attachment Handling**: Processes and stores email attachments

### AI-Powered Features

MaxRemind CRM leverages the Gemini API to provide intelligent analysis and automation:

- **Content Analysis**: Analyzes ticket content to identify key information
- **Sentiment Detection**: Identifies customer sentiment for prioritization
- **Automatic Categorization**: Suggests categories for tickets based on content
- **Response Suggestions**: Provides suggested responses based on ticket content
- **Priority Assignment**: Suggests priority levels based on content analysis

### Task Management

The task management feature helps teams organize work related to customer tickets:

- **Task Creation**: Create tasks related to specific tickets or customers
- **Assignment**: Assign tasks to team members
- **Due Dates**: Set deadlines for task completion
- **Status Tracking**: Monitor task progress (pending, in progress, completed)
- **Task Filtering**: Filter tasks by assignee, status, or due date

### Notification System

MaxRemind CRM includes a notification system to keep team members informed:

- **Microsoft Teams Integration**: Sends notifications to Teams channels
- **Webhook Functionality**: Uses webhooks for real-time notifications
- **Alert Types**: Various notification types for different events (new tickets, urgent issues, task assignments)
- **Customizable Notifications**: Configure which events trigger notifications

## Additional Functionality

### Data Upload

The system includes functionality for uploading datasets:

- **Upload Interface**: Dedicated interface for uploading data
- **Format Support**: Supports various data formats
- **Data Validation**: Validates uploaded data for integrity
- **Batch Processing**: Processes uploaded data in batches

### Settings and Configuration

The settings section allows users to configure the system according to their needs:

- **User Preferences**: Customize the user experience
- **Integration Settings**: Configure connections to external services
- **Notification Preferences**: Set notification rules and preferences
- **System Configuration**: Adjust system-wide settings

### Security Features

MaxRemind CRM includes several security features to protect sensitive customer data:

- **Authentication**: Secure login system
- **Authorization**: Role-based access control
- **API Security**: Secure API connections with tokens
- **Data Protection**: Encryption for sensitive data

## User Workflows

### New Ticket Workflow

1. Email is received in the connected Gmail account
2. System automatically processes the email and creates a ticket
3. Ticket appears in the Queries section with customer information and subject
4. Optional AI analysis provides additional context and suggestions
5. User can view ticket details, respond, or create related tasks
6. Notifications can be sent to Teams for urgent tickets

### Customer Inquiry Handling

1. User receives notification of new ticket
2. User navigates to Queries section and locates the ticket
3. User opens ticket details to view complete information
4. User can respond directly from the ticket interface
5. Response is sent to customer and recorded in the system
6. Ticket status is updated accordingly

### Task Management Workflow

1. User identifies action needed from a ticket
2. User creates a task with description and deadline
3. Task is assigned to appropriate team member
4. Assignee receives notification of new task
5. Task progress is updated as work progresses
6. Task is marked complete when finished
7. Ticket is updated to reflect completed action

## Technical Documentation

### System Architecture

#### Frontend Architecture

The frontend of MaxRemind CRM is built using React.js, a popular JavaScript library for building user interfaces. The frontend architecture follows these key principles:

##### Component Structure

The React application is organized into reusable components:

```
/components
  /Dashboard.js       # Main dashboard view
  /DetailsScreen.js   # Ticket details view
  /Queries.js         # Ticket listing and filtering
  /Settings.js        # System configuration
  /Sidebar.js         # Main navigation sidebar
  /Sidebar2.js        # Alternative sidebar for details view
  /Tasks.js           # Task management interface
  /TicketTabs.js      # Tab navigation for tickets
  /UploadDataset.js   # Data upload interface
```

##### Routing

The application uses React Router for navigation between different views:

```javascript
// From App.js
<Routes>
  <Route path="/" element={<Dashboard />} />
  <Route path="/queries" element={<Queries />} />
  <Route path="/tasks" element={<Tasks />} />
  <Route path="/settings" element={<Settings />} />
  <Route path="/details/:id" element={<DetailsScreen />} />
  <Route path="/upload-dataset" element={<UploadDataset />} />
</Routes>
```

This routing structure allows for deep linking and browser history integration.

#### Backend Architecture

The backend of MaxRemind CRM is built using Django, a high-level Python web framework. The backend follows these architectural patterns:

##### Project Structure

The Django project is named `crm_system` as identified in the manage.py file:

```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_system.settings')
```

The standard Django project structure is followed, with apps organized by functionality.

##### Database

The system uses SQLite as its database (db.sqlite3), which is suitable for development and smaller deployments. For production environments with higher load, the system can be configured to use PostgreSQL or MySQL.

### API Documentation

#### Internal APIs

The system implements several internal APIs for communication between frontend and backend:

##### Ticket API

- `GET /api/tickets/` - List all tickets with optional filtering
- `GET /api/tickets/{id}/` - Get details for a specific ticket
- `POST /api/tickets/` - Create a new ticket
- `PUT /api/tickets/{id}/` - Update a ticket
- `DELETE /api/tickets/{id}/` - Delete a ticket

##### Customer API

- `GET /api/customers/` - List all customers
- `GET /api/customers/{id}/` - Get details for a specific customer
- `POST /api/customers/` - Create a new customer
- `PUT /api/customers/{id}/` - Update a customer
- `DELETE /api/customers/{id}/` - Delete a customer

#### External API Integration

##### Google Gmail API

The system uses the Gmail API to:
1. Authenticate with OAuth 2.0
2. Retrieve emails from the user's inbox
3. Process email content and metadata
4. Create tickets based on email content

##### Gemini API

The system uses the Gemini API for AI-powered features:

```python
import google.generativeai as genai

def analyze_ticket_content(content):
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(f"Analyze this customer ticket: {content}")
    return response.text
```

##### Microsoft Teams Webhook

The system sends notifications to Microsoft Teams using the webhook URL:

```python
import requests
import json

def send_teams_notification(title, message, importance='normal'):
    webhook_url = os.getenv('WEBHOOK_URL')
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Medium",
                            "weight": "Bolder",
                            "text": title
                        },
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True
                        }
                    ],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.0"
                }
            }
        ]
    }
    
    response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    return response.status_code
```

### Database Schema

The system uses a relational database with the following key tables:

#### Customers Table

```
id: Integer (Primary Key)
name: String
email: String
phone: String
created_at: DateTime
updated_at: DateTime
```

#### Tickets Table

```
id: Integer (Primary Key)
customer_id: Integer (Foreign Key)
subject: String
content: Text
status: String (enum: new, in_progress, resolved, closed)
priority: String (enum: low, medium, high, urgent)
created_at: DateTime
updated_at: DateTime
email_id: String (Gmail message ID)
```

#### Tasks Table

```
id: Integer (Primary Key)
ticket_id: Integer (Foreign Key)
title: String
description: Text
assignee: String
due_date: DateTime
status: String (enum: pending, in_progress, completed)
created_at: DateTime
updated_at: DateTime
```

### Security Implementation

#### Authentication

The system implements token-based authentication for API access:

1. Users authenticate with username/password
2. System issues a JWT (JSON Web Token)
3. Frontend includes this token in all API requests
4. Backend validates the token for each request

#### OAuth Integration

For Google API access, the system uses OAuth 2.0:

1. User authorizes the application to access their Gmail
2. Google provides an access token and refresh token
3. System stores these tokens securely
4. Tokens are used for subsequent API calls
5. Refresh token is used to obtain new access tokens when needed

#### Environment Variables

Sensitive configuration is stored in environment variables:

```
GEMINI_API_KEY=AIzaSyDM_wO7kDONoQI05cWYRUMJKmo5_VRPkZY
WEBHOOK_URL=https://pern.webhook.office.com/webhookb2/...
```

This prevents sensitive information from being stored in the codebase.

### Deployment Architecture

#### Development Environment

For development, the system can be run locally:

1. Frontend: `npm start` (React development server)
2. Backend: `python manage.py runserver` (Django development server)

#### Production Deployment

For production, the recommended deployment architecture is:

1. **Frontend**:
   - Build React app with `npm run build`
   - Deploy static files to CDN or web server
   - Configure for HTTPS

2. **Backend**:
   - Deploy Django with Gunicorn/uWSGI
   - Use Nginx as reverse proxy
   - Configure for HTTPS
   - Set up proper environment variables

3. **Database**:
   - Migrate from SQLite to PostgreSQL or MySQL
   - Configure proper backups and replication

## Troubleshooting Guide

### Common Issues

1. **Email Integration Issues**:
   - Check Gmail API credentials
   - Verify OAuth token validity
   - Ensure proper scopes are configured

2. **AI Feature Issues**:
   - Verify Gemini API key
   - Check API rate limits
   - Validate input data format

3. **Notification Issues**:
   - Verify Teams webhook URL
   - Check network connectivity
   - Validate payload format

### Debugging Tools

- Browser developer tools for frontend issues
- Django debug toolbar for backend issues
- API testing tools (Postman, curl)
- Log analysis

## Conclusion

MaxRemind CRM provides a powerful, automated solution for customer relationship management with a focus on email processing and ticket management. By leveraging modern technologies and integrations with Google, Gemini AI, and Microsoft Teams, the system streamlines customer communication workflows and enhances team collaboration.

The combination of an intuitive user interface, powerful backend processing, and intelligent AI features makes MaxRemind CRM an ideal solution for businesses looking to improve their customer service operations and response times.

With its scalable architecture and comprehensive feature set, MaxRemind CRM can grow with your business needs while continuing to provide efficient customer relationship management capabilities.
