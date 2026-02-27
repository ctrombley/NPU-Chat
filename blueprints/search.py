import logging
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
)

search_bp = Blueprint('search', __name__)

lock = threading.Lock()
logger = logging.getLogger(__name__)


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

    if not question.strip():
        return jsonapi_error_response(400, 'Bad Request', 'Empty input is not allowed.')

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

    if not session_id:
        friendly_default_name = f"Chat {len(ChatService.list_chats()) + 1}"
        chat = ChatService.create_chat(friendly_default_name)
        chat.needs_naming = True
        from models import db
        db.session.commit()
        session_id = chat.id

    chat = ChatService.get_chat(session_id)
    if not chat:
        friendly_default_name = f"Chat {len(ChatService.list_chats()) + 1}"
        chat = ChatService.create_chat(friendly_default_name)
        chat.needs_naming = True
        from models import db
        db.session.commit()
        session_id = chat.id

    start_time = time.time()

    # Quick commands
    cmd = question.strip().lower()

    if cmd == 'context':
        messages = ChatService.get_chat_messages(session_id) or []
        context_history = ""
        for m in messages:
            context_history += f"```\n{m}\n```\n"
        return {'content': context_history, 'session_id': session_id}

    if cmd == 'clear':
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

    if cmd == 'help':
        help_text = (
            "Available quick commands:\n"
            "- context: show current chat context messages\n"
            "- clear: clear current chat context\n"
            "- on / off: enable or disable use of chat context for LLM calls\n"
            "- help: show this message\n"
        )
        return {'content': help_text, 'session_id': session_id}

    # Get template
    templates = TemplateService.load_templates()
    template = templates.get(chat.template_id, templates['default'])

    if lock.locked():
        return {'content': "Sorry, I can only handle one request at a time and I'm currently busy.", 'session_id': session_id}

    with lock:
        chat.add_message(f"User: {question}")

        messages = ChatService.get_chat_messages(session_id) or []
        query = question
        if config['USE_CONTEXT'] and len(messages) > 1:
            history_msgs = messages[:-1]
            llm_output_history = ""
            for llm_reply in history_msgs:
                llm_output_history = f"{llm_output_history}```\n{llm_reply}\n```\n"
            query = llm_output_history + question

        raw_answer = LLMService.feed_the_llama(query, template['prefix'], template['postfix'])

        chat.add_message(f"Assistant: {raw_answer}")

        if chat.needs_naming:
            NamingService.generate_name(chat)

        elapsed = time.time() - start_time
        logger.info("Search completed in %.2f seconds", elapsed)

        return {'content': raw_answer, 'session_id': session_id}
