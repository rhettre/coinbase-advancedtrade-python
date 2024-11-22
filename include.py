import json

def load_api_credentials(json_file_path='cdp_api_key.json'):
    # Read the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Extract the API key and secret
    api_key = data['name']
    api_secret = data['privateKey']
    
    return api_key, api_secret
