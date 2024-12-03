
from flask import Flask, request, jsonify, render_template_string
from enum import Enum
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
import sys

app = Flask(__name__)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('chatbot.log')
    ]
)
logger = logging.getLogger(__name__)


db_config = {
    'host': 'db',
    'user': 'root',
    'password': '',
    'database': 'crtvai_db'
}

HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CRTVAI Chatbot by Al-Amin</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background-color: #f0f2f5;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .chat-container {
            width: 100%;
            max-width: 600px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .chat-header {
            background: #3498db;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 1.5em;
        }

        .phone-input-container {
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }

        #phoneNumber {
            width: 100%;
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-size: 16px;
            outline: none;
        }

        #phoneNumber:focus {
            border-color: #3498db;
            box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
        }

        .messages-container {
            height: 400px;
            padding: 20px;
            overflow-y: auto;
            background: #fff;
        }

        .message {
            margin: 10px 0;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }

        .user-message {
            background: #3498db;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }

        .bot-message {
            background: #f1f0f0;
            color: #333;
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }

        .input-container {
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
        }

        #messageInput {
            flex: 1;
            padding: 12px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-size: 16px;
            outline: none;
        }

        #messageInput:focus {
            border-color: #3498db;
            box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
        }

        button {
            padding: 12px 24px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }

        button:hover {
            background: #2980b9;
        }

        button:active {
            transform: scale(0.98);
        }

        .error-message {
            background: #fee;
            color: #e74c3c;
            padding: 10px;
            margin: 10px 0;
            border-radius: 6px;
            text-align: center;
            display: none;
        }

        
        .loading {
            display: none;
            margin: 10px auto;
            text-align: center;
            color: #666;
        }

        .loading:after {
            content: '';
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid #666;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s linear infinite;
            margin-left: 5px;
        }

        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }

       
        @media (max-width: 768px) {
            .chat-container {
                height: 100vh;
                border-radius: 0;
                max-width: 100%;
            }

            .messages-container {
                height: calc(100vh - 200px);
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            CRTVAI Chatbot by Al-Amin
        </div>
        <div class="phone-input-container">
            <input type="text" id="phoneNumber" placeholder="Enter your phone number" maxlength="15">
        </div>
        <div class="error-message" id="errorMessage"></div>
        <div class="messages-container" id="messagesContainer"></div>
        <div class="loading" id="loadingIndicator">Sending message...</div>
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Type your message...">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const messagesContainer = document.getElementById('messagesContainer');
        const messageInput = document.getElementById('messageInput');
        const phoneInput = document.getElementById('phoneNumber');
        const errorMessage = document.getElementById('errorMessage');
        const loadingIndicator = document.getElementById('loadingIndicator');

        
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
            setTimeout(() => {
                errorMessage.style.display = 'none';
            }, 3000);
        }

        function addMessage(message, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            messageDiv.textContent = message;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            const phoneNumber = phoneInput.value.trim();

            if (!message) {
                showError('Please enter a message');
                return;
            }

            if (!phoneNumber) {
                showError('Please enter your phone number');
                return;
            }

            
            addMessage(message, true);
            messageInput.value = '';

           
            loadingIndicator.style.display = 'block';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_phone: phoneNumber,
                        user_message: message
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    addMessage(data.bot_message, false);
                } else {
                    showError(data.bot_message || 'An error occurred');
                }
            } catch (error) {
                console.error('Error:', error);
                showError('Failed to connect to server');
            } finally {
                loadingIndicator.style.display = 'none';
            }
        }

        
        phoneInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9+]/g, '');
        });

        
        messageInput.focus();
    </script>
</body>
</html>
'''

# Define conversation states
class ConversationState(Enum):
    INITIAL = "initial"
    WAITING_FOR_NAME = "waiting_for_name"
    WAITING_FOR_SONG = "waiting_for_song"
    COMPLETED = "completed"

def init_db():
    """Initialize database and create necessary tables"""
    import time
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    phone_number VARCHAR(20) PRIMARY KEY,
                    user_name VARCHAR(100),
                    favorite_song VARCHAR(200),
                    conversation_state VARCHAR(50),
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
            cursor.close()
            conn.close()
            break
            
        except Error as e:
            retry_count += 1
            logger.warning(f"Database connection attempt {retry_count}/{max_retries} failed: {e}")
            if retry_count == max_retries:
                logger.error("Max retries reached. Could not connect to database.")
                raise
            time.sleep(1)

class DatabaseManager:
    @staticmethod
    def get_connection():
        try:
            return mysql.connector.connect(**db_config)
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    @staticmethod
    def get_session(user_phone):
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('SELECT * FROM user_sessions WHERE phone_number = %s', (user_phone,))
            session = cursor.fetchone()
            
            if not session:
                cursor.execute(
                    'INSERT INTO user_sessions (phone_number, conversation_state) VALUES (%s, %s)',
                    (user_phone, ConversationState.INITIAL.value)
                )
                conn.commit()
                
                session = {
                    'phone_number': user_phone,
                    'conversation_state': ConversationState.INITIAL.value,
                    'user_name': None,
                    'favorite_song': None
                }
            
            return session
            
        except Error as e:
            logger.error(f"Database error in get_session: {e}")
            raise
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    @staticmethod
    def update_session(user_phone, state, name=None, song=None):
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            
            if name:
                cursor.execute(
                    'UPDATE user_sessions SET conversation_state = %s, user_name = %s WHERE phone_number = %s',
                    (state.value, name, user_phone)
                )
            elif song:
                cursor.execute(
                    'UPDATE user_sessions SET conversation_state = %s, favorite_song = %s WHERE phone_number = %s',
                    (state.value, song, user_phone)
                )
            else:
                cursor.execute(
                    'UPDATE user_sessions SET conversation_state = %s WHERE phone_number = %s',
                    (state.value, user_phone)
                )
            
            conn.commit()
            
        except Error as e:
            logger.error(f"Database error in update_session: {e}")
            raise
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

def process_message(message, state, session):
    
    
    if state == ConversationState.INITIAL:
        if message.lower() == "hello":
            return "What is your name?", ConversationState.WAITING_FOR_NAME
        return "Invalid initial input, please say hello.", ConversationState.INITIAL
    
    elif state == ConversationState.WAITING_FOR_NAME:
        return f"Hello {message}, what is your favorite song?", ConversationState.WAITING_FOR_SONG
    
    elif state == ConversationState.WAITING_FOR_SONG:
        return f"Playing {message}", ConversationState.COMPLETED
    
    elif state == ConversationState.COMPLETED:
        return f"Hello {session['user_name']}! Your favorite song is {session['favorite_song']}", state

@app.route('/')
def home():
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return empty response with No Content status

@app.route('/chat', methods=['POST'])
def chat():
   
    logger.info("Received chat request")
    
    try:
        
        if not request.is_json:
            logger.warning("Invalid content type received")
            return jsonify({
                "user_phone": "",
                "bot_message": "Content-Type must be application/json"
            }), 400

        
        data = request.get_json()
        
        if not isinstance(data, dict):
            logger.warning("Request data is not a JSON object")
            return jsonify({
                "user_phone": "",
                "bot_message": "Invalid request format"
            }), 400
            
        if "user_phone" not in data or "user_message" not in data:
            logger.warning("Missing required fields in request")
            return jsonify({
                "user_phone": "",
                "bot_message": "Request must contain user_phone and user_message"
            }), 400

        
        user_phone = str(data["user_phone"]).strip()
        user_message = str(data["user_message"]).strip()
        
        if not user_phone or not user_message:
            logger.warning("Empty phone number or message received")
            return jsonify({
                "user_phone": user_phone,
                "bot_message": "Phone number and message cannot be empty"
            }), 400

        logger.info(f"Processing message for phone: {user_phone}")
        
        try:
           
            session = DatabaseManager.get_session(user_phone)
            if not session:
                logger.error(f"Failed to create/retrieve session for phone: {user_phone}")
                return jsonify({
                    "user_phone": user_phone,
                    "bot_message": "Failed to process your request"
                }), 500

            
            current_state = ConversationState(session['conversation_state'])
            logger.info(f"Current state for {user_phone}: {current_state.value}")
            
            
            response, new_state = process_message(user_message, current_state, session)
            logger.info(f"New state for {user_phone}: {new_state.value}")
            
           
            if new_state != current_state:
                try:
                    if new_state == ConversationState.WAITING_FOR_SONG:
                        DatabaseManager.update_session(user_phone, new_state, name=user_message)
                    elif new_state == ConversationState.COMPLETED:
                        DatabaseManager.update_session(user_phone, new_state, song=user_message)
                    else:
                        DatabaseManager.update_session(user_phone, new_state)
                except Error as e:
                    logger.error(f"Database error updating session: {e}")
                    return jsonify({
                        "user_phone": user_phone,
                        "bot_message": "Failed to save your progress"
                    }), 500

            
            logger.info(f"Successfully processed message for {user_phone}")
            return jsonify({
                "user_phone": user_phone,
                "bot_message": response
            })

        except ValueError as e:
           
            logger.error(f"Invalid conversation state: {e}")
            return jsonify({
                "user_phone": user_phone,
                "bot_message": "Invalid conversation state"
            }), 500
            
        except Error as e:
            
            logger.error(f"Database error: {e}")
            return jsonify({
                "user_phone": user_phone,
                "bot_message": "Database error occurred"
            }), 500

    except Exception as e:
        
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        return jsonify({
            "user_phone": data.get("user_phone", "") if "data" in locals() else "",
            "bot_message": "An unexpected error occurred"
        }), 500
    
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "user_phone": "",
        "bot_message": "Resource not found"
    }), 404

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {error}")
    return jsonify({
        "user_phone": "",
        "bot_message": "An unexpected error occurred"
    }), 500

if __name__ == "__main__":
    try:
        init_db()
        logger.info("Starting Flask application")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        sys.exit(1)