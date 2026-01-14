import os

# Function to replace env variables on nested JSON
def replace_env_vars(data, key=None):
    if isinstance(data, list):
        return data
    if isinstance(data, dict): 
        return {k: replace_env_vars(v) for k, v in data.items()}
    env_var_name = data.upper().replace(".", "_")
    env_val = os.environ.get(env_var_name, None)
    return  env_val if env_val != None else data

