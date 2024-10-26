import requests

# Define the URLs for both endpoints
url_lang_chain_handler = 'http://127.0.0.1:5000/langChainHandler'
url_lang_chain_handler_search = 'http://127.0.0.1:5000/langChainHandlerSearch'

# Example data payload with user token and input text
payload = {
    "token": "e394cdcd-b6b4-42af-9033-2f648a8e71f3",  # Replace with actual user token
    "text": "This is a test input text."
}

# Function to test langChainHandler endpoint
def test_lang_chain_handler():
    response = requests.post(url_lang_chain_handler, json=payload)
    if response.status_code == 200:
        print("Response from langChainHandler:", response.json())
    else:
        print("Error:", response.status_code, response.text)

# Function to test langChainHandlerSearch endpoint
def test_lang_chain_handler_search():
    response = requests.post(url_lang_chain_handler_search, json=payload)
    if response.status_code == 200:
        print("Response from langChainHandlerSearch:", response.json())
    else:
        print("Error:", response.status_code, response.text)

# Run tests
print("Testing langChainHandler:")
test_lang_chain_handler()

print("\nTesting langChainHandlerSearch:")
test_lang_chain_handler_search()
