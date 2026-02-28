from flask import Blueprint, current_app, request

from jsonapi import (
    jsonapi_error_response,
    jsonapi_response,
    paginate_query,
    serialize_collection,
    serialize_resource,
    validate_jsonapi_request,
)
from models import Chat, Message
from schemas import CreateChatRequest, UpdateChatRequest
from services import ChatService, LLMService

chats_bp = Blueprint('chats', __name__)


@chats_bp.route('/chats', methods=['POST'])
def create_chat():
    """Create a new chat.
    ---
    tags:
      - chats
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
                  example: chats
                attributes:
                  type: object
                  properties:
                    name:
                      type: string
                      example: My Chat
    responses:
      201:
        description: Chat created
      400:
        description: Bad request
    """
    data, error = validate_jsonapi_request(request, CreateChatRequest)
    if error:
        return error

    chat = ChatService.create_chat(data.name if data.name else None, template_id=data.template_id)
    return jsonapi_response(
        serialize_resource('chats', chat.id, {
            'name': chat.name,
            'emoji': chat.emoji,
            'template_id': chat.template_id,
            'is_favorite': chat.is_favorite,
            'message_count': 0,
            'created_at': int(chat.created_at.timestamp() * 1000) if chat.created_at else None,
            'metadata': chat.chat_metadata or {},
        }),
        201,
    )


@chats_bp.route('/chats', methods=['GET'])
def list_chats():
    """List all chats.
    ---
    tags:
      - chats
    produces:
      - application/vnd.api+json
    parameters:
      - in: query
        name: page[number]
        type: integer
        default: 1
      - in: query
        name: page[size]
        type: integer
        default: 50
    responses:
      200:
        description: A list of chats
    """
    query = Chat.query.order_by(Chat.created_at)
    chats, meta = paginate_query(query, request)
    items = [chat.to_dict() for chat in chats]
    return jsonapi_response(serialize_collection('chats', items, meta=meta))


@chats_bp.route('/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get a single chat.
    ---
    tags:
      - chats
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: chat_id
        type: string
        required: true
    responses:
      200:
        description: Chat found
      404:
        description: Chat not found
    """
    chat = ChatService.get_chat(chat_id)
    if not chat:
        return jsonapi_error_response(404, 'Not Found', 'Chat not found')

    d = chat.to_dict()
    chat_id_val = d.pop('id')
    return jsonapi_response(serialize_resource('chats', chat_id_val, d))


@chats_bp.route('/chats/<chat_id>', methods=['PATCH'])
def update_chat(chat_id):
    """Update a chat.
    ---
    tags:
      - chats
    consumes:
      - application/vnd.api+json
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: chat_id
        type: string
        required: true
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
                  example: chats
                id:
                  type: string
                attributes:
                  type: object
                  properties:
                    name:
                      type: string
                    emoji:
                      type: string
                    is_favorite:
                      type: boolean
    responses:
      200:
        description: Chat updated
      400:
        description: Bad request
      404:
        description: Chat not found
    """
    data, error = validate_jsonapi_request(request, UpdateChatRequest)
    if error:
        return error

    chat = ChatService.update_chat(
        chat_id,
        data.name,
        data.emoji,
        data.template_id,
        data.is_favorite,
        data.metadata,
    )
    if not chat:
        return jsonapi_error_response(404, 'Not Found', 'Chat not found')

    return jsonapi_response(serialize_resource('chats', chat.id, {
        'name': chat.name,
        'emoji': chat.emoji,
        'template_id': chat.template_id,
        'is_favorite': chat.is_favorite,
        'metadata': chat.chat_metadata or {},
    }))


@chats_bp.route('/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat.
    ---
    tags:
      - chats
    parameters:
      - in: path
        name: chat_id
        type: string
        required: true
    responses:
      204:
        description: Chat deleted
      404:
        description: Chat not found
    """
    if not ChatService.delete_chat(chat_id):
        return jsonapi_error_response(404, 'Not Found', 'Chat not found')
    return '', 204


@chats_bp.route('/chats/<chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    """Get messages for a chat.
    ---
    tags:
      - chats
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: chat_id
        type: string
        required: true
      - in: query
        name: page[number]
        type: integer
        default: 1
      - in: query
        name: page[size]
        type: integer
        default: 50
    responses:
      200:
        description: A list of messages
      404:
        description: Chat not found
    """
    chat = ChatService.get_chat(chat_id)
    if not chat:
        return jsonapi_error_response(404, 'Not Found', 'Chat not found')

    query = Message.query.filter_by(chat_id=chat_id).order_by(Message.position)
    messages, meta = paginate_query(query, request)
    items = []
    for msg in messages:
        items.append({
            'id': str(msg.id),
            'role': msg.role,
            'content': msg.content,
        })
    return jsonapi_response(serialize_collection('messages', items, meta=meta))


@chats_bp.route('/chats/<chat_id>/review-metadata', methods=['POST'])
def review_chat_metadata(chat_id):
    """Trigger LLM metadata review for a chat and return updated chat data.
    ---
    tags:
      - chats
    parameters:
      - in: path
        name: chat_id
        type: string
        required: true
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            user_message:
              type: string
              description: The new user message to use as context for review
    responses:
      200:
        description: Updated chat data
      404:
        description: Chat not found
    """
    chat = ChatService.get_chat(chat_id)
    if not chat:
        return jsonapi_error_response(404, 'Not Found', 'Chat not found')

    if current_app.config.get('METADATA_REVIEW_ENABLED', True):
        body = request.get_json(force=True, silent=True) or {}
        user_message = body.get('user_message') if isinstance(body, dict) else None
        LLMService.review_chat_metadata(chat, user_message=user_message)

    d = chat.to_dict()
    chat_id_val = d.pop('id')
    return jsonapi_response(serialize_resource('chats', chat_id_val, d))
