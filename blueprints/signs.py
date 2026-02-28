from flask import Blueprint, request

from jsonapi import (
    jsonapi_error_response,
    jsonapi_response,
    paginate_query,
    serialize_collection,
    serialize_resource,
    validate_jsonapi_request,
)
from models import Sign
from schemas import CreateSignRequest, UpdateSignRequest
from services import SignService

signs_bp = Blueprint('signs', __name__)


def _serialize_sign(sign):
    d = sign.to_dict()
    sign_id = d.pop('id')
    return serialize_resource('signs', sign_id, d)


@signs_bp.route('/signs', methods=['GET'])
def list_signs():
    """List all signs.
    ---
    tags:
      - signs
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
        description: A list of signs
    """
    query = Sign.query
    signs, meta = paginate_query(query, request)
    items = [s.to_dict() for s in signs]
    return jsonapi_response(serialize_collection('signs', items, meta=meta))


@signs_bp.route('/signs', methods=['POST'])
def create_sign():
    """Create a new sign.
    ---
    tags:
      - signs
    consumes:
      - application/vnd.api+json
    produces:
      - application/vnd.api+json
    responses:
      201:
        description: Sign created
      400:
        description: Bad request
    """
    data, error = validate_jsonapi_request(request, CreateSignRequest)
    if error:
        return error

    sign = SignService.create_sign(
        data.name, data.prefix, data.postfix,
        values=data.values, interests=data.interests,
        default_goal=data.default_goal, aspects=data.aspects,
    )
    return jsonapi_response(_serialize_sign(sign), 201)


@signs_bp.route('/signs/<sign_id>', methods=['GET'])
def get_sign(sign_id):
    """Get a single sign.
    ---
    tags:
      - signs
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: sign_id
        type: string
        required: true
    responses:
      200:
        description: Sign found
      404:
        description: Sign not found
    """
    sign = SignService.get_sign(sign_id)
    if not sign:
        return jsonapi_error_response(404, 'Not Found', 'Sign not found')

    return jsonapi_response(_serialize_sign(sign))


@signs_bp.route('/signs/<sign_id>', methods=['PATCH'])
def update_sign(sign_id):
    """Update a sign.
    ---
    tags:
      - signs
    consumes:
      - application/vnd.api+json
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: sign_id
        type: string
        required: true
    responses:
      200:
        description: Sign updated
      400:
        description: Bad request
      404:
        description: Sign not found
    """
    data, error = validate_jsonapi_request(request, UpdateSignRequest)
    if error:
        return error

    sign = SignService.update_sign(
        sign_id,
        data.name, data.prefix, data.postfix,
        values=data.values, interests=data.interests,
        default_goal=data.default_goal, aspects=data.aspects,
    )
    if not sign:
        return jsonapi_error_response(404, 'Not Found', 'Sign not found or cannot update default')

    return jsonapi_response(_serialize_sign(sign))


@signs_bp.route('/signs/<sign_id>/clone', methods=['POST'])
def clone_sign(sign_id):
    """Clone a sign.
    ---
    tags:
      - signs
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: sign_id
        type: string
        required: true
    responses:
      201:
        description: Sign cloned
      404:
        description: Sign not found
    """
    clone = SignService.clone_sign(sign_id)
    if not clone:
        return jsonapi_error_response(404, 'Not Found', 'Sign not found')

    return jsonapi_response(_serialize_sign(clone), 201)


@signs_bp.route('/signs/<sign_id>', methods=['DELETE'])
def delete_sign(sign_id):
    """Delete a sign.
    ---
    tags:
      - signs
    parameters:
      - in: path
        name: sign_id
        type: string
        required: true
    responses:
      204:
        description: Sign deleted
      404:
        description: Sign not found
    """
    if not SignService.delete_sign(sign_id):
        return jsonapi_error_response(404, 'Not Found', 'Sign not found or cannot delete default')
    return '', 204
