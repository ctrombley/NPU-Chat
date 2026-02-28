import json
import logging
import time

from flask import Blueprint, Response, current_app, request

from extensions import limiter
from jsonapi import (
    jsonapi_error_response,
    jsonapi_response,
    serialize_resource,
    validate_jsonapi_request,
)
from models import Message, db
from schemas import SearchRequest
from services import (
    ChatService,
    LLMService,
    TemplateService,
)

search_bp = Blueprint('search', __name__)

logger = logging.getLogger(__name__)


@search_bp.route('/search', methods=['POST'])
@limiter.limit("10 per minute")
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
    data, error = validate_jsonapi_request(request, SearchRequest)
    if error:
        return error

    question = data.input_text
    if not question.strip():
        return jsonapi_error_response(400, 'Bad Request', 'Empty input is not allowed.')

    result = web_request_logic(data.session_id, question)
    resp = jsonapi_response(
        serialize_resource('search-results', result['session_id'], {
            'content': result['content'],
            'session_id': result['session_id'],
        })
    )
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp


@search_bp.route('/search/stream', methods=['POST'])
@limiter.limit("10 per minute")
def search_stream():
    """Send a message and stream the response via SSE."""
    data, error = validate_jsonapi_request(request, SearchRequest)
    if error:
        return error

    question = data.input_text
    if not question.strip():
        return jsonapi_error_response(400, 'Bad Request', 'Empty input is not allowed.')

    session_id = data.session_id
    config = current_app.config
    context_depth = config['CONTEXT_DEPTH']

    if not session_id:
        chat = ChatService.create_chat("New Chat")
        session_id = chat.id

    chat = ChatService.get_chat(session_id)
    if not chat:
        chat = ChatService.create_chat("New Chat")
        session_id = chat.id

    # Quick commands — return as a single SSE event, not streamed
    cmd = question.strip().lower()
    quick_commands = {
        'context': lambda: _context_response(session_id),
        'clear': lambda: _clear_response(session_id),
        'off': lambda: _off_response(session_id),
        'on': lambda: _on_response(),
        'help': lambda: _help_response(),
    }
    if cmd in quick_commands:
        content = quick_commands[cmd]()
        def single_event():
            yield f"data: {json.dumps({'session_id': session_id, 'chunk': content})}\n\n"
            yield f"data: {json.dumps({'session_id': session_id, 'done': True})}\n\n"
        return Response(single_event(), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    # Get template
    template = TemplateService.get_template(chat.template_id)
    if not template:
        template = TemplateService.get_template('default')

    chat.add_message('user', question)

    messages = ChatService.get_chat_messages(session_id) or []
    query = question
    if config['USE_CONTEXT'] and len(messages) > 1:
        history_msgs = messages[-context_depth * 2:-1] if context_depth else messages[:-1]
        llm_output_history = ""
        for msg in history_msgs:
            llm_output_history += f"```\n{msg.content}\n```\n"
        query = llm_output_history + question

    # We need to capture these for the generator closure
    chat_id = chat.id
    prefix = template.prefix
    postfix = template.postfix

    # Capture app and stream eagerly (while still in app context)
    # since the generator will be iterated outside it during streaming.
    app = current_app._get_current_object()
    stream = LLMService.feed_the_llama_stream(query, prefix, postfix)

    def generate():
        full_response = []
        for chunk in stream:
            full_response.append(chunk)
            yield f"data: {json.dumps({'session_id': chat_id, 'chunk': chunk})}\n\n"

        # Save the complete response and signal done.
        # Note: chat metadata (name/emoji) is updated via the separate shadow
        # POST /chats/{id}/review-metadata request fired by the frontend.
        complete_text = ''.join(full_response)
        with app.app_context():
            c = ChatService.get_chat(chat_id)
            if c:
                c.add_message('assistant', complete_text)

        yield f"data: {json.dumps({'session_id': chat_id, 'done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


def _context_response(session_id):
    messages = ChatService.get_chat_messages(session_id) or []
    return "".join(f"```\n[{m.role}] {m.content}\n```\n" for m in messages)

def _clear_response(session_id):
    Message.query.filter_by(chat_id=session_id).delete()
    db.session.commit()
    return "context cleared."

def _off_response(session_id):
    Message.query.filter_by(chat_id=session_id).delete()
    db.session.commit()
    return "context off. Note: context toggle is a server-wide setting via settings.ini."

def _on_response():
    return "context on. Note: context toggle is a server-wide setting via settings.ini."

def _help_response():
    return (
        "Available quick commands:\n"
        "- context: show current chat context messages\n"
        "- clear: clear current chat context\n"
        "- on / off: enable or disable use of chat context for LLM calls\n"
        "- help: show this message\n"
    )


def web_request_logic(session_id, question):
    config = current_app.config
    context_depth = config['CONTEXT_DEPTH']

    if not session_id:
        chat = ChatService.create_chat("New Chat")
        session_id = chat.id

    chat = ChatService.get_chat(session_id)
    if not chat:
        chat = ChatService.create_chat("New Chat")
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

    chat.add_message('user', question)

    messages = ChatService.get_chat_messages(session_id) or []
    query = question
    if config['USE_CONTEXT'] and len(messages) > 1:
        history_msgs = messages[-context_depth * 2:-1] if context_depth else messages[:-1]
        llm_output_history = ""
        for msg in history_msgs:
            llm_output_history += f"```\n{msg.content}\n```\n"
        query = llm_output_history + question

    raw_answer = LLMService.feed_the_llama(query, template.prefix, template.postfix)

    chat.add_message('assistant', raw_answer)

    elapsed = time.time() - start_time
    logger.info("Search completed in %.2f seconds", elapsed)

    return {'content': raw_answer, 'session_id': session_id}
