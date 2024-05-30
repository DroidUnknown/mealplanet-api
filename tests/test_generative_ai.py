
base_api_url = "/api"

def do_generate_text(client, headers, payload):
    response = client.post(f"{base_api_url}/ai/generate-text", headers=headers, json=payload)
    return response