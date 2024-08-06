import json
import logging
from pathlib import Path

import pydantic_core

import schemas.settings as settings
from utils.log_manager import LoggingManager

logging_manager = LoggingManager()


class ConfigManager:
    def __init__(self, config_file_path: str = './data/config.json'):
        self.config_file_path = Path(config_file_path)
        self.config_file_data = None
        self.load_config_file()

    def write_default_configs(self):
        logging_manager.log('Writing default config', level=logging.INFO)
        default_config = settings.Config(
            SONARR=settings.SonarrSettings(),
            RADARR=settings.RadarrSettings(),
            CONNECTIONS=settings.MediaServerSettings(),
            MEDIASERVER=settings.MediaServerSettings(),
            MISC=settings.MiscSettings()
        )
        self.config_file_data = default_config

        with open(str(self.config_file_path).replace(".json", "-default.json"), 'w') as f:
            json.dump(default_config.model_dump(), f, indent=4)

    def load_config_file(self):
        try:
            if not self.config_file_path.exists():
                self.write_default_configs()
            else:
                with open(self.config_file_path) as json_file:
                    self.config_file_data = settings.Config.model_validate(json.load(json_file))
        except pydantic_core._pydantic_core.ValidationError:
            logging_manager.log('Config file is invalid, writing default config', level=logging.WARNING)
            self.write_default_configs()
        except FileNotFoundError:
            logging_manager.log('Config file not found, writing default config', level=logging.WARNING)
            self.write_default_configs()

    def save_config_file(self, config_data: settings.Config):
        self.config_file_data = config_data
        logging_manager.log('Saving config file', level=logging.DEBUG)
        logging_manager.log(config_data.model_dump_json(indent=4), level=logging.DEBUG)
        with open(self.config_file_path, 'w') as f:
            json.dump(config_data.model_dump(), f, indent=4)

    def get_config(self) -> settings.Config:
        self.load_config_file()
        return self.config_file_data


# Example usage:
if __name__ == "__main__":
    config_manager = ConfigManager()
    config = config_manager.get_config()
    print(config.model_dump_json(indent=4))
