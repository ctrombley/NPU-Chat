import configparser
import os
import re
import requests
import threading
import time
import logging
import json
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify
from requests.exceptions import Timeout

# Load settings from settings.ini

def load_config(script_dir: str) -> None:
    """
    Loads user settings from settings.ini into globals
    """
    if script_dir and script_dir[-1] != '/':
        script_dir = script_dir + "/"

    config_path = f"{script_dir}settings.ini"
    parser = configparser.ConfigParser()
    _ = parser.read(config_path)

    global BINDING_ADDRESS
    global BINDING_PORT
    global NPU_ADDRESS
    global NPU_PORT
    global CONNECTION_TIMEOUT
    global use_chat_context
    global CONTEXT_DEPTH
    global ignore_chinese
    global UI_THEME

    BINDING_ADDRESS = parser.get('chat_ui', 'BINDING_ADDRESS')
    BINDING_PORT = int(parser.get('chat_ui', 'BINDING_PORT'))
    NPU_ADDRESS = parser.get('npu', 'NPU_ADDRESS')
    NPU_PORT = parser.get('npu', 'NPU_PORT')
    CONNECTION_TIMEOUT = int(parser.get('timeout', 'TIMEOUT'))

    use_chat_context = parser.getboolean('context', 'USE_CONTEXT', fallback=False)
    raw_context_depth = int(parser.get('context', 'DEPTH'))
    CONTEXT_DEPTH = max(2, raw_context_depth)
    if raw_context_depth < 2:
        logging.debug(f"CONTEXT_DEPTH was {raw_context_depth}, increased to {CONTEXT_DEPTH} to retain both user and assistant messages.")

    ignore_chinese = parser.getboolean('context', 'IGNORE_CHINESE', fallback=False)

    UI_THEME = parser.get('theme', 'THEME')


# Load configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
load_config(script_dir)

# Directory for persisting chat metadata + messages
DATA_DIR = os.path.join(script_dir, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# SQLite DB path
DB_PATH = os.path.join(DATA_DIR, 'chats.db')

# Templates file
TEMPLATES_PATH = os.path.join(DATA_DIR, 'templates.json')

# Contexts store multiple chat sessions; keys are chat ids and values are Chat objects
contexts: Dict[str, 'Chat'] = {}
# Backwards-compatible alias expected by tests
CONTEXTS = contexts
# Current in-memory context for the active request
current_context: List[str] = []
# Keep legacy alias (some earlier code uses 'context')
context = current_context

# Prompt templates: Dict[id, {'id': str, 'name': str, 'prefix': str, 'postfix': str}]
templates: Dict[str, Dict[str, str]] = {}

# A lock to guard concurrent requests — define at module level so routes can use it
lock = threading.Lock()

chat_id_counter = 0  # simple global counter


@dataclass
class Chat:
    """Represents a chat session with metadata and messages"""
    id: str
    name: str
    emoji: str = ''
    template_id: str = 'default'
    needs_naming: bool = False
    messages: List[str] = field(default_factory=list)
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> Dict[str, Any]:
        display_name = f"{self.emoji} {self.name}".strip() if self.emoji else self.name
        return {
            'id': self.id,
            'name': display_name,
            'emoji': self.emoji,
            'message_count': len(self.messages),
            'created_at': self.created_at
        }

    def add_message(self, message: str) -> None:
        # Add a message and trim to context depth
        self.messages.append(message)
        if len(self.messages) > CONTEXT_DEPTH:
            self.messages.pop(0)


APPNAME = 'NPU Chat'
VERSION = '0.27'


def contains_chinese(text: str) -> bool:
    pattern = r'[一-鿿]+'
    return bool(re.search(pattern, text))


# --- SQLite helpers -----------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize the SQLite database with required tables."""
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                name TEXT,
                emoji TEXT DEFAULT '',
                template_id TEXT DEFAULT 'default',
                needs_naming INTEGER DEFAULT 0,
                created_at INTEGER
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                content TEXT,
                position INTEGER,
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
        ''')
        conn.commit()
    except Exception:
        logging.exception("Failed to initialize database")
    finally:
        conn.close()


def save_templates() -> None:
    """Save templates to JSON file."""
    global templates
    try:
        with open(TEMPLATES_PATH, 'w') as f:
            json.dump(templates, f, indent=2)
    except Exception:
        logging.exception("Failed to save templates")

def load_templates() -> None:
    """Load templates from JSON file, or create default if none exists."""
    global templates
    if os.path.exists(TEMPLATES_PATH):
        try:
            with open(TEMPLATES_PATH, 'r') as f:
                templates = json.load(f)
        except Exception:
            logging.exception("Failed to load templates, using default")
            templates = {}
    else:
        # Create default template
        templates['default'] = {
            'id': 'default',
            'name': 'Default',
            'prefix': "<|im_start|>system You are a helpful assistant. <|im_end|> <|im_start|>user ",
            'postfix': " <|im_end|><|im_start|>assistant "
        }
        save_templates()


def save_chat_to_disk(chat_id: str) -> None:
    """Persist a chat (metadata + messages) to SQLite database."""
    if chat_id not in contexts:
        return
    chat = contexts[chat_id]
    try:
        init_db()
        conn = get_db_connection()
        cur = conn.cursor()
        if isinstance(chat, Chat):
            cur.execute(
                "INSERT OR REPLACE INTO chats (id, name, emoji, template_id, needs_naming, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (chat.id, chat.name, chat.emoji, chat.template_id, 1 if chat.needs_naming else 0, chat.created_at)
            )
            # Replace messages: delete existing and insert current list
            cur.execute("DELETE FROM messages WHERE chat_id = ?", (chat.id,))
            for idx, msg in enumerate(chat.messages):
                cur.execute(
                    "INSERT INTO messages (chat_id, content, position) VALUES (?, ?, ?)",
                    (chat.id, msg, idx)
                )
        else:
            # legacy format: chat is a list of messages
            cur.execute(
                "INSERT OR REPLACE INTO chats (id, name, emoji, needs_naming, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, f'Chat {chat_id}', '', 0, int(time.time() * 1000))
            )
            cur.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            for idx, msg in enumerate(chat):
                cur.execute(
                    "INSERT INTO messages (chat_id, content, position) VALUES (?, ?, ?)",
                    (chat_id, msg, idx)
                )
        conn.commit()
    except Exception:
        logging.exception(f"Failed to save chat {chat_id} to SQLite")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def load_chats_from_disk() -> None:
    """Load any persisted chats from SQLite into the in-memory contexts dict."""
    try:
        init_db()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, emoji, template_id, needs_naming, created_at FROM chats")
        rows = cur.fetchall()
        for row in rows:
            chat_id = row['id']
            name = row['name'] or f'Chat {len(contexts) + 1}'
            emoji = row['emoji'] or ''
            needs_naming = bool(row['needs_naming'])
            created_at = row['created_at'] or int(time.time() * 1000)

            # Load messages
            cur.execute("SELECT content FROM messages WHERE chat_id = ? ORDER BY position", (chat_id,))
            msg_rows = cur.fetchall()
            messages = [r['content'] for r in msg_rows]

            template_id = row['template_id'] if row['template_id'] else 'default'
            chat = Chat(chat_id, name, emoji=emoji, template_id=template_id, needs_naming=needs_naming, messages=messages, created_at=created_at)
            contexts[chat_id] = chat
    except Exception:
        logging.exception("Failed to load chats from SQLite")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def feed_the_llama(query: str, prefix: str, postfix: str) -> str:
    """Send the user's query to the NPU server and return the text content.

    When using chat context, we prepend recent messages to the query. However, web_request_logic
    appends the current user's message to the chat history before calling this function. To avoid
    duplicating that current user message in the prepended history, drop a trailing "User: ..."
    entry from the history if it exactly matches the current query.
    """
    global current_context

    if use_chat_context:
        if current_context:
            # Work on a copy so we don't mutate the shared in-memory list
            history_msgs = list(current_context)

            # If the last history entry is the current user's message (e.g. "User: {query}"),
            # remove it from the prepended history because the query itself will be sent separately.
            try:
                if history_msgs:
                    last = history_msgs[-1]
                    if isinstance(last, str) and last.strip().startswith('User:'):
                        # Extract the text after 'User:' and compare to the current query
                        candidate = last.split(':', 1)[1].strip() if ':' in last else last.strip()
                        if candidate == query.strip():
                            history_msgs = history_msgs[:-1]
            except Exception:
                # Be conservative: if anything goes wrong, fall back to using the full history
                history_msgs = list(current_context)

            llm_output_history = ""
            for llm_reply in history_msgs:
                llm_output_history = f"{llm_output_history}```\n{llm_reply}\n```\n"

            query = llm_output_history + query

    json_data = {
        'PROMPT_TEXT_PREFIX': prefix,
        'input_str': str(query) + ' ',
        'PROMPT_TEXT_POSTFIX': postfix,
    }

    headers = {
        'Content-Type': 'application/json',
    }

    try:
        resp = requests.post(
            f"http://{NPU_ADDRESS}:{NPU_PORT}",
            headers=headers,
            json=json_data,
            timeout=CONNECTION_TIMEOUT
        )

        resp.raise_for_status()
        resp_json: Dict[str, Any] = resp.json()
        answer = resp_json.get('content', '')
        return answer

    except Timeout:
        return "Request timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        error_msg = f"An error occurred: {str(e)} ---- is the server online?"
        return error_msg


def create_app() -> Flask:
    """Create and configure the Flask application."""
    print(f"Starting server at: http://{BINDING_ADDRESS}:{BINDING_PORT}")
    app = Flask(__name__)

    # Load persisted chats into memory at app startup
    load_chats_from_disk()

    # Load persisted templates
    load_templates()

    @app.route('/', methods=['GET', 'POST'])
    def index():
        # Serve the React app
        return app.send_static_file('dist/index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        # Serve static files from the React build
        if path.startswith('dist/') or '.' in path:
            return app.send_static_file(path)
        # For any other route, serve the React app (SPA routing)
        return app.send_static_file('dist/index.html')

    @app.route('/chats', methods=['POST'])
    def create_chat():
        """Create a new chat session (explicitly created by the user)."""
        global contexts
        global chat_id_counter

        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'name is required'}), 400

        chat_name = data['name']
        chat_id_counter += 1
        chat_id = f"chat-{chat_id_counter}"

        chat = Chat(chat_id, chat_name, needs_naming=False)
        contexts[chat_id] = chat

        # Persist to DB
        save_chat_to_disk(chat_id)

        return jsonify({
            'chat_id': chat_id,
            'name': chat_name,
            'created_at': chat.created_at
        }), 201

    @app.route('/chats', methods=['GET'])
    def list_chats():
        global contexts
        chats: List[Dict[str, Any]] = []
        for chat_id, chat in contexts.items():
            if isinstance(chat, Chat):
                chats.append(chat.to_dict())
            else:
                chat_name = f"Chat {len(chats) + 1}"
                created_at = int(chat_id.split('-')[1]) if '-' in chat_id and chat_id.split('-')[1].isdigit() else int(time.time() * 1000)
                chats.append({
                    'id': chat_id,
                    'name': chat_name,
                    'emoji': '',
                    'message_count': len(chat),
                    'created_at': created_at
                })
        return jsonify(chats)

    @app.route('/chats/<chat_id>', methods=['PUT'])
    def update_chat(chat_id: str):
        global contexts
        if chat_id not in contexts:
            return jsonify({'error': 'Chat not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        chat = contexts[chat_id]
        if not isinstance(chat, Chat):
            return jsonify({'error': 'Cannot update metadata for legacy chat format'}), 400

        # Update name if provided
        if 'name' in data:
            chat.name = data['name']
        # Update emoji if provided
        if 'emoji' in data:
            chat.emoji = data['emoji']
        # Update template_id if provided
        if 'template_id' in data:
            chat.template_id = data['template_id']

        # At least one field must be provided
        if 'name' not in data and 'emoji' not in data and 'template_id' not in data:
            return jsonify({'error': 'At least one of name, emoji, or template_id must be provided'}), 400

        # Persist change
        save_chat_to_disk(chat_id)

        return jsonify({'id': chat_id, 'name': chat.name, 'emoji': chat.emoji, 'template_id': chat.template_id})

    @app.route('/chats/<chat_id>', methods=['DELETE'])
    def delete_chat(chat_id: str):
        global contexts
        if chat_id not in contexts:
            return jsonify({'error': 'Chat not found'}), 404
        del contexts[chat_id]

        # Remove persisted DB rows if present
        try:
            init_db()
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            cur.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            conn.commit()
        except Exception:
            logging.exception(f"Failed to delete chat {chat_id} from SQLite")
        finally:
            try:
                conn.close()
            except Exception:
                pass

        return jsonify({'message': f'Chat {chat_id} deleted'}), 200

    @app.route('/chats/<chat_id>/switch', methods=['POST'])
    def switch_chat(chat_id: str):
        global contexts
        global context
        global current_context

        if chat_id not in contexts:
            return jsonify({'error': 'Chat not found'}), 404

        chat = contexts[chat_id]
        if isinstance(chat, Chat):
            current_context = chat.messages
            context = current_context
        else:
            current_context = chat
            context = current_context

        return jsonify({'message': f'Switched to chat {chat_id}'})

    @app.route('/chats/<chat_id>/messages', methods=['GET'])
    def get_chat_messages(chat_id: str):
        global contexts
        if chat_id not in contexts:
            return jsonify({'error': 'Chat not found'}), 404
        chat = contexts[chat_id]
        messages = chat.messages if isinstance(chat, Chat) else chat
        return jsonify({'messages': messages})

    @app.route('/templates', methods=['GET'])
    def list_templates():
        global templates
        return jsonify(list(templates.values()))

    @app.route('/templates', methods=['POST'])
    def create_template():
        global templates
        data = request.get_json()
        if not data or 'name' not in data or 'prefix' not in data or 'postfix' not in data:
            return jsonify({'error': 'name, prefix, and postfix are required'}), 400

        template_id = f"template-{int(time.time() * 1000)}"
        template = {
            'id': template_id,
            'name': data['name'],
            'prefix': data['prefix'],
            'postfix': data['postfix']
        }
        templates[template_id] = template
        save_templates()
        return jsonify(template), 201

    @app.route('/templates/<template_id>', methods=['PUT'])
    def update_template(template_id: str):
        global templates
        if template_id not in templates:
            return jsonify({'error': 'Template not found'}), 404
        if template_id == 'default':
            return jsonify({'error': 'Cannot update default template'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        template = templates[template_id]
        if 'name' in data:
            template['name'] = data['name']
        if 'prefix' in data:
            template['prefix'] = data['prefix']
        if 'postfix' in data:
            template['postfix'] = data['postfix']

        save_templates()
        return jsonify(template)

    @app.route('/templates/<template_id>', methods=['DELETE'])
    def delete_template(template_id: str):
        global templates
        if template_id not in templates:
            return jsonify({'error': 'Template not found'}), 404
        if template_id == 'default':
            return jsonify({'error': 'Cannot delete default template'}), 400

        del templates[template_id]
        save_templates()
        return jsonify({'message': f'Template {template_id} deleted'}), 200

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

    def web_request_logic(session_id: Optional[str], question: str) -> Dict[str, Any]:
        global use_chat_context
        global contexts
        global current_context

        # If no session_id or session doesn't exist, create a new server-side chat
        if not session_id or session_id not in contexts:
            new_session_id = f"chat-{int(time.time() * 1000)}"
            friendly_default_name = f"Chat {len(contexts) + 1}"
            chat = Chat(new_session_id, friendly_default_name, needs_naming=True)
            contexts[new_session_id] = chat
            # Persist initial chat metadata
            save_chat_to_disk(new_session_id)
            session_id = new_session_id

        # set the module-level current_context to point at this chat's messages list
        chat = contexts[session_id]
        if isinstance(chat, Chat):
            current_context = chat.messages
        else:
            current_context = chat

        # start timing
        start_time = time.time()

        # quick command handling
        cmd = question.strip().lower()

        # Helper to render messages list as markdown blocks
        def render_messages(msgs: List[str]) -> str:
            out = ""
            for m in msgs:
                out += f"```\n{m}\n```\n"
            return out

        if cmd == 'context':
            if isinstance(chat, Chat):
                current_context = chat.messages
            else:
                current_context = chat

            context_history = render_messages(current_context)
            answer = f"<md class='markdown-style'>{context_history}</md>"
            return {'content': answer, 'session_id': session_id}

        if cmd == 'clear':
            if isinstance(chat, Chat):
                chat.messages = []
                current_context = chat.messages
                save_chat_to_disk(session_id)
            else:
                if isinstance(current_context, list):
                    current_context.clear()
                else:
                    current_context = []
            return {'content': "context cleared.", 'session_id': session_id}

        if cmd == 'off':
            use_chat_context = False
            if isinstance(chat, Chat):
                chat.messages = []
                current_context = chat.messages
                save_chat_to_disk(session_id)
            else:
                if isinstance(current_context, list):
                    current_context.clear()
                else:
                    current_context = []
            return {'content': "context off.", 'session_id': session_id}

        if cmd == 'on':
            use_chat_context = True
            return {'content': "context on.", 'session_id': session_id}

        if cmd == 'sessions':
            sessions = []
            for sid, s in contexts.items():
                if isinstance(s, Chat):
                    sessions.append({'id': sid, 'name': s.name, 'emoji': s.emoji, 'messages': len(s.messages)})
                else:
                    sessions.append({'id': sid, 'name': str(sid), 'emoji': '', 'messages': len(s)})
            return {'content': json.dumps({'sessions': sessions}, indent=2), 'session_id': session_id}

        if cmd.startswith('dump '):
            parts = cmd.split(maxsplit=1)
            if len(parts) == 2:
                dump_id = parts[1]
                if dump_id in contexts:
                    target = contexts[dump_id]
                    msgs = target.messages if isinstance(target, Chat) else target
                    return {'content': render_messages(msgs), 'session_id': session_id}
                else:
                    return {'content': f'chat {dump_id} not found', 'session_id': session_id}

        if cmd == 'show_config':
            cfg = {
                'BINDING_ADDRESS': BINDING_ADDRESS,
                'BINDING_PORT': BINDING_PORT,
                'NPU_ADDRESS': NPU_ADDRESS,
                'NPU_PORT': NPU_PORT,
                'CONNECTION_TIMEOUT': CONNECTION_TIMEOUT,
                'use_chat_context': use_chat_context,
                'CONTEXT_DEPTH': CONTEXT_DEPTH,
                'ignore_chinese': ignore_chinese,
                'UI_THEME': UI_THEME
            }
            return {'content': json.dumps(cfg, indent=2), 'session_id': session_id}

        if cmd == 'help':
            help_text = (
                "Available quick commands:\n"
                "- context: show current chat context messages\n"
                "- clear: clear current chat context\n"
                "- on / off: enable or disable use of chat context for LLM calls\n"
                "- sessions: list existing server sessions\n"
                "- dump <chat_id>: show messages for a session\n"
                "- show_config: display server config values\n"
                "- help: show this message\n"
            )
            return {'content': help_text, 'session_id': session_id}

        # Get template for the chat
        if isinstance(chat, Chat):
            template_id = chat.template_id
            template = templates.get(template_id)
            if template:
                prefix = template['prefix']
                postfix = template['postfix']
            else:
                prefix = templates['default']['prefix']
                postfix = templates['default']['postfix']
        else:
            # legacy, use default
            prefix = templates['default']['prefix']
            postfix = templates['default']['postfix']

        if lock.locked():
            return {'result': "Sorry, I can only handle one request at a time and I'm currently busy.", 'session_id': session_id}

        with lock:
            if isinstance(chat, Chat):
                chat.add_message(f"User: {question}")
                save_chat_to_disk(session_id)
            else:
                current_context.append(f"User: {question}")

            raw_answer = feed_the_llama(question, prefix, postfix)

        ignore_chinese_chars = False
        if ignore_chinese:
            ignore_chinese_chars = contains_chinese(raw_answer)

        if not ignore_chinese_chars:
            if isinstance(chat, Chat):
                chat.add_message(f"Assistant: {raw_answer}")
                save_chat_to_disk(session_id)
            else:
                current_context.append(f"Assistant: {raw_answer}")

        try:
            if isinstance(chat, Chat) and chat.needs_naming:
                naming_prompt = (
                    "Please provide a very short (1-3 words) descriptive name for the conversation we just had, "
                    "and a single emoji that summarizes it. Respond ONLY with a JSON object like: {\"name\": \"...\", \"emoji\": \"...\"}."
                )

                with lock:
                    naming_response = feed_the_llama(naming_prompt, templates['default']['prefix'], templates['default']['postfix'])

                parsed: Optional[Dict[str, Any]] = None
                try:
                    parsed = json.loads(naming_response)
                except Exception:
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
                        chat.name = name
                        chat.emoji = emoji
                    chat.needs_naming = False
                    save_chat_to_disk(session_id)
        except Exception:
            pass

        answer = f"<md class='markdown-style'>{raw_answer}</md>"

        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds.")

        return {'content': answer, 'session_id': session_id}

    return app


def web_server() -> None:
    print(f"Starting server at: http://{BINDING_ADDRESS}:{BINDING_PORT}")
    app = create_app()
    app.run(host=BINDING_ADDRESS, port=BINDING_PORT, debug=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')
    logging.debug("Starting web server...")
    web_server()
