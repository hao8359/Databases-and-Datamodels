# -*- coding: utf-8 -*-

"""
MongoDB Messaging System for Clinic Management

This module implements a MongoDB-based messaging system that allows
communication between doctors/nurses and patients. It supports:

- Text and image messages
- User authentication and session management
- Real-time messaging between healthcare providers and patients
- Message history and conversation threads
- Image upload and storage capabilities

Requirements:
- pymongo
- bcrypt
- bson
- datetime
- base64
"""

# =============================================================================
# IMPORT STATEMENTS
# =============================================================================

import pymongo
from pymongo import MongoClient
from datetime import datetime, timezone
import bcrypt
import base64
import os
import mimetypes
from typing import Optional, List, Dict, Any
from bson import ObjectId
import json
from dotenv import load_dotenv, find_dotenv

# =============================================================================
# MONGODB CONNECTION CONFIGURATION
# =============================================================================

load_dotenv(find_dotenv())

password = os.environ.get("MONGODB_PWD")
connection_string = f"mongodb+srv://hao_db:{password}@lab2mongodb.1jekjhm.mongodb.net/?retryWrites=true&w=majority&appName=Lab2mongodb"
client = MongoClient(connection_string)

db = client.lab2mongodb

MONGODB_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'database': 'clinic_messaging'
}

# =============================================================================
# MONGODB MESSAGING CLASS
# =============================================================================

class MongoMessagingSystem:
    """
    MongoDB-based messaging system for clinic management.
    
    This class handles all messaging operations including:
    - User authentication and management
    - Message creation, retrieval, and management
    - Image handling and storage
    - Conversation thread management
    """
    
    def __init__(self, host='localhost', port=27017, database='clinic_messaging'):
        """
        Initialize MongoDB connection and collections.
        
        Args:
            host (str): MongoDB host address
            port (int): MongoDB port number
            database (str): Database name
        """
        self.host = host
        self.port = port
        self.database_name = database
        self.client = None
        self.db = None
        
        # Collection references
        self.users = None
        self.messages = None
        self.conversations = None
        self.user_sessions = None
        
    def connect(self) -> bool:
        """
        Establish connection to MongoDB and initialize collections.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(f"mongodb://{self.host}:{self.port}/?directConnection=true")
            self.db = self.client[self.database_name]
            
            # Initialize collections
            self.users = self.db['users']
            self.messages = self.db['messages']
            self.conversations = self.db['conversations']
            self.user_sessions = self.db['user_sessions']
            
            # Test connection
            self.client.admin.command('ping')
            print(f"Successfully connected to MongoDB: {self.database_name}")
            
            # Create indexes for better performance
            self._create_indexes()
            
            return True
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")
    
    def _create_indexes(self):
        """Create database indexes for better performance."""
        try:
            # User indexes
            self.users.create_index("username", unique=True)
            self.users.create_index("user_id")
            
            # Message indexes
            self.messages.create_index([("conversation_id", 1), ("timestamp", -1)])
            self.messages.create_index("sender_id")
            
            # Conversation indexes
            self.conversations.create_index("participants")
            self.conversations.create_index("last_activity")
            
            # Session indexes
            self.user_sessions.create_index("user_id")
            self.user_sessions.create_index("expires_at", expireAfterSeconds=0)
            
            print("Database indexes created successfully.")
            
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
    
    def create_user(self, username: str, password: str, user_type: str, 
                   first_name: str, last_name: str, user_id: Optional[int] = None) -> Optional[str]:
        """
        Create a new user account.
        
        Args:
            username (str): Unique username
            password (str): Plain text password (will be hashed)
            user_type (str): 'doctor', 'nurse', or 'patient'
            first_name (str): User's first name
            last_name (str): User's last name
            user_id (int, optional): External user ID from MySQL database
            
        Returns:
            str: User ObjectId if successful, None if failed
        """
        try:
            # Check if username already exists
            if self.users.find_one({"username": username}):
                print(f"Username {username} already exists.")
                return None
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            user_doc = {
                "username": username,
                "password_hash": password_hash,
                "user_type": user_type,
                "first_name": first_name,
                "last_name": last_name,
                "user_id": user_id,  # MySQL database ID
                "created_at": datetime.now(timezone.utc),
                "is_active": True,
                "profile_image": None
            }
            
            result = self.users.insert_one(user_doc)
            print(f"User {username} created successfully with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user credentials.
        
        Args:
            username (str): Username
            password (str): Plain text password
            
        Returns:
            dict: User information if authentication successful, None if failed
        """
        try:
            user = self.users.find_one({"username": username, "is_active": True})
            if not user:
                print(f"User {username} not found or inactive.")
                return None
            
            # Check password
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                # Create session
                session_id = self._create_session(str(user['_id']))
                
                user_info = {
                    "_id": str(user['_id']),
                    "username": user['username'],
                    "user_type": user['user_type'],
                    "first_name": user['first_name'],
                    "last_name": user['last_name'],
                    "user_id": user.get('user_id'),
                    "session_id": session_id
                }
                
                print(f"User {username} authenticated successfully.")
                return user_info
            else:
                print(f"Invalid password for user {username}.")
                return None
                
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def _create_session(self, user_id: str) -> str:
        """
        Create a user session.
        
        Args:
            user_id (str): User ObjectId
            
        Returns:
            str: Session ID
        """
        try:
            session_doc = {
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc).replace(hour=23, minute=59, second=59),
                "is_active": True
            }
            
            result = self.user_sessions.insert_one(session_doc)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error creating session: {e}")
            return ""
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """
        Validate user session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            str: User ID if session valid, None if invalid
        """
        try:
            session = self.user_sessions.find_one({
                "_id": ObjectId(session_id),
                "is_active": True,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            
            return session['user_id'] if session else None
            
        except Exception as e:
            print(f"Error validating session: {e}")
            return None
    
    def logout_user(self, session_id: str) -> bool:
        """
        Logout user by deactivating session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.user_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"is_active": False}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error logging out user: {e}")
            return False
    
    def get_or_create_conversation(self, participant1_id: str, participant2_id: str) -> Optional[str]:
        """
        Get existing conversation or create new one between two users.
        
        Args:
            participant1_id (str): First participant's user ID
            participant2_id (str): Second participant's user ID
            
        Returns:
            str: Conversation ObjectId if successful, None if failed
        """
        try:
            # Look for existing conversation
            conversation = self.conversations.find_one({
                "participants": {"$all": [participant1_id, participant2_id]}
            })
            
            if conversation:
                return str(conversation['_id'])
            
            # Create new conversation
            conversation_doc = {
                "participants": [participant1_id, participant2_id],
                "created_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "message_count": 0
            }
            
            result = self.conversations.insert_one(conversation_doc)
            print(f"New conversation created: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error getting/creating conversation: {e}")
            return None
    
    def send_message(self, sender_id: str, conversation_id: str, message_text: str = "", 
                    image_data: bytes = None, image_filename: str = "") -> Optional[str]:
        """
        Send a message with optional image attachment.
        
        Args:
            sender_id (str): Sender's user ID
            conversation_id (str): Conversation ID
            message_text (str): Text content of the message
            image_data (bytes, optional): Binary image data
            image_filename (str, optional): Original image filename
            
        Returns:
            str: Message ObjectId if successful, None if failed
        """
        try:
            message_doc = {
                "conversation_id": conversation_id,
                "sender_id": sender_id,
                "message_text": message_text,
                "timestamp": datetime.now(timezone.utc),
                "message_type": "text",
                "is_read": False
            }
            
            # Handle image attachment
            if image_data and image_filename:
                # Encode image as base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Get MIME type
                mime_type, _ = mimetypes.guess_type(image_filename)
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/jpeg'  # Default
                
                message_doc.update({
                    "message_type": "image",
                    "image_data": image_base64,
                    "image_filename": image_filename,
                    "image_mime_type": mime_type,
                    "image_size": len(image_data)
                })
            
            # Insert message
            result = self.messages.insert_one(message_doc)
            
            # Update conversation last activity
            self.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {"last_activity": datetime.now(timezone.utc)},
                    "$inc": {"message_count": 1}
                }
            )
            
            print(f"Message sent successfully: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 50, 
                                skip: int = 0) -> List[Dict]:
        """
        Retrieve messages from a conversation.
        
        Args:
            conversation_id (str): Conversation ID
            limit (int): Maximum number of messages to retrieve
            skip (int): Number of messages to skip
            
        Returns:
            list: List of message documents
        """
        try:
            messages = list(self.messages.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", -1).skip(skip).limit(limit))
            
            # Convert ObjectIds to strings and format timestamps
            for message in messages:
                message['_id'] = str(message['_id'])
                message['timestamp'] = message['timestamp'].isoformat()
            
            return list(reversed(messages))  # Return in chronological order
            
        except Exception as e:
            print(f"Error retrieving messages: {e}")
            return []
    
    def get_user_conversations(self, user_id: str) -> List[Dict]:
        """
        Get all conversations for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of conversation documents with participant info
        """
        try:
            conversations = list(self.conversations.find(
                {"participants": user_id}
            ).sort("last_activity", -1))
            
            result = []
            for conv in conversations:
                # Get other participant info
                other_participant_id = next(p for p in conv['participants'] if p != user_id)
                other_user = self.users.find_one({"_id": ObjectId(other_participant_id)})
                
                if other_user:
                    conv_info = {
                        "_id": str(conv['_id']),
                        "last_activity": conv['last_activity'].isoformat(),
                        "message_count": conv['message_count'],
                        "other_participant": {
                            "_id": str(other_user['_id']),
                            "username": other_user['username'],
                            "first_name": other_user['first_name'],
                            "last_name": other_user['last_name'],
                            "user_type": other_user['user_type']
                        }
                    }
                    result.append(conv_info)
            
            return result
            
        except Exception as e:
            print(f"Error retrieving conversations: {e}")
            return []
    
    def mark_messages_as_read(self, conversation_id: str, user_id: str) -> bool:
        """
        Mark all messages in a conversation as read for a specific user.
        
        Args:
            conversation_id (str): Conversation ID
            user_id (str): User ID who read the messages
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.messages.update_many(
                {
                    "conversation_id": conversation_id,
                    "sender_id": {"$ne": user_id},  # Don't mark own messages as read
                    "is_read": False
                },
                {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
            )
            
            print(f"Marked {result.modified_count} messages as read.")
            return True
            
        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return False
    
    def search_users(self, query: str, user_type: str = None) -> List[Dict]:
        """
        Search for users by name or username.
        
        Args:
            query (str): Search query
            user_type (str, optional): Filter by user type
            
        Returns:
            list: List of matching users
        """
        try:
            search_filter = {
                "$or": [
                    {"username": {"$regex": query, "$options": "i"}},
                    {"first_name": {"$regex": query, "$options": "i"}},
                    {"last_name": {"$regex": query, "$options": "i"}}
                ],
                "is_active": True
            }
            
            if user_type:
                search_filter["user_type"] = user_type
            
            users = list(self.users.find(
                search_filter,
                {
                    "_id": 1,
                    "username": 1,
                    "first_name": 1,
                    "last_name": 1,
                    "user_type": 1
                }
            ).limit(20))
            
            # Convert ObjectIds to strings
            for user in users:
                user['_id'] = str(user['_id'])
            
            return users
            
        except Exception as e:
            print(f"Error searching users: {e}")
            return []
    
    def get_unread_message_count(self, user_id: str) -> int:
        """
        Get count of unread messages for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            int: Number of unread messages
        """
        try:
            # Get all conversations for this user
            conversations = self.conversations.find({"participants": user_id})
            
            total_unread = 0
            for conv in conversations:
                unread_count = self.messages.count_documents({
                    "conversation_id": str(conv['_id']),
                    "sender_id": {"$ne": user_id},
                    "is_read": False
                })
                total_unread += unread_count
            
            return total_unread
            
        except Exception as e:
            print(f"Error getting unread message count: {e}")
            return 0
    
    def upload_profile_image(self, user_id: str, image_data: bytes, 
                           image_filename: str) -> bool:
        """
        Upload user profile image.
        
        Args:
            user_id (str): User ID
            image_data (bytes): Binary image data
            image_filename (str): Original filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Encode image as base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(image_filename)
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = 'image/jpeg'
            
            # Update user profile
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "profile_image": {
                            "data": image_base64,
                            "filename": image_filename,
                            "mime_type": mime_type,
                            "uploaded_at": datetime.now(timezone.utc)
                        }
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error uploading profile image: {e}")
            return False
    
    def create_sample_data(self):
        """Create sample users and conversations for testing."""
        try:
            # Create sample users
            sample_users = [
                {
                    "username": "dr.johnson",
                    "password": "doctor123",
                    "user_type": "doctor",
                    "first_name": "Anna",
                    "last_name": "Johnson",
                    "user_id": 1
                },
                {
                    "username": "nurse.smith",
                    "password": "nurse123",
                    "user_type": "nurse",
                    "first_name": "Sarah",
                    "last_name": "Smith",
                    "user_id": None
                },
                {
                    "username": "patient.brown",
                    "password": "patient123",
                    "user_type": "patient",
                    "first_name": "John",
                    "last_name": "Brown",
                    "user_id": 1
                },
                {
                    "username": "patient.davis",
                    "password": "patient123",
                    "user_type": "patient",
                    "first_name": "Mary",
                    "last_name": "Davis",
                    "user_id": 2
                }
            ]
            
            user_ids = {}
            for user_data in sample_users:
                user_id = self.create_user(**user_data)
                if user_id:
                    user_ids[user_data["username"]] = user_id
            
            print(f"Created {len(user_ids)} sample users.")
            
            # Create sample conversations and messages
            if len(user_ids) >= 3:
                # Doctor-Patient conversation
                conv_id = self.get_or_create_conversation(
                    user_ids["dr.johnson"], 
                    user_ids["patient.brown"]
                )
                
                if conv_id:
                    # Send some sample messages
                    self.send_message(
                        user_ids["dr.johnson"], 
                        conv_id, 
                        "Hello Mr. Brown, how are you feeling today?"
                    )
                    
                    self.send_message(
                        user_ids["patient.brown"], 
                        conv_id, 
                        "Hello Dr. Johnson, I'm feeling much better, thank you!"
                    )
                    
                    self.send_message(
                        user_ids["dr.johnson"], 
                        conv_id, 
                        "That's great to hear. Please continue taking your medication as prescribed."
                    )
                
                print("Sample conversations and messages created.")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def initialize_messaging_system() -> MongoMessagingSystem:
    """
    Initialize and setup the MongoDB messaging system.
    
    Returns:
        MongoMessagingSystem: Configured messaging system instance
    """
    messaging_system = MongoMessagingSystem(
        host=MONGODB_CONFIG['host'],
        port=MONGODB_CONFIG['port'],
        database=MONGODB_CONFIG['database']
    )
    
    if messaging_system.connect():
        print("MongoDB messaging system initialized successfully.")
        return messaging_system
    else:
        print("Failed to initialize MongoDB messaging system.")
        return None


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Test the messaging system
    print("Testing MongoDB Messaging System...")
    print("=" * 50)
    
    # Initialize system
    messaging = initialize_messaging_system()
    
    if messaging:
        try:
            # Create sample data
            print("\n1. Creating sample data...")
            messaging.create_sample_data()
            
            # Test authentication
            print("\n2. Testing authentication...")
            user = messaging.authenticate_user("dr.johnson", "doctor123")
            if user:
                print(f"Authenticated: {user['first_name']} {user['last_name']} ({user['user_type']})")
                
                # Test getting conversations
                print("\n3. Getting user conversations...")
                conversations = messaging.get_user_conversations(user['_id'])
                for conv in conversations:
                    print(f"Conversation with: {conv['other_participant']['first_name']} {conv['other_participant']['last_name']}")
                    
                    # Get messages
                    messages = messaging.get_conversation_messages(conv['_id'], limit=5)
                    for msg in messages:
                        sender_name = "You" if msg['sender_id'] == user['_id'] else conv['other_participant']['first_name']
                        print(f"  {sender_name}: {msg['message_text']}")
                
                # Logout
                messaging.logout_user(user['session_id'])
                print("\nUser logged out successfully.")
            
        except Exception as e:
            print(f"Error during testing: {e}")
        
        finally:
            messaging.disconnect()
    
    else:
        print("Could not initialize messaging system.")
        print("Please ensure MongoDB is running and accessible.")