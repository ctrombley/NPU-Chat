import json
import threading
import time

from flask import Blueprint, current_app, request

from jsonapi import (
    jsonapi_error_response,
    jsonapi_response,
    parse_request_data,
    serialize_resource,
)
from services import (
    ChatService,
    LLMService,
    NamingService,
    TemplateService,
    contains_chinese,
)

search_bp = Blueprint('search', __name__)

lock = threading.Lock()


@search_bp.route('/search', methods=['POST'])
def search():
    """Send a message and get a response.
    ---
    tags:
      - search
    consumes:
      - application/vnd.api+json
    produces:
      - application/vnd.api+json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                type:
                  type: string
                  example: search-requests
                attributes:
                  type: object
                  properties:
                    input_text:
                      type: string
                    session_id:
                      type: string
    responses:
      200:
        description: Search result
      400:
        description: Bad request
    """
    attrs = parse_request_data(request)
    if attrs is None:
        return jsonapi_error_response(400, 'Bad Request', 'Request body is required')

    session_id = attrs.get('session_id')
    question = attrs.get('input_text', '')

    # Input validation
    if not question.strip():
        return jsonapi_error_response(400, 'Bad Request', 'Empty input is not allowed.')

    if "'" in question or "--" in question or "DROP TABLE" in question.upper():
        return jsonapi_error_response(400, 'Bad Request', 'Invalid input detected.')

    result = web_request_logic(session_id, question)
    resp = jsonapi_response(
        serialize_resource('search-results', result['session_id'], {
            'content': result['content'],
            'session_id': result['session_id'],
        })
    )
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp


def web_request_logic(session_id, question):
    config = current_app.config

    # If no session_id or session doesn't exist, create a new server-side chat
    if not session_id:
        friendly_default_name = f"Chat {len(ChatService.list_chats()) + 1}"
        chat = ChatService.create_chat(friendly_default_name)
        chat.needs_naming = True
        from models import db
        db.session.commit()
        session_id = chat.id

    chat = ChatService.get_chat(session_id)
    if not chat:
        # Create if not exists
        friendly_default_name = f"Chat {len(ChatService.list_chats()) + 1}"
        chat = ChatService.create_chat(friendly_default_name)
        chat.needs_naming = True
        from models import db
        db.session.commit()
        session_id = chat.id

    # Start timing
    start_time = time.time()

    # Quick command handling
    cmd = question.strip().lower()

    def render_messages(msgs):
        out = ""
        for m in msgs:
            out += f"```\n{m}\n```\n"
        return out

    if cmd == 'context':
        messages = ChatService.get_chat_messages(session_id) or []
        context_history = render_messages(messages)
        answer = f"<md class='markdown-style'>{context_history}</md>"
        return {'content': answer, 'session_id': session_id}

    if cmd == 'clear':
        # Clear messages
        from models import Message
        Message.query.filter_by(chat_id=session_id).delete()
        from models import db
        db.session.commit()
        return {'content': "context cleared.", 'session_id': session_id}

    if cmd == 'off':
        from models import Message, db
        config['USE_CONTEXT'] = False
        Message.query.filter_by(chat_id=session_id).delete()
        db.session.commit()
        return {'content': "context off.", 'session_id': session_id}

    if cmd == 'on':
        config['USE_CONTEXT'] = True
        return {'content': "context on.", 'session_id': session_id}

    if cmd == 'sessions':
        chats = ChatService.list_chats()
        sessions = []
        for c in chats:
            sessions.append({'id': c.id, 'name': c.name, 'emoji': c.emoji, 'messages': len(c.messages)})
        return {'content': json.dumps({'sessions': sessions}, indent=2), 'session_id': session_id}

    if cmd.startswith('dump '):
        parts = cmd.split(maxsplit=1)
        if len(parts) == 2:
            dump_id = parts[1]
            msgs = ChatService.get_chat_messages(dump_id)
            if msgs is not None:
                return {'content': render_messages(msgs), 'session_id': session_id}
            else:
                return {'content': f'chat {dump_id} not found', 'session_id': session_id}

    if cmd == 'show_config':
        cfg = {
            'BINDING_ADDRESS': config['BINDING_ADDRESS'],
            'BINDING_PORT': config['BINDING_PORT'],
            'NPU_ADDRESS': config['NPU_ADDRESS'],
            'NPU_PORT': config['NPU_PORT'],
            'CONNECTION_TIMEOUT': config['CONNECTION_TIMEOUT'],
            'USE_CONTEXT': config['USE_CONTEXT'],
            'CONTEXT_DEPTH': config['CONTEXT_DEPTH'],
            'IGNORE_CHINESE': config['IGNORE_CHINESE'],
            'UI_THEME': config['UI_THEME']
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

    # Get template
    templates = TemplateService.load_templates()
    template = templates.get(chat.template_id, templates['default'])

    if lock.locked():
        return {'result': "Sorry, I can only handle one request at a time and I'm currently busy.", 'session_id': session_id}

    with lock:
        # Add user message
        chat.add_message(f"User: {question}")

        # Prepare context
        messages = ChatService.get_chat_messages(session_id) or []
        query = question
        if config['USE_CONTEXT'] and len(messages) > 1:
            # Prepend history, but skip the current user message if it's the last one
            history_msgs = messages[:-1]
            llm_output_history = ""
            for llm_reply in history_msgs:
                llm_output_history = f"{llm_output_history}```\n{llm_reply}\n```\n"
            query = llm_output_history + question

        raw_answer = LLMService.feed_the_llama(query, template['prefix'], template['postfix'])

        ignore_chinese_chars = False
        if config['IGNORE_CHINESE']:
            ignore_chinese_chars = contains_chinese(raw_answer)

        if not ignore_chinese_chars:
            chat.add_message(f"Assistant: {raw_answer}")

        # Naming
        print(f"DEBUG search: chat.needs_naming={chat.needs_naming}, chat.name={chat.name}")
        if chat.needs_naming:
            NamingService.generate_name(chat)

        answer = f"<md class='markdown-style'>{raw_answer}</md>"

        end_time = time.time()
        print(f"Completed in {end_time - start_time:.2f} seconds.")

        return {'content': answer, 'session_id': session_id}
