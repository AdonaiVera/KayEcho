import requests

# Define the URLs for all endpoints
#url= 'http://172.17.0.2:8080'
url= 'https://kayecho-364607428894.us-central1.run.app'
url_lang_chain_handler = f'{url}/langChainHandler'
url_lang_chain_handler_search = f'{url}/langChainHandlerSearch'
url_profile_linkedin = f'{url}/userProfile'
url_simulate_conversation = f'{url}/simulateConversation'
profile_linkedin_1 = 'https://www.linkedin.com/in/ryanyoshimoto/'
profile_linkedin_2 = 'https://www.linkedin.com/in/quinteroossa/' 

# Example data payload with user token and input text
payload = {
    "token": "e394cdcd-b6b4-42af-9033-2f648a8e71f3",  # Replace with actual user token
    "text": "This is a test input text."
}

payload_profile = {
    "linkedin_id": profile_linkedin_1
}

payload_simulate_conversation = {
    "linkedin_1": profile_linkedin_1,
    "linkedin_2": profile_linkedin_2
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
        response_data = response.json()
        
        # Check if "response" and "profile_user" keys are in the JSON response
        assert "response" in response_data, "Missing 'response' in JSON output"
        assert "profile_user" in response_data, "Missing 'profile_user' in JSON output"
        
        # Check if "text" and "token" keys are in the "response" dictionary
        assert "text" in response_data["response"], "Missing 'text' in response structure"
        assert "token" in response_data["response"], "Missing 'token' in response structure"
        
        # Print results for manual inspection
        print("Response from langChainHandlerSearch:", response_data)
    else:
        print("Error:", response.status_code, response.text)

# Function to test userProfile endpoint
def test_get_profile():
    response = requests.post(url_profile_linkedin, json=payload_profile)
    if response.status_code == 200:
        print("Response from userProfile:", response.json())
    else:
        print("Error:", response.status_code, response.text)

# Function to test simulateConversation endpoint
def test_simulate_conversation():
    response = requests.post(url_simulate_conversation, json=payload_simulate_conversation)
    if response.status_code == 200:
        print("Response from simulateConversation:", response.json())
    else:
        print("Error:", response.status_code, response.text)

# Run tests
print("Testing langChainHandler:")
test_lang_chain_handler()

print("\nTesting langChainHandlerSearch:")
test_lang_chain_handler_search()

print("\nTesting userProfile:")
test_get_profile()

print("\nTesting simulateConversation:")
test_simulate_conversation()




