import logging
import time

from flask import Blueprint, current_app, request

from jsonapi import (
    jsonapi_error_response,
    jsonapi_response,
    parse_request_data,
    serialize_resource,
)
from models import Message, db
from services import (
    ChatService,
    LLMService,
    NamingService,
    TemplateService,
)

search_bp = Blueprint('search', __name__)

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
    context_depth = config['CONTEXT_DEPTH']

    if not session_id:
        chat = ChatService.create_chat("New Chat")
        chat.needs_naming = True
        db.session.commit()
        session_id = chat.id

    chat = ChatService.get_chat(session_id)
    if not chat:
        chat = ChatService.create_chat("New Chat")
        chat.needs_naming = True
        db.session.commit()
        session_id = chat.id

    start_time = time.time()

    # Quick commands
    cmd = question.strip().lower()

    if cmd == 'context':
        messages = ChatService.get_chat_messages(session_id) or []
        context_history = ""
        for m in messages:
            context_history += f"```\n[{m.role}] {m.content}\n```\n"
        return {'content': context_history, 'session_id': session_id}

    if cmd == 'clear':
        Message.query.filter_by(chat_id=session_id).delete()
        db.session.commit()
        return {'content': "context cleared.", 'session_id': session_id}

    if cmd == 'off':
        Message.query.filter_by(chat_id=session_id).delete()
        db.session.commit()
        return {'content': "context off. Note: context toggle is a server-wide setting via settings.ini.", 'session_id': session_id}

    if cmd == 'on':
        return {'content': "context on. Note: context toggle is a server-wide setting via settings.ini.", 'session_id': session_id}

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
    template = TemplateService.get_template(chat.template_id)
    if not template:
        template = TemplateService.get_template('default')

    chat.add_message('user', question, context_depth)

    messages = ChatService.get_chat_messages(session_id) or []
    query = question
    if config['USE_CONTEXT'] and len(messages) > 1:
        history_msgs = messages[:-1]
        llm_output_history = ""
        for msg in history_msgs:
            llm_output_history += f"```\n{msg.content}\n```\n"
        query = llm_output_history + question

    raw_answer = LLMService.feed_the_llama(query, template.prefix, template.postfix)

    chat.add_message('assistant', raw_answer, context_depth)

    if chat.needs_naming:
        NamingService.generate_name(chat)

    elapsed = time.time() - start_time
    logger.info("Search completed in %.2f seconds", elapsed)

    return {'content': raw_answer, 'session_id': session_id}
