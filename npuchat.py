import configparser
import os
import re
import requests
import threading
import time
import logging
from flask import Flask, render_template, request, jsonify
from requests.exceptions import Timeout

def load_config(script_dir: str) -> None:
    """
    Loads user settings from settings.ini into globals

    Args:
        script_dir (str): The working directory of this script.

    Returns:
        None
    """

    # if script path doesn't have trailing slash
    if script_dir[-1] != '/':
        script_dir = script_dir + "/"  # add it

    # get current working directory of this script to find settings.ini
    config_path = f"{script_dir}settings.ini"

    # parse settings.ini
    parser = configparser.ConfigParser()
    parser.read(config_path)

    # globals for settings
    global BINDING_ADDRESS
    global BINDING_PORT
    global NPU_ADDRESS
    global NPU_PORT
    global CONNECTION_TIMEOUT
    global USE_CHAT_CONTEXT
    global CONTEXT_DEPTH
    global IGNORE_CHINESE
    global UI_THEME

    # assign settings. str unless noted otherwise
    BINDING_ADDRESS = parser.get('chat_ui', 'BINDING_ADDRESS')
    BINDING_PORT = int(parser.get('chat_ui', 'BINDING_PORT'))
    NPU_ADDRESS = parser.get('npu', 'NPU_ADDRESS')
    NPU_PORT = parser.get('npu', 'NPU_PORT')
    CONNECTION_TIMEOUT = int(
        parser.get('timeout', 'TIMEOUT')
    )  # int

    USE_CHAT_CONTEXT = parser.get('context', 'USE_CONTEXT')  # bool
    CONTEXT_DEPTH = int(
        parser.get('context', 'DEPTH')
    )  # int
    IGNORE_CHINESE = parser.get('context', 'IGNORE_CHINESE')  # bool

    UI_THEME = parser.get('theme', 'THEME')

# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
load_config(script_dir)

# context / chat history
context = []
CONTEXTS = {}  # Dictionary to store multiple chat contexts with full metadata

chat_id_counter = 0  # Global counter for unique chat IDs

class Chat:
    """Represents a chat session with metadata and messages"""
    def __init__(self, chat_id, name):
        self.id = chat_id
        self.name = name
        self.messages = []  # List of message strings (for context window)
        self.created_at = int(time.time() * 1000)  # timestamp in milliseconds

    def to_dict(self):
        """Convert chat to dictionary representation"""
        return {
            'id': self.id,
            'name': self.name,
            'message_count': len(self.messages),
            'created_at': self.created_at
        }

    def add_message(self, message):
        """Add a message to the chat"""
        self.messages.append(message)

        # Trim context to desired depth by removing oldest element
        if len(self.messages) > CONTEXT_DEPTH:
            self.messages.pop(0)

APPNAME = 'NPU Chat'
VERSION = '0.27'


def contains_chinese(text: str) -> bool:
    """
    Detect if a string contains Chinese characters.

    Args:
        text (str): The input string to check.

    Returns:
        bool: True if the string contains Chinese characters, False otherwise.
    """
    pattern = r'[一-鿿]+'
    if re.search(pattern, text):
        return True
    else:
        return False

def feed_the_llama(query: str) -> str:
    """
    Send the user's query to the NPU server and modify it if context is being
    used.

    Args:
        query (str): The user's input string.

    Returns:
        str: Answer from the LLM.
    """

    if USE_CHAT_CONTEXT:
        if CONTEXT:  # if context history isn't empty
            # compile the history into individual codeblocks
            llm_output_history = ""
            for llm_reply in CONTEXT:  # format into markdown codeblocks
                llm_output_history = (
                    f"{llm_output_history}"
                    f"```\n"
                    f"{llm_reply}"
                    f"\n```\n"
                )
            query = llm_output_history + query  # append user's query

    # prompt template:
    prefix = (
        "<|im_start|>system You are a helpful assistant. <|im_end|> "
        "<|im_start|>user "
    )

    postfix = (
        "<|im_end|><|im_start|>assistant "
    )

    # create the request object
    json_data = {
        'PROMPT_TEXT_PREFIX': prefix,
        'input_str': str(query) + ' ',
        'PROMPT_TEXT_POSTFIX': postfix,
    }

    headers = {
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(
            f"http://{NPU_ADDRESS}:{NPU_PORT}",
            headers=headers,
            json=json_data,
            timeout=CONNECTION_TIMEOUT
        )

        response.raise_for_status()  # throw exception on non 2xx HTTP statuses

        response = response.json()  # get JSON from response

        answer = response['content']  # text of the LLM's response

        return answer  # return text to client

    # handle errors for better user-friendliness
    except Timeout:
        return "Request timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        error_msg = (
            f"An error occurred: {str(e)}"
            f" ---- is the server online?"
        )
        return error_msg

def create_app():
    """
    Sets up the Flask server and handles web requests.
    """

    # print the server details to the console
    print(
        f"Starting server at: "
        f"http://{BINDING_ADDRESS}:{BINDING_PORT}"
    )
    app = Flask(__name__)
    app.name = f"{APPNAME} v{VERSION}"

    # serve the UI to the user
    @app.route('/', methods=['GET', 'POST'])
    def index():
        response = app.make_response(
            render_template('index.html', selected_theme=UI_THEME)
        )
        response.headers['Pragma'] = 'no-cache'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    # Chat management endpoints
    @app.route('/chats', methods=['POST'])
    def create_chat():
        """Create a new chat session"""
        global CONTEXTS
        global chat_id_counter

        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'name is required'}), 400

        chat_name = data['name']
        chat_id_counter += 1
        chat_id = f"chat-{chat_id_counter}"

        # Create new Chat object
        chat = Chat(chat_id, chat_name)
        CONTEXTS[chat_id] = chat

        return jsonify({
            'chat_id': chat_id,
            'name': chat_name,
            'created_at': chat.created_at
        }), 201

    @app.route('/chats', methods=['GET'])
    def list_chats():
        """List all chat sessions"""
        global CONTEXTS

        chats = []
        for chat_id, chat in CONTEXTS.items():
            if isinstance(chat, Chat):
                chats.append(chat.to_dict())
            else:
                # Handle legacy format (list of messages)
                chat_name = f"Chat {len(chats) + 1}"
                created_at = int(chat_id.split('-')[1]) if '-' in chat_id and chat_id.split('-')[1].isdigit() else int(time.time() * 1000)
                chats.append({
                    'id': chat_id,
                    'name': chat_name,
                    'message_count': len(chat),
                    'created_at': created_at
                })

        return jsonify(chats)

    @app.route('/chats/<chat_id>', methods=['PUT'])
    def update_chat(chat_id):
        """Update a chat's name"""
        global CONTEXTS

        if chat_id not in CONTEXTS:
            return jsonify({'error': 'Chat not found'}), 404

        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'name is required'}), 400

        new_name = data['name']
        chat = CONTEXTS[chat_id]

        if isinstance(chat, Chat):
            chat.name = new_name
        else:
            # For legacy format, we can't update the name
            return jsonify({'error': 'Cannot update name for legacy chat format'}), 400

        return jsonify({
            'id': chat_id,
            'name': new_name
        })

    @app.route('/chats/<chat_id>', methods=['DELETE'])
    def delete_chat(chat_id):
        """Delete a chat"""
        global CONTEXTS

        if chat_id not in CONTEXTS:
            return jsonify({'error': 'Chat not found'}), 404

        del CONTEXTS[chat_id]
        return jsonify({'message': f'Chat {chat_id} deleted'}), 200

    @app.route('/chats/<chat_id>/switch', methods=['POST'])
    def switch_chat(chat_id):
        """Switch to a specific chat session"""
        global CONTEXTS
        global context

        if chat_id not in CONTEXTS:
            return jsonify({'error': 'Chat not found'}), 404

        chat = CONTEXTS[chat_id]
        if isinstance(chat, Chat):
            context = chat.messages  # Use the chat's message list
        else:
            context = chat  # Legacy format (list of messages)

        return jsonify({'message': f'Switched to chat {chat_id}'})

    @app.route('/chats/<chat_id>/messages', methods=['GET'])
    def get_chat_messages(chat_id):
        """Get messages for a specific chat"""
        global CONTEXTS

        if chat_id not in CONTEXTS:
            return jsonify({'error': 'Chat not found'}), 404

        chat = CONTEXTS[chat_id]
        if isinstance(chat, Chat):
            messages = chat.messages
        else:
            messages = chat  # Legacy format (list of messages)

        return jsonify({'messages': messages})

    # endpoint (http://your-ip/search)
    @app.route('/search', methods=['POST'])
    def web_request():
        session_id = request.args.get('session_id')
        question = request.form['input_text']

        # Debug logging
        print(f"Debug: Received session ID: {session_id}")
        print(f"Debug: Received question: {question}")

        # Input validation
        if not question.strip():
            print("Debug: Empty input detected.")
            return jsonify({'content': 'Empty input is not allowed.'}), 400

        if "'" in question or "--" in question or "DROP TABLE" in question.upper():
            print("Debug: SQL injection detected.")
            return jsonify({'content': 'Invalid input detected.'}), 400

        response = app.make_response(jsonify(web_request_logic(session_id, question)))
        response.headers['Pragma'] = 'no-cache'
        response.headers['Cache-Control'] = (
            'no-cache, no-store, must-revalidate'
        )
        return response

    def web_request_logic(session_id, question):
        global USE_CHAT_CONTEXT
        global CONTEXTS
        global CONTEXT

        # retrieve session ID from request
        print(f"Validating input: '{question}'")
        if not session_id or session_id not in CONTEXTS:
            return {'content': 'Invalid or missing session ID.'}

        # fetch or initialize the current context
        print("Input validation passed.")
        CONTEXT = CONTEXTS[session_id]

        # start recording response time
        import logging

        # Debug logging: Entering function and checking session state/log status
        logging.debug("Entering 'web_request_logic' function.")
        logging.debug(f"Session state or lock status before execution. Context size: {len(CONTEXT)}")
        start_time = time.time()

        # commands for manipulating context state
        if question.lower() == 'context':  # show current context
            context_history = ""
            for llm_reply in CONTEXT:  # format into markdown codeblocks
                context_history = (
                    f"```\n"
                    f"{llm_reply}"
                    f"\n```\n"
                )
            answer = (
                f"<md class='markdown-style'>"
                f"{context_history}"
                f"</md>"
            )
            return {'content': answer}
        if question.lower() == 'clear':  # erase context
            CONTEXT = []  # initialize the context list
            return {'content': "context cleared."}
        if question.lower() == 'off':  # turn it off
            CONTEXT = []  # initialize the context list
            USE_CHAT_CONTEXT = False
            return {'content': "context off."}
        if question.lower() == 'on':  # turn it on
            USE_CHAT_CONTEXT = True
            return {'content': "context on."}

        print(f"━━━━━━━━┫ Received request: {question}")

        # if lock is acquired then this app is currently in use.
        # we can currently only handle one request at a time.
        if lock.locked():
            error_msg = "Sorry, I can only handle one request at a time and I'm currently busy."
            return {
                'result': error_msg
            }

        # if this app is free to process a request
        with lock:
            answer = feed_the_llama(question)  # send to npu server

        # update chat context
        if USE_CHAT_CONTEXT:

            ignore_chinese_chars = False

            # check if user wants to ignore Chinese characters
            if IGNORE_CHINESE:
                ignore_chinese_chars = contains_chinese(answer)

            # update context history
            if not ignore_chinese_chars:
                CONTEXT.append(answer)

                # trim context to desired depth by removing oldest element
                if len(CONTEXT) > CONTEXT_DEPTH:
                    CONTEXT.pop(0)

        # modify the answer for markdown HTML tag to make it pretty
        answer = (
            f"<md class='markdown-style'>"
            f"{answer}"
            f"</md>"
        )

        # print completed time
        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds.")

        # return answer to client
        answer_markdown = {'content': answer}
        return answer_markdown

    return app

def web_server() -> None:
    """
    Starts the Flask server.
    """

    # print the server details to the console
    print(
        f"Starting server at: "
        f"http://{BINDING_ADDRESS}:{BINDING_PORT}"
    )

    app = create_app()
    app.run(
        host=BINDING_ADDRESS,
        port=BINDING_PORT,
        debug=True
    )

if __name__ == "__main__":

    # control access since currently only one instance can run at a time
    lock = threading.Lock()

    # start Flask
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

    logging.debug("Starting web server...")
    web_server()
