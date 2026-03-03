"""Tests for chat metadata review via the review-metadata endpoint."""
import json
from unittest.mock import patch

from conftest import JSONAPI_CONTENT_TYPE, get_jsonapi_id, jsonapi_post

from models import Chat, Sign, db


class MockLLMResp:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception('HTTP error')

    def json(self):
        return self._json

    def iter_lines(self):
        content = self._json.get('choices', [{}])[0].get('message', {}).get('content', '')
        yield f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}".encode('utf-8')
        yield b"data: [DONE]"


def _is_metadata_call(req_json):
    """Identify a metadata review call by its system prompt content."""
    messages = (req_json or {}).get('messages', [])
    return any('metadata assistant' in m.get('content', '') for m in messages if m.get('role') == 'system')


def make_llm_mock(metadata_response, normal_response='LLM normal reply'):
    """Build a requests.post side-effect that returns metadata_response for metadata
    prompts (identified by the metadata assistant system prompt) and normal_response otherwise."""
    metadata_content = json.dumps(metadata_response)

    def side_effect(url, headers=None, json=None, timeout=None, stream=False):
        if _is_metadata_call(json):
            return MockLLMResp({'choices': [{'message': {'content': metadata_content}}]})
        return MockLLMResp({'choices': [{'message': {'content': normal_response}}]})

    return side_effect


def test_review_metadata_endpoint_updates_name_and_emoji(client):
    """POST /api/v1/chats/{id}/review-metadata calls LLM and updates name/emoji in DB."""
    resp = jsonapi_post(client, '/api/v1/chats', 'chats', {})
    assert resp.status_code == 201
    chat_id = get_jsonapi_id(resp)

    with patch('requests.post', side_effect=make_llm_mock({'name': 'Python Help', 'emoji': '\U0001f40d', 'theme': 'Python debugging'})):
        response = client.post(
            f'/api/v1/chats/{chat_id}/review-metadata',
            data=json.dumps({'user_message': 'How do I fix this Python bug?'}),
            content_type='application/json',
        )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert body['data']['attributes']['name'] == 'Python Help'
    assert body['data']['attributes']['emoji'] == '\U0001f40d'

    with client.application.app_context():
        chat = db.session.get(Chat, chat_id)
        assert chat.name == 'Python Help'
        assert chat.emoji == '\U0001f40d'


def test_review_metadata_endpoint_uses_user_message_from_body(client):
    """POST body user_message is passed to LLM, not DB messages."""
    resp = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Chat 1'})
    chat_id = get_jsonapi_id(resp)

    captured_queries = []

    def capture_side_effect(url, headers=None, json=None, timeout=None, stream=False):
        if _is_metadata_call(json):
            user_content = next((m.get('content', '') for m in (json or {}).get('messages', []) if m.get('role') == 'user'), '')
            captured_queries.append(user_content)
            return MockLLMResp({'choices': [{'message': {'content': '{"name": "JS Help", "emoji": "\U0001f7e8", "theme": "JavaScript questions"}'}}]})
        return MockLLMResp({'choices': [{'message': {'content': 'reply'}}]})

    with patch('requests.post', side_effect=capture_side_effect):
        client.post(
            f'/api/v1/chats/{chat_id}/review-metadata',
            data=json.dumps({'user_message': 'What is a JavaScript closure?'}),
            content_type='application/json',
        )

    assert len(captured_queries) == 1
    assert 'What is a JavaScript closure?' in captured_queries[0]


def test_review_metadata_endpoint_not_found(client):
    """POST to review-metadata for non-existent chat returns 404."""
    response = client.post(
        '/api/v1/chats/does-not-exist/review-metadata',
        data=json.dumps({}),
        content_type='application/json',
    )
    assert response.status_code == 404


def test_review_metadata_returns_existing_data_when_review_disabled(client):
    """When METADATA_REVIEW_ENABLED is False, endpoint returns current chat data without calling LLM."""
    resp = jsonapi_post(client, '/api/v1/chats', 'chats', {'name': 'Original'})
    chat_id = get_jsonapi_id(resp)

    client.application.config['METADATA_REVIEW_ENABLED'] = False
    try:
        call_count = 0

        def should_not_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return MockLLMResp({'content': '{}'})

        with patch('requests.post', side_effect=should_not_call):
            response = client.post(
                f'/api/v1/chats/{chat_id}/review-metadata',
                data=json.dumps({'user_message': 'hello'}),
                content_type='application/json',
            )

        assert response.status_code == 200
        body = json.loads(response.data)
        assert body['data']['attributes']['name'] == 'Original'
        assert call_count == 0
    finally:
        client.application.config['METADATA_REVIEW_ENABLED'] = True


def test_search_stream_does_not_call_metadata_review(client):
    """Streaming endpoint no longer performs metadata review itself."""
    resp = jsonapi_post(client, '/api/v1/chats', 'chats', {})
    chat_id = get_jsonapi_id(resp)

    metadata_call_count = 0

    def track_calls(url, headers=None, json=None, timeout=None, stream=False):
        nonlocal metadata_call_count
        if _is_metadata_call(json):
            metadata_call_count += 1
            return MockLLMResp({'choices': [{'message': {'content': '{}'}}]})
        return MockLLMResp({'choices': [{'message': {'content': 'stream reply'}}]})

    with patch('requests.post', side_effect=track_calls):
        response = client.post(
            '/api/v1/search/stream',
            data=json.dumps({'data': {'type': 'search-requests', 'attributes': {
                'input_text': 'Hello stream',
                'session_id': chat_id,
            }}}),
            content_type=JSONAPI_CONTENT_TYPE,
        )
        assert response.status_code == 200
        response.get_data(as_text=True)

    assert metadata_call_count == 0, (
        'search/stream should not call metadata review; '
        'the frontend fires that separately'
    )


def test_review_metadata_clamps_chart_values(client):
    """Chart values returned by LLM are clamped to the aspect schema min/max."""
    with client.application.app_context():
        sign = Sign(
            id='test-sign',
            name='Test Sign',
            prefix='<|im_start|>system test <|im_end|> <|im_start|>user ',
            postfix=' <|im_end|><|im_start|>assistant ',
        )
        sign.aspects = json.dumps({
            'trust': {'description': 'Trust level', 'initial': 0.5, 'min': 0, 'max': 1},
            'curiosity': {'description': 'Curiosity', 'initial': 0.3, 'min': 0, 'max': 1},
        })
        sign.default_goal = 'Build rapport'
        db.session.add(sign)
        db.session.commit()

    resp = jsonapi_post(client, '/api/v1/chats', 'chats', {'sign_id': 'test-sign'})
    assert resp.status_code == 201
    chat_id = get_jsonapi_id(resp)
    body = json.loads(resp.data)
    assert body['data']['attributes']['goal'] == 'Build rapport'
    chart = body['data']['attributes']['metadata'].get('chart', {})
    assert chart['trust'] == 0.5
    assert chart['curiosity'] == 0.3

    # LLM returns out-of-range values — they should be clamped
    llm_response = {
        'name': 'Trust Test',
        'emoji': '\U0001f91d',
        'theme': 'Testing trust',
        'chart': {'trust': 1.5, 'curiosity': -0.2},
        'goal': 'Establish deep trust',
    }

    with patch('requests.post', side_effect=make_llm_mock(llm_response)):
        response = client.post(
            f'/api/v1/chats/{chat_id}/review-metadata',
            data=json.dumps({'user_message': 'I trust you completely'}),
            content_type='application/json',
        )

    assert response.status_code == 200
    body = json.loads(response.data)
    attrs = body['data']['attributes']
    assert attrs['name'] == 'Trust Test'
    assert attrs['goal'] == 'Establish deep trust'
    chart = attrs['metadata']['chart']
    assert chart['trust'] == 1.0  # clamped from 1.5
    assert chart['curiosity'] == 0.0  # clamped from -0.2
