import requests

# Define the URLs for all endpoints
url= 'http://100.66.8.252:8080'
#url= 'https://kayecho-364607428894.us-central1.run.app'
url_lang_chain_handler = f'{url}/langChainHandler'
url_lang_chain_handler_search = f'{url}/langChainHandlerSearch'
url_profile_linkedin = f'{url}/userProfile'
url_simulate_conversation = f'{url}/simulateConversation'
profile_linkedin_1 = 'https://www.linkedin.com/in/ryanyoshimoto/'
profile_linkedin_2 = 'https://www.linkedin.com/in/quinteroossa/' 

# Example data payload with user token and input text
payload = {
    "token": "3669fe7bf99a1e31bc490138ad16e253",  # Replace with actual user token
    "text": "This is a test input text."
}

payload_profile = {
    "linkedin_id": profile_linkedin_1
}

payload_simulate_conversation = {
    "linkedin_1": "https://www.linkedin.com/in/jonathan-groberg/",
    "linkedin_2": "https://www.linkedin.com/in/dynamicwebpaige"
}

payload_search={
    "linkedin_id":"https://www.linkedin.com/in/jonathan-groberg/",
    "token":"4c1d11b167a6a23112bef0a2fa91e776667",
    "text":"experienced professional with over 12 years in applied machine learning, predictive modeling, data science, and visualization",
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
    response = requests.post(url_lang_chain_handler_search, json=payload_search)
    if response.status_code == 200:
        response_data = response.json()

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
print("\nTesting langChainHandlerSearch:")
test_lang_chain_handler_search()


'''
print("Testing langChainHandler:")
test_lang_chain_handler()


print("\nTesting userProfile:")
test_get_profile()
'''


print("\nTesting simulateConversation:")
test_simulate_conversation()



