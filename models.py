from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    emoji = db.Column(db.String(10), default='')
    template_id = db.Column(db.String(50), default='default')
    needs_naming = db.Column(db.Boolean, default=False)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('Message', backref='chat', lazy=True, order_by='Message.position')

    def __init__(self, id, name, emoji='', template_id='default', needs_naming=False, is_favorite=False, messages=None):
        self.id = id
        self.name = name
        self.emoji = emoji
        self.template_id = template_id
        self.needs_naming = needs_naming
        if messages:
            for idx, msg in enumerate(messages):
                db.session.add(Message(chat_id=id, content=msg, position=idx))

    def to_dict(self):
        display_name = f"{self.emoji} {self.name}".strip() if self.emoji else self.name
        return {
            'id': self.id,
            'name': display_name,
            'emoji': self.emoji,
            'is_favorite': self.is_favorite,
            'message_count': len(self.messages),
            'created_at': int(self.created_at.timestamp() * 1000) if self.created_at else None
        }

    def add_message(self, message):
        # Add a message and trim to context depth
        from flask import current_app
        CONTEXT_DEPTH = current_app.config['CONTEXT_DEPTH']
        new_position = len(self.messages)
        msg = Message(chat_id=self.id, content=message, position=new_position)
        db.session.add(msg)
        db.session.commit()
        if len(self.messages) > CONTEXT_DEPTH:
            # Remove oldest message
            oldest = Message.query.filter_by(chat_id=self.id).order_by(Message.position).first()
            if oldest:
                db.session.delete(oldest)
                # Reorder positions
                remaining = Message.query.filter_by(chat_id=self.id).order_by(Message.position).all()
                for i, m in enumerate(remaining):
                    m.position = i
                db.session.commit()

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), db.ForeignKey('chats.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)

    @property
    def role(self):
        if self.content.startswith('User: '):
            return 'user'
        elif self.content.startswith('Assistant: '):
            return 'assistant'
        return 'system'

    @property
    def text(self):
        if self.content.startswith('User: '):
            return self.content[6:]
        elif self.content.startswith('Assistant: '):
            return self.content[11:]
        return self.content

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

