from flask import Blueprint, request

from jsonapi import (
    jsonapi_error_response,
    jsonapi_response,
    parse_request_data,
    serialize_collection,
    serialize_resource,
)
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
    responses:
      200:
        description: A list of templates
    """
    templates = TemplateService.load_templates()
    items = list(templates.values())
    return jsonapi_response(serialize_collection('templates', items))


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
    attrs = parse_request_data(request)
    if attrs is None or not all(k in attrs for k in ('name', 'prefix', 'postfix')):
        return jsonapi_error_response(400, 'Bad Request', 'name, prefix, and postfix are required')

    template = TemplateService.create_template(attrs['name'], attrs['prefix'], attrs['postfix'])
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
    from models import Template as TemplateModel
    from models import db
    template = db.session.get(TemplateModel, template_id)
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
    attrs = parse_request_data(request)
    if attrs is None:
        return jsonapi_error_response(400, 'Bad Request', 'Request body is required')

    template = TemplateService.update_template(
        template_id,
        attrs.get('name'),
        attrs.get('prefix'),
        attrs.get('postfix'),
    )
    if not template:
        return jsonapi_error_response(404, 'Not Found', 'Template not found or cannot update default')

    return jsonapi_response(serialize_resource('templates', template.id, {
        'name': template.name,
        'prefix': template.prefix,
        'postfix': template.postfix,
    }))


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
