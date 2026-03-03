import json
import logging
import re
import threading
import uuid
from typing import Any, Dict, List, Optional

import requests
from flask import current_app
from requests.exceptions import Timeout
from sqlalchemy.orm.attributes import flag_modified

from models import Chat, Message, Sign, db

logger = logging.getLogger(__name__)


class ChatService:
    @staticmethod
    def _next_default_name() -> str:
        existing = db.session.query(Chat.name).filter(Chat.name.like('Chat %')).all()
        max_num = 0
        for (name,) in existing:
            parts = name.split(' ', 1)
            if len(parts) == 2 and parts[1].isdigit():
                max_num = max(max_num, int(parts[1]))
        return f"Chat {max_num + 1}"

    @staticmethod
    def create_chat(name: Optional[str] = None, sign_id: Optional[str] = None) -> Chat:
        if not name:
            name = ChatService._next_default_name()
        chat_id = str(uuid.uuid4())
        sid = sign_id or 'default'
        goal = None
        chart = None
        sign = db.session.get(Sign, sid)
        if sign:
            goal = sign.default_goal or None
            if sign.aspects:
                try:
                    aspects = json.loads(sign.aspects) if isinstance(sign.aspects, str) else sign.aspects
                    chart = {k: v.get('initial', 0.5) for k, v in aspects.items()}
                except (ValueError, TypeError, AttributeError):
                    pass
        metadata = {}
        if chart:
            metadata['chart'] = chart
        chat = Chat(id=chat_id, name=name, sign_id=sid, goal=goal, chat_metadata=metadata or None)
        db.session.add(chat)
        db.session.commit()
        return chat

    @staticmethod
    def get_chat(chat_id: str) -> Optional[Chat]:
        return db.session.get(Chat, chat_id)

    @staticmethod
    def update_chat(chat_id: str, name: Optional[str] = None, emoji: Optional[str] = None, sign_id: Optional[str] = None, is_favorite: Optional[bool] = None, metadata: Optional[Dict] = None, goal: Optional[str] = None) -> Optional[Chat]:
        chat = db.session.get(Chat, chat_id)
        if not chat:
            return None
        if name is not None:
            chat.name = name
        if emoji is not None:
            chat.emoji = emoji
        if sign_id is not None:
            chat.sign_id = sign_id
        if is_favorite is not None:
            chat.is_favorite = is_favorite
        if metadata is not None:
            existing = chat.chat_metadata or {}
            existing.update(metadata)
            chat.chat_metadata = existing
        if goal is not None:
            chat.goal = goal
        db.session.commit()
        return chat

    @staticmethod
    def delete_chat(chat_id: str) -> bool:
        chat = db.session.get(Chat, chat_id)
        if not chat:
            return False
        db.session.delete(chat)
        db.session.commit()
        return True

    @staticmethod
    def list_chats() -> List[Chat]:
        return Chat.query.order_by(Chat.created_at).all()

    @staticmethod
    def get_chat_messages(chat_id: str) -> Optional[List[Message]]:
        chat = db.session.get(Chat, chat_id)
        if not chat:
            return None
        return list(chat.messages)

class SignService:
    @staticmethod
    def list_signs() -> List[Sign]:
        return Sign.query.all()

    @staticmethod
    def ensure_default_sign() -> None:
        if not db.session.get(Sign, 'default'):
            default = Sign(
                id='default',
                name='Default',
                prefix="<|im_start|>system You are a helpful assistant. <|im_end|> <|im_start|>user ",
                postfix=" <|im_end|><|im_start|>assistant "
            )
            db.session.add(default)
            db.session.commit()

    @staticmethod
    def get_sign(sign_id: str) -> Optional[Sign]:
        return db.session.get(Sign, sign_id)

    @staticmethod
    def create_sign(name: str, prefix: str, postfix: str, values: Optional[str] = None, interests: Optional[str] = None, default_goal: Optional[str] = None, aspects: Optional[str] = None) -> Sign:
        sign_id = str(uuid.uuid4())
        sign = Sign(id=sign_id, name=name, prefix=prefix, postfix=postfix)
        sign.values = values
        sign.interests = interests
        sign.default_goal = default_goal
        sign.aspects = aspects
        db.session.add(sign)
        db.session.commit()
        return sign

    @staticmethod
    def update_sign(sign_id: str, name: Optional[str] = None, prefix: Optional[str] = None, postfix: Optional[str] = None, values: Optional[str] = None, interests: Optional[str] = None, default_goal: Optional[str] = None, aspects: Optional[str] = None) -> Optional[Sign]:
        sign = db.session.get(Sign, sign_id)
        if not sign or sign_id == 'default':
            return None
        if name is not None:
            sign.name = name
        if prefix is not None:
            sign.prefix = prefix
        if postfix is not None:
            sign.postfix = postfix
        if values is not None:
            sign.values = values
        if interests is not None:
            sign.interests = interests
        if default_goal is not None:
            sign.default_goal = default_goal
        if aspects is not None:
            sign.aspects = aspects
        db.session.commit()
        return sign

    @staticmethod
    def clone_sign(sign_id: str) -> Optional[Sign]:
        source = db.session.get(Sign, sign_id)
        if not source:
            return None
        new_id = str(uuid.uuid4())
        clone = Sign(id=new_id, name=f"Copy of {source.name}",
                     prefix=source.prefix, postfix=source.postfix)
        clone.values = source.values
        clone.interests = source.interests
        clone.default_goal = source.default_goal
        clone.aspects = source.aspects
        db.session.add(clone)
        db.session.commit()
        return clone

    @staticmethod
    def delete_sign(sign_id: str) -> bool:
        if sign_id == 'default':
            return False
        sign = db.session.get(Sign, sign_id)
        if not sign:
            return False
        db.session.delete(sign)
        db.session.commit()
        return True

class LLMService:
    # One lock per unique address:port. Two roles sharing a server share the lock.
    _locks: Dict[str, threading.Lock] = {}
    _locks_lock = threading.Lock()

    @staticmethod
    def _get_lock(address: str, port: int) -> threading.Lock:
        key = f"{address}:{port}"
        with LLMService._locks_lock:
            if key not in LLMService._locks:
                LLMService._locks[key] = threading.Lock()
            return LLMService._locks[key]

    @staticmethod
    def _get_model_config(role: str) -> Dict[str, Any]:
        config = current_app.config
        registry = config.get('MODEL_REGISTRY', {})
        if role in registry:
            entry = registry[role]
        elif 'chat' in registry:
            entry = registry['chat']
        else:
            entry = {
                'address': config['NPU_ADDRESS'],
                'port': int(config['NPU_PORT']),
                'timeout': config['CONNECTION_TIMEOUT'],
                'serialize': True,
                'model': config.get('NPU_MODEL', 'qwen3-4b'),
            }
        return {
            'address': entry.get('address', config['NPU_ADDRESS']),
            'port': int(entry.get('port', config['NPU_PORT'])),
            'timeout': int(entry.get('timeout', config['CONNECTION_TIMEOUT'])),
            'serialize': entry.get('serialize', True),
            'model': entry.get('model', config.get('NPU_MODEL', 'qwen3-4b')),
        }

    @staticmethod
    def _clean_prefix(prefix: str) -> str:
        """Strip Qwen2.5 chat template tokens from Sign.prefix to yield plain system prompt text."""
        text = re.sub(r'<\|im_start\|>system\s*', '', prefix)
        text = re.sub(r'\s*<\|im_end\|>.*', '', text, flags=re.DOTALL)
        return text.strip()

    @staticmethod
    def _build_request(messages: List[Dict[str, str]], model: str) -> Dict[str, Any]:
        return {'model': model, 'messages': messages}

    @staticmethod
    def feed_the_llama(messages: List[Dict[str, str]], role: str = 'chat') -> str:
        mc = LLMService._get_model_config(role)
        json_data = LLMService._build_request(messages, mc['model'])
        url = f"http://{mc['address']}:{mc['port']}/v1/chat/completions"
        headers = {'Content-Type': 'application/json'}
        lock = LLMService._get_lock(mc['address'], mc['port']) if mc['serialize'] else None

        def _do_request():
            try:
                resp = requests.post(url, headers=headers, json=json_data, timeout=mc['timeout'])
                resp.raise_for_status()
                try:
                    resp_json: Dict[str, Any] = resp.json()
                    answer = resp_json['choices'][0]['message']['content']
                except (ValueError, KeyError, IndexError):
                    answer = resp.text
                return answer
            except Timeout:
                return "Request timed out. Please try again later."
            except requests.exceptions.RequestException as e:
                return f"An error occurred: {str(e)} ---- is the server online?"

        if lock:
            with lock:
                return _do_request()
        return _do_request()

    @staticmethod
    def feed_the_llama_stream(messages: List[Dict[str, str]]):
        """Returns a generator that yields text chunks from the LLM via OpenAI SSE streaming."""
        mc = LLMService._get_model_config('chat')
        json_data = {**LLMService._build_request(messages, mc['model']), 'stream': True}
        url = f"http://{mc['address']}:{mc['port']}/v1/chat/completions"
        lock = LLMService._get_lock(mc['address'], mc['port']) if mc['serialize'] else None

        def _stream():
            def _do_stream():
                try:
                    resp = requests.post(
                        url,
                        headers={'Content-Type': 'application/json'},
                        json=json_data,
                        timeout=mc['timeout'],
                        stream=True,
                    )
                    resp.raise_for_status()

                    for raw_line in resp.iter_lines():
                        if not raw_line:
                            continue
                        line = raw_line.decode('utf-8') if isinstance(raw_line, bytes) else raw_line
                        if not line.startswith('data: '):
                            continue
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            return
                        try:
                            event = json.loads(data_str)
                            content = event['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                yield content
                        except (ValueError, KeyError, IndexError):
                            continue

                except Timeout:
                    yield "Request timed out. Please try again later."
                except requests.exceptions.RequestException as e:
                    yield f"An error occurred: {str(e)} ---- is the server online?"

            if lock:
                with lock:
                    yield from _do_stream()
            else:
                yield from _do_stream()

        return _stream()

    @staticmethod
    def review_chat_metadata(chat: Chat, user_message: Optional[str] = None) -> None:
        """Silently review and update chat metadata using LLM. Fire-and-forget; errors are logged and ignored."""
        try:
            last_user = user_message
            if not last_user:
                messages = list(chat.messages)
                last_user = next((m.content for m in reversed(messages) if m.role == 'user'), '')

            if not last_user:
                return

            # Load sign to get aspect schema
            sign = db.session.get(Sign, chat.sign_id) if chat.sign_id else None
            aspects_schema = None
            if sign and sign.aspects:
                try:
                    aspects_schema = json.loads(sign.aspects) if isinstance(sign.aspects, str) else sign.aspects
                except (ValueError, TypeError):
                    pass

            current_chart = (chat.chat_metadata or {}).get('chart', {})
            current_goal = chat.goal or ''

            # Build the prompt
            query = f"""Metadata: {json.dumps(chat.chat_metadata or {}, indent=2)}
New user message: {last_user}

Return ONLY a JSON object. No explanation, no markdown.
- "name": short title (≤6 words). Update if default ("Chat N") or clearly wrong.
- "emoji": single emoji. Update if empty or a better one is obvious.
- "theme": one sentence summary. ALWAYS update."""

            if aspects_schema:
                query += f"""
- "chart": object with aspect values. Current chart: {json.dumps(current_chart)}
  Aspect schema: {json.dumps(aspects_schema)}
  Update aspect values based on the conversation. Keep values within each aspect's min/max range.
- "goal": updated goal string. Current goal: {json.dumps(current_goal)}
  Update if the conversation reveals a shift in purpose."""
                query += f"""
Example: {{"name": "Python async debugging", "emoji": "🐍", "theme": "Debugging async/await.", "chart": {json.dumps({k: v.get('initial', 0.5) for k, v in aspects_schema.items()})}, "goal": "Help debug async code"}}"""
            else:
                query += """
Example: {"name": "Python async debugging", "emoji": "🐍", "theme": "Debugging async/await with SQLAlchemy."}"""

            meta_messages = [
                {"role": "system", "content": "You are a concise chat metadata assistant. Return JSON only, no explanation, no markdown."},
                {"role": "user", "content": query},
            ]

            response = LLMService.feed_the_llama(meta_messages, role='metadata')
            response = response.strip()

            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON object found in metadata review response for chat %s", chat.id)
                return

            updates = json.loads(json_match.group())
            if not isinstance(updates, dict):
                return

            # Clamp chart values to aspect schema min/max
            if 'chart' in updates and aspects_schema and isinstance(updates['chart'], dict):
                clamped = {}
                for key, val in updates['chart'].items():
                    if key in aspects_schema:
                        schema = aspects_schema[key]
                        try:
                            val = float(val)
                            val = max(schema.get('min', 0), min(schema.get('max', 1), val))
                        except (ValueError, TypeError):
                            val = schema.get('initial', 0.5)
                        clamped[key] = val
                updates['chart'] = clamped

            existing = dict(chat.chat_metadata or {})
            existing.update(updates)
            chat.chat_metadata = existing
            flag_modified(chat, 'chat_metadata')

            if 'name' in updates:
                chat.name = updates['name']
            if 'emoji' in updates:
                chat.emoji = updates['emoji']
            if 'goal' in updates:
                chat.goal = updates['goal']

            db.session.commit()
        except Exception as e:
            logger.warning("Failed to review chat metadata for chat %s: %s", chat.id, e)

