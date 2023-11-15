import yaml

# Read the .txt file
with open('available_functions_agent.txt', 'r') as txt_file:
    lines = txt_file.readlines()

# Prepare data for yaml
data = {'lines': lines}

# Write to .yaml file
with open('available_functions_agent.yaml', 'w') as yaml_file:
    yaml.dump(data, yaml_file)