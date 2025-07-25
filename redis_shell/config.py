import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from .utils.logging_utils import ConfigurationError

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    # General settings
    "general": {
        "history_size": 100,
        "log_level": "info",
        "log_file": None,
        "state_file": "~/.redis-shell"
    },

    # Redis connection settings
    "redis": {
        "default_host": "127.0.0.1",
        "default_port": 6379,
        "default_db": 0,
        "default_username": "default",
        "default_password": "",
        "timeout": 5,
        "decode_responses": False,
        "ssl": False,
        "ssl_ca_certs": None,
        "ssl_ca_path": None,
        "ssl_keyfile": None,
        "ssl_certfile": None,
        "ssl_cert_reqs": "required"
    },

    # Extension settings
    "extensions": {
        "extension_dir": "~/.config/redis-shell/extensions"
    },

    # UI settings
    "ui": {
        "prompt_style": "green",
        "error_style": "red",
        "warning_style": "yellow",
        "success_style": "green",
        "info_style": "blue"
    }
}


class Config:
    """Configuration manager for redis-shell."""

    _instance = None

    def __new__(cls):
        """Singleton implementation."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the configuration manager."""
        if getattr(self, '_initialized', False):
            return

        self.config = DEFAULT_CONFIG.copy()
        self.config_file = self._get_config_file_path()
        self._load_config()
        self._initialized = True

    def _get_config_file_path(self) -> str:
        """
        Get the configuration file path.

        Returns:
            Configuration file path
        """
        # Check environment variable first
        config_file = os.environ.get('REDIS_SHELL_CONFIG')
        if config_file:
            return os.path.expanduser(config_file)

        # Check common locations
        locations = [
            '~/.redis-shell',
            '~/.config/redis-shell/config.json',
            '/etc/redis-shell/config.json'
        ]

        for location in locations:
            expanded_path = os.path.expanduser(location)
            if os.path.isfile(expanded_path):
                return expanded_path

        # Return default location
        return os.path.expanduser('~/.redis-shell')

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            # Reset to default configuration first
            self.config = DEFAULT_CONFIG.copy()

            # If the file exists but is empty, initialize it with default configuration
            if os.path.isfile(self.config_file) and os.path.getsize(self.config_file) == 0:
                self.save_config()

            # If the file does not exist, create it with default configuration
            elif not os.path.isfile(self.config_file):
                self.save_config()

            if os.path.isfile(self.config_file):
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)

                # Replace the configuration with what's in the file
                # This ensures we're always using the latest data from disk
                self.config = user_config
            # If file doesn't exist, we'll use the default configuration

        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise ConfigurationError(f"Error loading configuration: {str(e)}")

    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Merge source configuration into target configuration.

        Args:
            target: Target configuration
            source: Source configuration
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value


    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Create directory if needed (only if the path includes a directory)
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)

            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)

            # Configuration saved successfully
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            raise ConfigurationError(f"Error saving configuration: {str(e)}")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        # Always reload the configuration from disk to ensure we have the latest values
        self._load_config()

        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default

    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Configuration value
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.

        Args:
            section: Configuration section

        Returns:
            Configuration section
        """
        # Always reload the configuration from disk to ensure we have the latest values
        self._load_config()

        return self.config.get(section, {})

    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration.

        Returns:
            Entire configuration
        """
        # Always reload the configuration from disk to ensure we have the latest values
        self._load_config()

        return self.config.copy()


# Create a global configuration instance
config = Config()
