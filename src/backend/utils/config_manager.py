import json
import logging
from pathlib import Path

from pydantic import ValidationError

import schemas.settings as settings
from utils.log_manager import LoggingManager

logging_manager = LoggingManager()

CONFIG_VERSION = "0.1.2"


# region Upgrade functions

def upgrade_v0_1_1_to_v0_1_2(config_data):
    # Define changes needed to upgrade from v0.1.1 to v0.1.2
    config_data["MUSICVIDEO"]["download_subtitles"] = True
    config_data["MUSICVIDEO"]["subtitle_languages"] = ["en"]
    config_data["MISC"]["config_version"] = "0.1.2"
    return config_data


def upgrade_v0_1_0_to_v0_1_1(config_data):
    # Define changes needed to upgrade from v0.1.0 to v0.1.1
    config_data["SPOTIFY"] = settings.SpotifySettings().dict()
    config_data["MUSICVIDEO"] = settings.MusicVideoSettings().dict()
    config_data["MISC"]["config_version"] = "0.1.1"
    return config_data


# endregion

upgrade_map = {
    "0.1.0": upgrade_v0_1_0_to_v0_1_1,
    "0.1.1": upgrade_v0_1_1_to_v0_1_2,
}


class ConfigManager:
    def __init__(self, config_file_path: str = './data/config.json', latest_version=CONFIG_VERSION):
        self.config_file_path = Path(config_file_path)
        self.config_file_data = None
        self.latest_version = latest_version
        self.load_config_file()

    def write_default_configs(self):
        logging_manager.log('Writing default config', level=logging.INFO)
        default_config = settings.Config(
            SONARR=settings.SonarrSettings(),
            RADARR=settings.RadarrSettings(),
            SPOTIFY=settings.SpotifySettings(),
            MUSICVIDEO=settings.MusicVideoSettings(),
            MEDIASERVER=settings.MediaServerSettings(),
            MISC=settings.MiscSettings(config_version=CONFIG_VERSION)
        )
        self.config_file_data = default_config

        with open(str(self.config_file_path).replace(".json", "-default.json"), 'w') as f:
            json.dump(default_config.dict(), f, indent=4)

    def upgrade_config(self, existing_config_data):
        logging_manager.log('Upgrading config file', level=logging.INFO)
        current_version = existing_config_data.get("MISC", {}).get("config_version", "0.0.0")

        while current_version in upgrade_map and current_version != self.latest_version:
            logging_manager.log(f'Upgrading from {current_version}', level=logging.INFO)
            upgrade_func = upgrade_map[current_version]
            existing_config_data = upgrade_func(existing_config_data)
            current_version = existing_config_data["MISC"]["config_version"]

        return existing_config_data

    def load_config_file(self):
        try:
            if not self.config_file_path.exists():
                self.write_default_configs()
            else:
                with open(self.config_file_path) as json_file:
                    config_data = json.load(json_file)
                    upgraded = False
                    if config_data["MISC"]["config_version"] != self.latest_version:
                        logging_manager.log('Config version mismatch, upgrading config', level=logging.INFO)
                        config_data = self.upgrade_config(config_data)
                        upgraded = True
                    self.config_file_data = settings.Config(**config_data)
                    if upgraded:
                        self.save_config_file(self.config_file_data)
        except ValidationError:
            logging_manager.log('Config file is invalid, writing default config', level=logging.WARNING)
            self.write_default_configs()
        except FileNotFoundError:
            logging_manager.log('Config file not found, writing default config', level=logging.WARNING)
            self.write_default_configs()

    def save_config_file(self, config_data: settings.Config):
        self.config_file_data = config_data
        logging_manager.log('Saving config file', level=logging.DEBUG)
        logging_manager.log(json.dumps(config_data.dict(), indent=4), level=logging.DEBUG, print_message=False)
        with open(self.config_file_path, 'w') as f:
            json.dump(config_data.dict(), f, indent=4)

    def get_config(self) -> settings.Config:
        self.load_config_file()
        return self.config_file_data


# Example usage:
if __name__ == "__main__":
    config_manager = ConfigManager()
    config = config_manager.get_config()
    print(json.dumps(config.dict(), indent=4))
