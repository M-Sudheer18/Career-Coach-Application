import os
import json
import logging
import logging.config

# Logger specifically for this utility module
logger = logging.getLogger(__name__)

# Initializes the logging configuration.
def setup_logging(default_path="config/logging.config", default_level=logging.INFO):
    path = default_path
    if os.path.exists(path):
        with open(path, 'rt') as f:
            try:
                config = json.load(f)
                logging.config.dictConfig(config)
            except Exception as e:
                # Fallback if the JSON is malformed
                logging.basicConfig(level=default_level)
                logger.error(
                    "Failed to load logging configuration from %s. "
                    "Using basic setup. Error: %s", path, e
                )
    else:
        # Fallback if the file is missing
        logging.basicConfig(level=default_level)
        logging.warning(
            "Logging config file '%s' not found. Using basic setup.", 
            path
        )