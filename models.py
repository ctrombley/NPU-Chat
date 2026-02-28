from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    emoji = db.Column(db.String(10), default='')
    template_id = db.Column(db.String(50), default='default')
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan', order_by='Message.position')

    def __init__(self, id, name, emoji='', template_id='default', is_favorite=False):
        self.id = id
        self.name = name
        self.emoji = emoji
        self.template_id = template_id

    def to_dict(self):
        display_name = f"{self.emoji} {self.name}".strip() if self.emoji else self.name
        return {
            'id': self.id,
            'name': display_name,
            'emoji': self.emoji,
            'template_id': self.template_id,
            'is_favorite': self.is_favorite,
            'message_count': len(self.messages),
            'created_at': int(self.created_at.timestamp() * 1000) if self.created_at else None
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

class Template(db.Model):
    __tablename__ = 'templates'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    prefix = db.Column(db.Text, nullable=False)
    postfix = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'prefix': self.prefix,
            'postfix': self.postfix
        }
