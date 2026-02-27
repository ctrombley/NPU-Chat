import configparser
import os


class Config:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.load_config(script_dir)

    def load_config(self, script_dir):
        if script_dir and script_dir[-1] != '/':
            script_dir = script_dir + "/"

        config_path = f"{script_dir}settings.ini"
        parser = configparser.ConfigParser()
        parser.read(config_path)

        self.BINDING_ADDRESS = parser.get('chat_ui', 'BINDING_ADDRESS')
        self.BINDING_PORT = int(parser.get('chat_ui', 'BINDING_PORT'))
        self.NPU_ADDRESS = parser.get('npu', 'NPU_ADDRESS')
        self.NPU_PORT = parser.get('npu', 'NPU_PORT')
        self.CONNECTION_TIMEOUT = int(parser.get('timeout', 'TIMEOUT'))

        self.USE_CONTEXT = parser.getboolean('context', 'USE_CONTEXT', fallback=False)
        raw_context_depth = int(parser.get('context', 'DEPTH'))
        self.CONTEXT_DEPTH = max(2, raw_context_depth)

        # Database
        self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(script_dir, 'data', 'chats.db')}"
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
