import json
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    emoji = db.Column(db.String(10), default='')
    sign_id = db.Column(db.String(50), default='default')
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    chat_metadata = db.Column('metadata', db.JSON, nullable=True, default=dict)
    goal = db.Column(db.Text, nullable=True)

    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan', order_by='Message.position')

    def __init__(self, id, name, emoji='', sign_id='default', is_favorite=False, chat_metadata=None, goal=None):
        self.id = id
        self.name = name
        self.emoji = emoji
        self.sign_id = sign_id
        self.chat_metadata = chat_metadata or {}
        self.goal = goal

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'emoji': self.emoji or '',
            'sign_id': self.sign_id,
            'is_favorite': self.is_favorite,
            'message_count': len(self.messages),
            'created_at': int(self.created_at.timestamp() * 1000) if self.created_at else None,
            'metadata': self.chat_metadata or {},
            'goal': self.goal or '',
        }

    def add_message(self, role, content):
        new_position = len(self.messages)
        msg = Message(chat_id=self.id, role=role, content=content, position=new_position)
        db.session.add(msg)
        db.session.commit()

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), db.ForeignKey('chats.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='system')
    content = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)

class Sign(db.Model):
    __tablename__ = 'signs'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    prefix = db.Column(db.Text, nullable=False)
    postfix = db.Column(db.Text, nullable=False)
    values = db.Column(db.Text, nullable=True)
    interests = db.Column(db.Text, nullable=True)
    default_goal = db.Column(db.Text, nullable=True)
    aspects = db.Column(db.Text, nullable=True)

    def to_dict(self):
        def _parse_json(text):
            if not text:
                return None
            try:
                return json.loads(text)
            except (ValueError, TypeError):
                return text

        return {
            'id': self.id,
            'name': self.name,
            'prefix': self.prefix,
            'postfix': self.postfix,
            'values': _parse_json(self.values),
            'interests': _parse_json(self.interests),
            'default_goal': self.default_goal or '',
            'aspects': _parse_json(self.aspects),
        }
