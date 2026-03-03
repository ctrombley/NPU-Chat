import json
import os


class Config:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Web UI
        self.BINDING_ADDRESS = os.environ.get('BINDING_ADDRESS', '0.0.0.0')
        self.BINDING_PORT = int(os.environ.get('BINDING_PORT', '1314'))

        # NPU Server — OpenAI-compatible proxy (port 8090)
        self.NPU_ADDRESS = os.environ.get('NPU_ADDRESS', 'localhost')
        self.NPU_PORT = os.environ.get('NPU_PORT', '8090')
        self.NPU_MODEL = os.environ.get('NPU_MODEL', 'qwen3-4b')
        self.CONNECTION_TIMEOUT = int(os.environ.get('CONNECTION_TIMEOUT', '120'))

        # Model registry — JSON mapping role → {address, port, timeout, serialize, model}
        # If not set, all roles use NPU_ADDRESS:NPU_PORT with NPU_MODEL
        raw_registry = os.environ.get('MODEL_REGISTRY', '')
        if raw_registry:
            self.MODEL_REGISTRY = json.loads(raw_registry)
        else:
            self.MODEL_REGISTRY = {
                'chat': {
                    'address': self.NPU_ADDRESS,
                    'port': int(self.NPU_PORT),
                    'timeout': self.CONNECTION_TIMEOUT,
                    'serialize': True,
                    'model': self.NPU_MODEL,
                }
            }

        # Context
        self.USE_CONTEXT = os.environ.get('USE_CONTEXT', 'True').lower() in ('true', '1', 'yes')
        raw_context_depth = int(os.environ.get('CONTEXT_DEPTH', '1'))
        self.CONTEXT_DEPTH = max(2, raw_context_depth)

        # Database
        default_db = f"sqlite:///{os.path.join(script_dir, 'data', 'chats.db')}"
        self.SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', default_db)
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        # Logging
        self.LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json')
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

        # Rate limiting
        self.RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day;50 per hour')
        self.RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')

        # Metadata review
        self.METADATA_REVIEW_ENABLED = os.environ.get('METADATA_REVIEW_ENABLED', 'True').lower() in ('true', '1', 'yes')
