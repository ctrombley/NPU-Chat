from flask import Blueprint, request

from jsonapi import (
    jsonapi_error_response,
    jsonapi_response,
    parse_request_data,
    serialize_collection,
    serialize_resource,
)
from services import ChatService

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
    attrs = parse_request_data(request)
    if attrs is None or 'name' not in attrs:
        return jsonapi_error_response(400, 'Bad Request', 'name is required')

    chat = ChatService.create_chat(attrs['name'])
    return jsonapi_response(
        serialize_resource('chats', chat.id, {
            'name': chat.name,
            'emoji': chat.emoji,
            'is_favorite': chat.is_favorite,
            'message_count': 0,
            'created_at': int(chat.created_at.timestamp() * 1000) if chat.created_at else None,
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
    responses:
      200:
        description: A list of chats
    """
    chats = ChatService.list_chats()
    items = [chat.to_dict() for chat in chats]
    return jsonapi_response(serialize_collection('chats', items))


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
    attrs = parse_request_data(request)
    if attrs is None:
        return jsonapi_error_response(400, 'Bad Request', 'Request body is required')

    chat = ChatService.update_chat(
        chat_id,
        attrs.get('name'),
        attrs.get('emoji'),
        attrs.get('template_id'),
        attrs.get('is_favorite'),
    )
    if not chat:
        return jsonapi_error_response(404, 'Not Found', 'Chat not found')

    return jsonapi_response(serialize_resource('chats', chat.id, {
        'name': chat.name,
        'emoji': chat.emoji,
        'template_id': chat.template_id,
        'is_favorite': chat.is_favorite,
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
    responses:
      200:
        description: A list of messages
      404:
        description: Chat not found
    """
    chat = ChatService.get_chat(chat_id)
    if not chat:
        return jsonapi_error_response(404, 'Not Found', 'Chat not found')

    messages = chat.messages
    items = []
    for msg in messages:
        items.append({
            'id': str(msg.id),
            'role': msg.role,
            'content': msg.content,
        })
    return jsonapi_response(serialize_collection('messages', items))
