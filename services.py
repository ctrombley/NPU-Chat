import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

import requests
from flask import current_app
from requests.exceptions import Timeout
from sqlalchemy.orm.attributes import flag_modified

from models import Chat, Message, Template, db

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
    def create_chat(name: Optional[str] = None, template_id: Optional[str] = None) -> Chat:
        if not name:
            name = ChatService._next_default_name()
        chat_id = str(uuid.uuid4())
        chat = Chat(id=chat_id, name=name,
                    template_id=template_id or 'default')
        db.session.add(chat)
        db.session.commit()
        return chat

    @staticmethod
    def get_chat(chat_id: str) -> Optional[Chat]:
        return db.session.get(Chat, chat_id)

    @staticmethod
    def update_chat(chat_id: str, name: Optional[str] = None, emoji: Optional[str] = None, template_id: Optional[str] = None, is_favorite: Optional[bool] = None, metadata: Optional[Dict] = None) -> Optional[Chat]:
        chat = db.session.get(Chat, chat_id)
        if not chat:
            return None
        if name is not None:
            chat.name = name
        if emoji is not None:
            chat.emoji = emoji
        if template_id is not None:
            chat.template_id = template_id
        if is_favorite is not None:
            chat.is_favorite = is_favorite
        if metadata is not None:
            existing = chat.chat_metadata or {}
            existing.update(metadata)
            chat.chat_metadata = existing
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

class TemplateService:
    @staticmethod
    def list_templates() -> List[Template]:
        return Template.query.all()

    @staticmethod
    def ensure_default_template() -> None:
        if not db.session.get(Template, 'default'):
            default = Template(
                id='default',
                name='Default',
                prefix="<|im_start|>system You are a helpful assistant. <|im_end|> <|im_start|>user ",
                postfix=" <|im_end|><|im_start|>assistant "
            )
            db.session.add(default)
            db.session.commit()

    @staticmethod
    def get_template(template_id: str) -> Optional[Template]:
        return db.session.get(Template, template_id)

    @staticmethod
    def create_template(name: str, prefix: str, postfix: str) -> Template:
        template_id = str(uuid.uuid4())
        template = Template(id=template_id, name=name, prefix=prefix, postfix=postfix)
        db.session.add(template)
        db.session.commit()
        return template

    @staticmethod
    def update_template(template_id: str, name: Optional[str] = None, prefix: Optional[str] = None, postfix: Optional[str] = None) -> Optional[Template]:
        template = db.session.get(Template, template_id)
        if not template or template_id == 'default':
            return None
        if name is not None:
            template.name = name
        if prefix is not None:
            template.prefix = prefix
        if postfix is not None:
            template.postfix = postfix
        db.session.commit()
        return template

    @staticmethod
    def clone_template(template_id: str) -> Optional[Template]:
        source = db.session.get(Template, template_id)
        if not source:
            return None
        new_id = str(uuid.uuid4())
        clone = Template(id=new_id, name=f"Copy of {source.name}",
                         prefix=source.prefix, postfix=source.postfix)
        db.session.add(clone)
        db.session.commit()
        return clone

    @staticmethod
    def delete_template(template_id: str) -> bool:
        if template_id == 'default':
            return False
        template = db.session.get(Template, template_id)
        if not template:
            return False
        db.session.delete(template)
        db.session.commit()
        return True

class LLMService:
    @staticmethod
    def _build_request(query: str, prefix: str, postfix: str) -> Dict[str, Any]:
        return {
            'PROMPT_TEXT_PREFIX': prefix,
            'input_str': str(query) + ' ',
            'PROMPT_TEXT_POSTFIX': postfix,
        }

    @staticmethod
    def feed_the_llama(query: str, prefix: str, postfix: str) -> str:
        config = current_app.config
        json_data = LLMService._build_request(query, prefix, postfix)
        headers = {'Content-Type': 'application/json'}

        try:
            resp = requests.post(
                f"http://{config['NPU_ADDRESS']}:{config['NPU_PORT']}",
                headers=headers,
                json=json_data,
                timeout=config['CONNECTION_TIMEOUT']
            )
            resp.raise_for_status()
            resp_json: Dict[str, Any] = resp.json()
            answer = resp_json.get('content', '')
            return answer
        except Timeout:
            return "Request timed out. Please try again later."
        except requests.exceptions.RequestException as e:
            error_msg = f"An error occurred: {str(e)} ---- is the server online?"
            return error_msg

    @staticmethod
    def feed_the_llama_stream(query: str, prefix: str, postfix: str):
        """Returns a generator that yields chunks of the LLM response for SSE streaming."""
        # Capture config values now while still in the application context,
        # since the returned generator will be iterated outside it during streaming.
        config = current_app.config
        npu_address = config['NPU_ADDRESS']
        npu_port = config['NPU_PORT']
        connection_timeout = config['CONNECTION_TIMEOUT']
        json_data = LLMService._build_request(query, prefix, postfix)

        def _stream():
            headers = {'Content-Type': 'application/json'}

            try:
                resp = requests.post(
                    f"http://{npu_address}:{npu_port}",
                    headers=headers,
                    json=json_data,
                    timeout=connection_timeout,
                    stream=True,
                )
                resp.raise_for_status()

                # Try to consume as a chunked stream first
                buffer = b""
                got_chunks = False
                for chunk in resp.iter_content(chunk_size=64):
                    if chunk:
                        got_chunks = True
                        buffer += chunk
                        # Try to decode and yield partial text
                        try:
                            partial = buffer.decode('utf-8')
                            yield partial
                            buffer = b""
                        except UnicodeDecodeError:
                            # Incomplete multi-byte char, wait for more data
                            continue

                # If we got chunked data, flush any remaining buffer
                if got_chunks and buffer:
                    try:
                        yield buffer.decode('utf-8', errors='replace')
                    except Exception:
                        pass
                    return

                # If iter_content gave us the full response at once (no chunking),
                # parse JSON and yield the content in small pieces
                if not got_chunks:
                    full_text = resp.text
                    try:
                        resp_json = resp.json()
                        full_text = resp_json.get('content', full_text)
                    except (ValueError, KeyError):
                        pass
                    # Yield word-by-word for a typing effect
                    words = full_text.split(' ')
                    for i, word in enumerate(words):
                        yield word + (' ' if i < len(words) - 1 else '')

            except Timeout:
                yield "Request timed out. Please try again later."
            except requests.exceptions.RequestException as e:
                yield f"An error occurred: {str(e)} ---- is the server online?"

        return _stream()

    @staticmethod
    def review_chat_metadata(chat: Chat) -> None:
        """Silently review and update chat metadata using LLM. Fire-and-forget; errors are logged and ignored."""
        try:
            # Find last user and assistant messages
            messages = list(chat.messages)
            last_user = next((m.content for m in reversed(messages) if m.role == 'user'), '')
            last_assistant = next((m.content for m in reversed(messages) if m.role == 'assistant'), '')

            if not last_user and not last_assistant:
                return

            query = f"""Current metadata:
{json.dumps(chat.chat_metadata or {}, indent=2)}

Latest exchange:
User: {last_user}
Assistant: {last_assistant}

Instructions:
- Return ONLY a JSON object with fields to update. No explanation, no markdown.
- "name": short title (≤6 words). Update if still a default like "Chat N" or clearly wrong.
- "emoji": single emoji. Update if empty or if a better one is obvious.
- "theme": one sentence summary of what this chat is about. ALWAYS update this.
- Add any other fields useful for tracking this conversation's context.
- Example: {{"name": "Python async debugging", "emoji": "🐍", "theme": "Debugging async/await with SQLAlchemy."}}"""

            prefix = "<|im_start|>system You are a concise chat metadata assistant. <|im_end|> <|im_start|>user "
            postfix = " <|im_end|><|im_start|>assistant "

            response = LLMService.feed_the_llama(query, prefix, postfix)
            response = response.strip()

            # Extract JSON object from the response, tolerating surrounding text/fences
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON object found in metadata review response for chat %s", chat.id)
                return

            updates = json.loads(json_match.group())
            if not isinstance(updates, dict):
                return

            existing = dict(chat.chat_metadata or {})
            existing.update(updates)
            chat.chat_metadata = existing
            flag_modified(chat, 'chat_metadata')

            if 'name' in updates:
                chat.name = updates['name']
            if 'emoji' in updates:
                chat.emoji = updates['emoji']

            db.session.commit()
        except Exception as e:
            logger.warning("Failed to review chat metadata for chat %s: %s", chat.id, e)

