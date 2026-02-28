import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

import requests
from flask import current_app
from requests.exceptions import Timeout

from models import Chat, Message, Template, db

logger = logging.getLogger(__name__)


class ChatService:
    @staticmethod
    def create_chat(name: str) -> Chat:
        chat_id = str(uuid.uuid4())
        chat = Chat(id=chat_id, name=name, needs_naming=False)
        db.session.add(chat)
        db.session.commit()
        return chat

    @staticmethod
    def get_chat(chat_id: str) -> Optional[Chat]:
        return db.session.get(Chat, chat_id)

    @staticmethod
    def update_chat(chat_id: str, name: Optional[str] = None, emoji: Optional[str] = None, template_id: Optional[str] = None, is_favorite: Optional[bool] = None) -> Optional[Chat]:
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
    def feed_the_llama(query: str, prefix: str, postfix: str) -> str:
        config = current_app.config
        json_data = {
            'PROMPT_TEXT_PREFIX': prefix,
            'input_str': str(query) + ' ',
            'PROMPT_TEXT_POSTFIX': postfix,
        }

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

class NamingService:
    @staticmethod
    def generate_name(chat: Chat) -> None:
        try:
            naming_prompt = (
                "Please provide a very short (1-3 words) descriptive name for the conversation we just had, "
                "and a single emoji that summarizes it. Respond ONLY with a JSON object like: {\"name\": \"...\", \"emoji\": \"...\"}."
            )
            default_template = TemplateService.get_template('default')
            if not default_template:
                TemplateService.ensure_default_template()
                default_template = TemplateService.get_template('default')
            naming_response = LLMService.feed_the_llama(naming_prompt, default_template.prefix, default_template.postfix)

            parsed = None
            try:
                parsed = json.loads(naming_response)
            except (json.JSONDecodeError, ValueError):
                m = re.search(r"(\{.*\})", naming_response, re.DOTALL)
                if m:
                    try:
                        parsed = json.loads(m.group(1))
                    except (json.JSONDecodeError, ValueError):
                        parsed = None

            if isinstance(parsed, dict):
                name = parsed.get('name', '').strip()
                emoji = parsed.get('emoji', '').strip()
                if name:
                    chat.name = name
                    chat.emoji = emoji
                    chat.needs_naming = False
                    db.session.commit()
        except Exception as e:
            logger.exception("Failed to generate chat name: %s", e)
