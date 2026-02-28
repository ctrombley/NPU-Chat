from flask import jsonify, make_response
from pydantic import ValidationError


def serialize_resource(type_, id_, attributes):
    """Serialize a single resource into JSON:API format."""
    return {"data": {"type": type_, "id": str(id_), "attributes": attributes}}


def serialize_collection(type_, items, meta=None):
    """Serialize a list of resources into JSON:API format.

    Each item should be a dict with at least an 'id' key.
    The remaining keys become attributes.
    """
    data = []
    for item in items:
        item_copy = dict(item)
        item_id = str(item_copy.pop("id"))
        data.append({"type": type_, "id": item_id, "attributes": item_copy})
    result = {"data": data}
    if meta:
        result["meta"] = meta
    return result


def serialize_error(status, title, detail=None):
    """Serialize an error into JSON:API format."""
    error = {"status": str(status), "title": title}
    if detail:
        error["detail"] = detail
    return {"errors": [error]}


def parse_request_data(req):
    """Extract attributes from a JSON:API request body.

    Expects: {"data": {"type": "...", "attributes": {...}}}
    Returns the attributes dict, or None if the body is malformed.
    """
    body = req.get_json(silent=True)
    if not body or "data" not in body:
        return None
    data = body["data"]
    return data.get("attributes", {})


def validate_jsonapi_request(req, schema_class):
    """Parse JSON:API body and validate with a Pydantic schema.

    Returns (validated_data, None) on success, or (None, error_response) on failure.
    """
    attrs = parse_request_data(req)
    if attrs is None:
        return None, jsonapi_error_response(400, 'Bad Request', 'Request body is required')
    try:
        validated = schema_class(**attrs)
        return validated, None
    except ValidationError as e:
        detail = '; '.join(
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in e.errors()
        )
        return None, jsonapi_error_response(400, 'Bad Request', detail)


def paginate_query(query, req, default_page_size=50, max_page_size=100):
    """Paginate a SQLAlchemy query using request parameters.

    Query params: page[number] (default 1), page[size] (default 50, max 100)
    Returns (items, meta_dict).
    """
    try:
        page = int(req.args.get('page[number]', 1))
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = min(int(req.args.get('page[size]', default_page_size)), max_page_size)
    except (ValueError, TypeError):
        per_page = default_page_size

    page = max(1, page)
    per_page = max(1, per_page)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }
    return pagination.items, meta


def jsonapi_response(body, status=200):
    """Create a Flask response with JSON:API content type."""
    resp = make_response(jsonify(body) if isinstance(body, dict) else body, status)
    resp.headers["Content-Type"] = "application/vnd.api+json"
    return resp


def jsonapi_error_response(status, title, detail=None):
    """Create an error response in JSON:API format."""
    return jsonapi_response(serialize_error(status, title, detail), status)
