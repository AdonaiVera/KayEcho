import csv
from methods.agent_scrapper import scrape_guests_from_event, get_linkedin_from_guest_profile, extract_linkedin_profile
from methods.agent_openai import get_profile, get_profile_db
import json
from methods.agent_mongo import MongoDBHandler
import requests
import base64
import os 
from dotenv import load_dotenv, find_dotenv

# Meta variables
_ = load_dotenv(find_dotenv()) 

csv_file = os.environ['CSV_FILE'] 
collection_type="user_profile"
mongo_uri = os.environ['MONGO_URI'] 
openai_api_key= os.environ['OPENAI_API_KEY']
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

mongo_handler = MongoDBHandler(mongo_uri, openai_api_key)

# Function to write headers to the CSV file if it doesn't exist or is empty
def initialize_csv(file_name):
    try:
        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the header row
            writer.writerow([
                'name', 
                'linkedin_url', 
                'picture', 
                'profile',
                'topic', 
                'key_words',
                'main_topic',
                'event_url']
            )
    except Exception as e:
        print(f"Error initializing CSV file: {e}")

# Function to check if the LinkedIn URL already exists in the CSV file
def linkedin_exists_in_csv(file_name, linkedin_url):
    try:
        with open(file_name, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[1] == linkedin_url:  # Assuming LinkedIn URL is the second column (index 1)
                    return True
        return False
    except FileNotFoundError:
        return False  # If the file doesn't exist yet, proceed normally
    except Exception as e:
        print(f"Error checking CSV file: {e}")
        return False

# Function to append data to the CSV file
def append_to_csv(file_name, guest_name, linkedin_url, picture, profile, topic, key_words, main_topic, event_url):
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Append the row of data
            writer.writerow([guest_name, linkedin_url, picture, profile, topic, key_words, main_topic, event_url])
    except Exception as e:
        print(f"Error writing to CSV file: {e}")

# Initialize the CSV file (write headers)
if not os.path.exists(csv_file):
    initialize_csv(csv_file)

# Scrape guests from the event
list_linkedin_urls=[
    "https://www.linkedin.com/in/aaronbegg1/",
    "https://www.linkedin.com/in/dynamicwebpaige",
    "https://www.linkedin.com/in/alex-albert/",
    "https://www.linkedin.com/in/kem-ezeoke-149b1a53/", 
    "https://www.linkedin.com/in/vaishnavitumsi/",
    "https://www.linkedin.com/in/irfanessa"
    ]

nCount = 0
for linkedin_url in list_linkedin_urls:
    try:
        # Extract LinkedIn profile information
        profile_info = extract_linkedin_profile(linkedin_url)  # Profile of LinkedIn

        guest=profile_info['response']['full_name']

        event_url="ATL Hackathon"
        # Get profile summary using OpenAI (or another agent)
        agent_response = get_profile_db(profile_info)  # Extract profile summary from the API

        print(profile_info)
        
        # Extract required information from agent_response
        profile_summary = agent_response.profile_user  
        topic = agent_response.topic
        key_words = agent_response.key_words 
        main_topic = agent_response.main_topic  

        profile_picture=None
        try:
            profile_pictrue=profile_info['response']['picture']
        except Exception as e:
            print("[INFO] Error finding the picture")

        flag_image=False
        if profile_pictrue is not None:
            for nCount in range(0,3):
                response_image = requests.get(profile_pictrue , headers=headers)

                # Check if the request was successful
                if response_image.status_code==200:
                    image_base64 = base64.b64encode(response_image.content).decode('utf-8')
                    flag_image=True
                    break

        # Check if the image was successfully downloaded
        if flag_image==False:
            continue

        # Save the extracted information to MongoDB
        mongo_handler.save_text(guest, linkedin_url, image_base64, profile_summary, topic, key_words, main_topic, event_url, collection_type)
        
        # Append the extracted information to the CSV file
        append_to_csv(csv_file, guest, linkedin_url, profile_pictrue, profile_summary, topic, key_words, main_topic, event_url)

        print(f"Processed {guest} successfully!")
        nCount += 1
    except Exception as e:
        print(f"Error processing guest: {e}")
