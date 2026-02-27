from flask import jsonify, make_response


def serialize_resource(type_, id_, attributes):
    """Serialize a single resource into JSON:API format."""
    return {"data": {"type": type_, "id": str(id_), "attributes": attributes}}


def serialize_collection(type_, items):
    """Serialize a list of resources into JSON:API format.

    Each item should be a dict with at least an 'id' key.
    The remaining keys become attributes.
    """
    data = []
    for item in items:
        item_copy = dict(item)
        item_id = str(item_copy.pop("id"))
        data.append({"type": type_, "id": item_id, "attributes": item_copy})
    return {"data": data}


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


def jsonapi_response(body, status=200):
    """Create a Flask response with JSON:API content type."""
    resp = make_response(jsonify(body) if isinstance(body, dict) else body, status)
    resp.headers["Content-Type"] = "application/vnd.api+json"
    return resp


def jsonapi_error_response(status, title, detail=None):
    """Create an error response in JSON:API format."""
    return jsonapi_response(serialize_error(status, title, detail), status)
