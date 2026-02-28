from flask import Blueprint, request

from jsonapi import (
    jsonapi_error_response,
    jsonapi_response,
    paginate_query,
    serialize_collection,
    serialize_resource,
    validate_jsonapi_request,
)
from models import Template
from schemas import CreateTemplateRequest, UpdateTemplateRequest
from services import TemplateService

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('/templates', methods=['GET'])
def list_templates():
    """List all templates.
    ---
    tags:
      - templates
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
        description: A list of templates
    """
    query = Template.query
    templates, meta = paginate_query(query, request)
    items = [t.to_dict() for t in templates]
    return jsonapi_response(serialize_collection('templates', items, meta=meta))


@templates_bp.route('/templates', methods=['POST'])
def create_template():
    """Create a new template.
    ---
    tags:
      - templates
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
                  example: templates
                attributes:
                  type: object
                  properties:
                    name:
                      type: string
                    prefix:
                      type: string
                    postfix:
                      type: string
    responses:
      201:
        description: Template created
      400:
        description: Bad request
    """
    data, error = validate_jsonapi_request(request, CreateTemplateRequest)
    if error:
        return error

    template = TemplateService.create_template(data.name, data.prefix, data.postfix)
    return jsonapi_response(
        serialize_resource('templates', template.id, {
            'name': template.name,
            'prefix': template.prefix,
            'postfix': template.postfix,
        }),
        201,
    )


@templates_bp.route('/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a single template.
    ---
    tags:
      - templates
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: template_id
        type: string
        required: true
    responses:
      200:
        description: Template found
      404:
        description: Template not found
    """
    template = TemplateService.get_template(template_id)
    if not template:
        return jsonapi_error_response(404, 'Not Found', 'Template not found')

    return jsonapi_response(serialize_resource('templates', template.id, {
        'name': template.name,
        'prefix': template.prefix,
        'postfix': template.postfix,
    }))


@templates_bp.route('/templates/<template_id>', methods=['PATCH'])
def update_template(template_id):
    """Update a template.
    ---
    tags:
      - templates
    consumes:
      - application/vnd.api+json
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: template_id
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
                  example: templates
                id:
                  type: string
                attributes:
                  type: object
                  properties:
                    name:
                      type: string
                    prefix:
                      type: string
                    postfix:
                      type: string
    responses:
      200:
        description: Template updated
      400:
        description: Bad request
      404:
        description: Template not found
    """
    data, error = validate_jsonapi_request(request, UpdateTemplateRequest)
    if error:
        return error

    template = TemplateService.update_template(
        template_id,
        data.name,
        data.prefix,
        data.postfix,
    )
    if not template:
        return jsonapi_error_response(404, 'Not Found', 'Template not found or cannot update default')

    return jsonapi_response(serialize_resource('templates', template.id, {
        'name': template.name,
        'prefix': template.prefix,
        'postfix': template.postfix,
    }))


@templates_bp.route('/templates/<template_id>/clone', methods=['POST'])
def clone_template(template_id):
    """Clone a template.
    ---
    tags:
      - templates
    produces:
      - application/vnd.api+json
    parameters:
      - in: path
        name: template_id
        type: string
        required: true
    responses:
      201:
        description: Template cloned
      404:
        description: Template not found
    """
    clone = TemplateService.clone_template(template_id)
    if not clone:
        return jsonapi_error_response(404, 'Not Found', 'Template not found')

    return jsonapi_response(
        serialize_resource('templates', clone.id, {
            'name': clone.name,
            'prefix': clone.prefix,
            'postfix': clone.postfix,
        }),
        201,
    )


@templates_bp.route('/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template.
    ---
    tags:
      - templates
    parameters:
      - in: path
        name: template_id
        type: string
        required: true
    responses:
      204:
        description: Template deleted
      404:
        description: Template not found
    """
    if not TemplateService.delete_template(template_id):
        return jsonapi_error_response(404, 'Not Found', 'Template not found or cannot delete default')
    return '', 204
