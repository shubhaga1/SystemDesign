 Building a Collaborative Messenger System: Schema, Code Snippet, and Dummy Data Example

Introduction:
In this GitHub repository, we explore the schema, provide a code snippet, and showcase a dummy data example for a collaborative messenger system. This system enables seamless communication between users in private and group conversations. Let's dive in!

Schema Overview:
The schema consists of four main tables:

1. User Table:
   - Columns: user_id, username, email, password, created_at, updated_at
   - This table stores user information, including their unique ID, username, email, and password.
   - The created_at and updated_at columns track the creation and update timestamps of user records.

2. Messenger Conversation Table:
   - Columns: conversation_id, name, created_at, updated_at
   - This table represents conversations and includes a unique conversation ID, a name for the conversation, and timestamps for creation and updates.

3. Participant Table:
   - Columns: participant_id, conversation_id, user_id, role, joined_at
   - This table manages the relationship between users and conversations.
   - It maps the user_id and conversation_id, indicating the users participating in each conversation.
   - The role column specifies the user's role in the conversation (e.g., member, admin).
   - The joined_at column stores the timestamp when a participant joined the conversation.

4. Messenger Message Table:
   - Columns: message_id, conversation_id, sender_id, receiver_id, content, sent_at, seen_at, delivered_at, created_at, updated_at
   - This table stores the messages exchanged within conversations.
   - The message_id is a unique identifier for each message.
   - The conversation_id links the message to its corresponding conversation.
   - The sender_id and receiver_id represent the user IDs of the sender and receiver respectively.
   - The content column holds the message content.
   - The sent_at, seen_at, and delivered_at columns track the timestamps for message sent, seen, and delivered statuses.
   - The created_at and updated_at columns record the creation and update timestamps of message records.

Code Snippet (Java - JDBC):
```java
// Establish a database connection
Connection connection = DriverManager.getConnection("jdbc:mysql://localhost:3306/messenger", "username", "password");

// Insert a new user
String insertUserQuery = "INSERT INTO User (user_id, username, email, password) VALUES (?, ?, ?, ?)";
PreparedStatement insertUserStatement = connection.prepareStatement(insertUserQuery);
insertUserStatement.setString(1, "1");
insertUserStatement.setString(2, "John");
insertUserStatement.setString(3, "john@example.com");
insertUserStatement.setString(4, "password");
insertUserStatement.executeUpdate();

// Create a new conversation
String insertConversationQuery = "INSERT INTO MessengerConversation (conversation_id, name) VALUES (?, ?)";
PreparedStatement insertConversationStatement = connection.prepareStatement(insertConversationQuery);
insertConversationStatement.setString(1, "1");
insertConversationStatement.setString(2, "My Group Chat");
insertConversationStatement.executeUpdate();

// Add a participant to a conversation
String insertParticipantQuery = "INSERT INTO Participant (participant_id, conversation_id, user_id, role, joined_at) VALUES (?, ?, ?, ?, ?)";
PreparedStatement insertParticipantStatement = connection.prepareStatement(insertParticipantQuery);
insertParticipantStatement.setString(1, "1");
insertParticipantStatement.setString(2, "1");
insertParticipantStatement.setString(3, "1");
insertParticipantStatement.setString(4, "member");
insertParticipantStatement.setTimestamp(5, new Timestamp(System.currentTimeMillis()));
insertParticipantStatement.executeUpdate();

// Send a message
String insertMessageQuery = "INSERT INTO MessengerMessage (message_id, conversation_id, sender_id, receiver_id, content, sent_at,

 created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)";
PreparedStatement insertMessageStatement = connection.prepareStatement(insertMessageQuery);
insertMessageStatement.setString(1, "1");
insertMessageStatement.setString(2, "1");
insertMessageStatement.setString(3, "1");
insertMessageStatement.setString(4, "2");
insertMessageStatement.setString(5, "Hello there!");
insertMessageStatement.setTimestamp(6, new Timestamp(System.currentTimeMillis()));
insertMessageStatement.setTimestamp(7, new Timestamp(System.currentTimeMillis()));
insertMessageStatement.setTimestamp(8, new Timestamp(System.currentTimeMillis()));
insertMessageStatement.executeUpdate();

// Close the database connection
connection.close();
```

Dummy Data Example:
Here's an example of how the schema can be populated with dummy data:

User Table:
```
user_id | username | email               | password  | created_at           | updated_at
-----------------------------------------------------------------------------------------
1       | John     | john@example.com    | password  | 2023-06-01 10:00:00  | 2023-06-01 10:00:00
2       | Jane     | jane@example.com    | password  | 2023-06-01 11:00:00  | 2023-06-01 11:00:00
```

Messenger Conversation Table:
```
conversation_id | name            | created_at           | updated_at
---------------------------------------------------------------------
1               | My Group Chat   | 2023-06-01 12:00:00  | 2023-06-01 12:00:00
```

Participant Table:
```
participant_id | conversation_id | user_id | role    | joined_at
-----------------------------------------------------------------
1              | 1               | 1       | member  | 2023-06-01 12:30:00
2              | 1               | 2       | member  | 2023-06-01 12:30:00
```

Messenger Message Table:
```
message_id | conversation_id | sender_id | receiver_id | content       | sent_at              | seen_at | delivered_at | created_at           | updated_at
--------------------------------------------------------------------------------------------------------------------------------------------------------------
1          | 1               | 1         | 2           | Hello there!  | 2023-06-01 13:00:00  | NULL    | NULL         | 2023-06-01 13:00:00  | 2023-06-01 13:00:00
```

Feel free to check out the full code snippet and dummy data example in the GitHub repository [link to the repository]. I'd love to hear your thoughts on building collaborative messenger systems!

#github #messenger #systemdesign #collaboration
