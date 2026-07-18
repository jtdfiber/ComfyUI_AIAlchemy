import os
import time
import requests
import configparser
from .utils import get_local_app_setting_path, get_machine_id, generate_random_string
from .url_config import CatUrlConfig
from server import PromptServer


class AuthUnit:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AuthUnit, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.machine_id = get_machine_id()
            local_app_path = get_local_app_setting_path()
            local_app_path.mkdir(parents=True, exist_ok=True)
            self.config_path = local_app_path / "config.ini"
            self.last_check_time = 0
            self.initialized = True

    def empty_token(self, need_clear=False):
        self.token = ""
        self.last_check_time = 0
        if need_clear:
            self.clear_user_token()

    def get_user_token(self):
        # AI Alchemy self-host: the creator token comes from server.json (encrypt
        # machine only). Buyers have no token — decode uses their license key.
        from .selfhost import creator_token
        tok = creator_token()
        if tok:
            return tok, "", 0
        # Fallback: a token pasted/stored locally (optional).
        self.token = self.read_user_token()
        if self.token and len(self.token) > 10:
            return self.token, "", 0
        return None, "no creator token — set it in server.json (encrypt machine only)", -3

    def login_dialog(self, title=""):
        self.client_key = generate_random_string(8)
        PromptServer.instance.send_sync(
            "alchemycrypto_login_dialog",
            {
                "machine_id": self.machine_id,
                "client_key": self.client_key,
                "title": title,
            },
        )

    def read_user_token(self):
        if not os.path.exists(self.config_path):
            return ""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_path, encoding="utf-8")
            return config.get("Auth", "user_token", fallback="")
        except Exception as e:
            print(f"Error reading token: {e}")
            return ""

    def set_user_token(self, user_token, client_key):
        if not client_key or self.client_key != client_key:
            print("client_key is not match")
            return
        if not user_token:
            user_token = ""
            print("user_token is empty")
        self._save_user_token(user_token)

    def _save_user_token(self, user_token):
        try:
            config = configparser.ConfigParser()
            if os.path.exists(self.config_path):
                config.read(self.config_path, encoding="utf-8")
            else:
                local_app_path = get_local_app_setting_path()
                if not os.path.exists(local_app_path):
                    local_app_path.mkdir(parents=True, exist_ok=True)
            if "Auth" not in config:
                config.add_section("Auth")
            config["Auth"]["user_token"] = user_token
            with open(self.config_path, "w", encoding="utf-8") as f:
                config.write(f)
            print(f"Token saved successfully. config_path:{self.config_path}")
        except Exception as e:
            print(f"Error saving token: {e}")
            raise RuntimeError(f"Failed to save token: {e}")

    def set_long_token(self, long_token):
        if not long_token or len(long_token) < 50:
            return
        self._save_user_token(long_token)
        self.client_key = ""

    def clear_user_token(self):
        PromptServer.instance.send_sync(
            "alchemycrypto_clear_user_info", {"clear_key": "all"}
        )
        if os.path.exists(self.config_path):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_path, encoding="utf-8")
                if "Auth" not in config:
                    return
                if "user_token" not in config["Auth"]:
                    return
                config["Auth"]["user_token"] = ""
                with open(self.config_path, "w", encoding="utf-8") as f:
                    config.write(f)
            except Exception as e:
                print(f"Error clearing token: {e}")
                raise RuntimeError(f"Failed to clear token: {e}")
