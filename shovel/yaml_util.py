import yaml
from datetime import datetime

# Loads the given yaml
def load_yaml(yaml_path):
    file = open(yaml_path, "r")
    doc = str(yaml.load(file))
    # Insert current timestamp for any occurrences of '$now' in yaml config
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    doc = doc.replace('$now', now)
    print doc + "\n"
    return yaml.load(doc)