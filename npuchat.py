import configparser
import os
import re
import requests
import threading
import time
import logging
import json
from flask import Flask, render_template, request, jsonify
from requests.exceptions import Timeout

# Load settings from settings.ini

def load_config(script_dir: str) -> None:
    """
    Loads user settings from settings.ini into globals
    """
    if script_dir[-1] != '/':
        script_dir = script_dir + "/"

    config_path = f"{script_dir}settings.ini"
    parser = configparser.ConfigParser()
    parser.read(config_path)

    global BINDING_ADDRESS
    global BINDING_PORT
    global NPU_ADDRESS
    global NPU_PORT
    global CONNECTION_TIMEOUT
    global USE_CHAT_CONTEXT
    global CONTEXT_DEPTH
    global IGNORE_CHINESE
    global UI_THEME

    BINDING_ADDRESS = parser.get('chat_ui', 'BINDING_ADDRESS')
    BINDING_PORT = int(parser.get('chat_ui', 'BINDING_PORT'))
    NPU_ADDRESS = parser.get('npu', 'NPU_ADDRESS')
    NPU_PORT = parser.get('npu', 'NPU_PORT')
    CONNECTION_TIMEOUT = int(parser.get('timeout', 'TIMEOUT'))

    USE_CHAT_CONTEXT = parser.get('context', 'USE_CONTEXT')
    CONTEXT_DEPTH = int(parser.get('context', 'DEPTH'))
    IGNORE_CHINESE = parser.get('context', 'IGNORE_CHINESE')

    UI_THEME = parser.get('theme', 'THEME')

# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
load_config(script_dir)

# Contexts store multiple chat sessions; keys are chat ids and values are Chat objects
CONTEXTS = {}
# Current in-memory context for the active request
CONTEXT = []
# Keep legacy alias (some earlier code uses 'context')
context = CONTEXT

# A lock to guard concurrent requests — define at module level so routes can use it
lock = threading.Lock()

chat_id_counter = 0  # simple global counter

class Chat:
    """Represents a chat session with metadata and messages"""
    def __init__(self, chat_id, name, needs_naming=False):
        self.id = chat_id
        self.name = name
        self.messages = []
        self.created_at = int(time.time() * 1000)
        # Flag indicating whether the server should ask the LLM to suggest a nicer name/emoji
        self.needs_naming = needs_naming

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'message_count': len(self.messages),
            'created_at': self.created_at
        }

    def add_message(self, message):
        self.messages.append(message)
        # Trim to context depth
        if len(self.messages) > CONTEXT_DEPTH:
            self.messages.pop(0)


APPNAME = 'NPU Chat'
VERSION = '0.27'


def contains_chinese(text: str) -> bool:
    pattern = r'[一-鿿]+'
    return bool(re.search(pattern, text))


def feed_the_llama(query: str) -> str:
    """Send the user's query to the NPU server and return the text content."""
    # If context usage is enabled, prepend the recent context
    global CONTEXT

    if USE_CHAT_CONTEXT:
        if CONTEXT:
            llm_output_history = ""
            for llm_reply in CONTEXT:
                llm_output_history = f"{llm_output_history}```\n{llm_reply}\n```\n"
            query = llm_output_history + query

    prefix = (
        "<|im_start|>system You are a helpful assistant. <|im_end|> "
        "<|im_start|>user "
    )

    postfix = (
        "<|im_end|><|im_start|>assistant "
    )

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

        response.raise_for_status()
        response = response.json()
        answer = response.get('content', '')
        return answer

    except Timeout:
        return "Request timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        error_msg = f"An error occurred: {str(e)} ---- is the server online?"
        return error_msg


def create_app():
    """Create and configure the Flask application."""
    print(f"Starting server at: http://{BINDING_ADDRESS}:{BINDING_PORT}")
    # Flask.__init__ does not accept a 'name' keyword argument; use the module name only.
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        response = app.make_response(render_template('index.html', selected_theme=UI_THEME))
        response.headers['Pragma'] = 'no-cache'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    @app.route('/chats', methods=['POST'])
    def create_chat():
        """Create a new chat session (explicitly created by the user)."
        """
        global CONTEXTS
        global chat_id_counter

        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'name is required'}), 400

        chat_name = data['name']
        chat_id_counter += 1
        chat_id = f"chat-{chat_id_counter}"

        # User-created chats should not trigger auto-naming
        chat = Chat(chat_id, chat_name, needs_naming=False)
        CONTEXTS[chat_id] = chat

        return jsonify({
            'chat_id': chat_id,
            'name': chat_name,
            'created_at': chat.created_at
        }), 201

    @app.route('/chats', methods=['GET'])
    def list_chats():
        global CONTEXTS
        chats = []
        for chat_id, chat in CONTEXTS.items():
            if isinstance(chat, Chat):
                chats.append(chat.to_dict())
            else:
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
            return jsonify({'error': 'Cannot update name for legacy chat format'}), 400

        return jsonify({'id': chat_id, 'name': new_name})

    @app.route('/chats/<chat_id>', methods=['DELETE'])
    def delete_chat(chat_id):
        global CONTEXTS
        if chat_id not in CONTEXTS:
            return jsonify({'error': 'Chat not found'}), 404
        del CONTEXTS[chat_id]
        return jsonify({'message': f'Chat {chat_id} deleted'}), 200

    @app.route('/chats/<chat_id>/switch', methods=['POST'])
    def switch_chat(chat_id):
        global CONTEXTS
        global context
        global CONTEXT

        if chat_id not in CONTEXTS:
            return jsonify({'error': 'Chat not found'}), 404

        chat = CONTEXTS[chat_id]
        if isinstance(chat, Chat):
            CONTEXT = chat.messages
            context = CONTEXT
        else:
            CONTEXT = chat
            context = CONTEXT

        return jsonify({'message': f'Switched to chat {chat_id}'})

    @app.route('/chats/<chat_id>/messages', methods=['GET'])
    def get_chat_messages(chat_id):
        global CONTEXTS
        if chat_id not in CONTEXTS:
            return jsonify({'error': 'Chat not found'}), 404
        chat = CONTEXTS[chat_id]
        messages = chat.messages if isinstance(chat, Chat) else chat
        return jsonify({'messages': messages})

    @app.route('/search', methods=['POST'])
    def web_request():
        session_id = request.args.get('session_id')
        question = request.form.get('input_text', '')

        # Input validation
        if not question.strip():
            return jsonify({'content': 'Empty input is not allowed.'}), 400

        if "'" in question or "--" in question or "DROP TABLE" in question.upper():
            return jsonify({'content': 'Invalid input detected.'}), 400

        response = app.make_response(jsonify(web_request_logic(session_id, question)))
        response.headers['Pragma'] = 'no-cache'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    def web_request_logic(session_id, question):
        global USE_CHAT_CONTEXT
        global CONTEXTS
        global CONTEXT

        # If no session_id or session doesn't exist, create a new server-side chat
        if not session_id or session_id not in CONTEXTS:
            new_session_id = f"chat-{int(time.time() * 1000)}"
            # Create a Chat object and mark it for auto-naming
            friendly_default_name = f"Chat {len(CONTEXTS) + 1}"
            chat = Chat(new_session_id, friendly_default_name, needs_naming=True)
            CONTEXTS[new_session_id] = chat
            session_id = new_session_id

        # set the module-level CONTEXT to point at this chat's messages list
        chat = CONTEXTS[session_id]
        if isinstance(chat, Chat):
            CONTEXT = chat.messages
        else:
            CONTEXT = chat

        # start timing
        start_time = time.time()

        # quick command handling
        if question.lower() == 'context':
            context_history = ""
            for llm_reply in CONTEXT:
                context_history = f"```\n{llm_reply}\n```\n"
            answer = f"<md class='markdown-style'>{context_history}</md>"
            return {'content': answer}
        if question.lower() == 'clear':
            if isinstance(chat, Chat):
                chat.messages = []
            else:
                CONTEXT = []
            return {'content': "context cleared."}
        if question.lower() == 'off':
            if isinstance(chat, Chat):
                chat.messages = []
            CONTEXT = []
            return {'content': "context off."}
        if question.lower() == 'on':
            USE_CHAT_CONTEXT = True
            return {'content': "context on."}

        # concurrency guard
        if lock.locked():
            return {'result': "Sorry, I can only handle one request at a time and I'm currently busy."}

        with lock:
            answer = feed_the_llama(question)

        # Update chat context
        ignore_chinese_chars = False
        if IGNORE_CHINESE:
            ignore_chinese_chars = contains_chinese(answer)

        if not ignore_chinese_chars:
            # Save the raw answer string as part of the chat's messages
            if isinstance(chat, Chat):
                chat.add_message(answer)
            else:
                CONTEXT.append(answer)

        # After producing a response for a newly created chat, request a short name + emoji
        try:
            if isinstance(chat, Chat) and chat.needs_naming:
                # Ask the LLM to propose a concise title and single emoji for the chat
                naming_prompt = (
                    "Please provide a very short (1-3 words) descriptive name for the conversation we just had, "
                    "and a single emoji that summarizes it. Respond ONLY with a JSON object like: {\"name\": \"...\", \"emoji\": \"...\"}."
                )

                with lock:
                    naming_response = feed_the_llama(naming_prompt)

                # Try to parse JSON
                parsed = None
                try:
                    parsed = json.loads(naming_response)
                except Exception:
                    # If the response itself was wrapped (e.g. quoted JSON), try to extract a JSON substring
                    m = re.search(r"(\{.*\})", naming_response, re.DOTALL)
                    if m:
                        try:
                            parsed = json.loads(m.group(1))
                        except Exception:
                            parsed = None

                if isinstance(parsed, dict):
                    name = parsed.get('name', '').strip()
                    emoji = parsed.get('emoji', '').strip()
                    if name:
                        # Prepend emoji if present
                        if emoji:
                            chat.name = f"{emoji} {name}"
                        else:
                            chat.name = name
                    # Once named, don't ask again
                    chat.needs_naming = False
        except Exception:
            # Naming is best-effort — if anything fails, don't block the primary response
            pass

        # Wrap the LLM answer in markdown tag for client
        answer = f"<md class='markdown-style'>{answer}</md>"

        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds.")

        return {'content': answer}

    return app


def web_server() -> None:
    print(f"Starting server at: http://{BINDING_ADDRESS}:{BINDING_PORT}")
    app = create_app()
    app.run(host=BINDING_ADDRESS, port=BINDING_PORT, debug=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')
    logging.debug("Starting web server...")
    web_server()
