from pathlib import Path
import sys, os

if __name__ == "__main__":
    MODULE_PARENT_DIR = Path(__file__).parent.resolve()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))


from mekeweserver.config import Config, get_config

from psyplus import YamlSettingsPlus

OUTPUT_FILE = "config.template.yaml"

os.environ["FRONTEND_FILES_DIR"] = "frontend/.output/public"
yaml_handler = YamlSettingsPlus(Config, OUTPUT_FILE)

yaml_handler.generate_config_file(overwrite_existing=True)

config_file_content = []
with open(OUTPUT_FILE, "rt") as file:
    for line in file:
        if line.startswith('# Default:      "/home/'):
            config_file_content.append('# Default:      "frontend/.output/public"\n')
        else:
            config_file_content.append(line)
with open(OUTPUT_FILE, "wt") as file:
    file.write("".join(config_file_content))
