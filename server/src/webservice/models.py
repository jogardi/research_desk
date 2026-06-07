import yaml
import os

# Get the directory of this file and construct path to models.yml
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up two levels from src/webservice/ to reach the webservice root
models_yml_path = os.path.join(current_dir, "..", "..", "models.yml")

# Load YAML file
with open(models_yml_path, "r") as file:
    data = yaml.safe_load(file)

# Load defaultModel and models from YAML
defaultModel = data['defaultModel']
models = data['models']

# Add defaultModel to models list
models.insert(0, defaultModel)

print("*** Loaded models!")