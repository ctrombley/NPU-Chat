import os


class Config:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Web UI
        self.BINDING_ADDRESS = os.environ.get('BINDING_ADDRESS', '0.0.0.0')
        self.BINDING_PORT = int(os.environ.get('BINDING_PORT', '1314'))

        # NPU Server
        self.NPU_ADDRESS = os.environ.get('NPU_ADDRESS', '192.168.0.196')
        self.NPU_PORT = os.environ.get('NPU_PORT', '31337')
        self.CONNECTION_TIMEOUT = int(os.environ.get('CONNECTION_TIMEOUT', '45'))

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
