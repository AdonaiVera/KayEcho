from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from methods.agent_openai import get_profile_keywords
import requests 

from dotenv import load_dotenv, find_dotenv
import os
import json

_ = load_dotenv(find_dotenv()) 

KEY_LINKEDIN = os.environ['KEY_LINKEDIN']

KEY_LINKEDIN_PROFILE= os.environ['KEY_LINKEDIN']

KEY_LINKEDIN_POST=os.environ['KEY_LINKEDIN_POST']

def scrape_guests_from_event(url):
    # Initialize Safari WebDriver (you can use any driver)
    driver = webdriver.Safari()

    # Open the base page so the driver starts
    driver.get("https://lu.ma")

    # Add login cookies manually (after extracting from your browser)
    cookies = [
        {
            'name': 'luma.auth-session-key', 
            'value': KEY_LINKEDIN_PROFILE, 
            'domain': '.lu.ma',
            'path': '/',
        },
    ]

    for cookie in cookies:
        driver.add_cookie(cookie)

    # Now open the desired page after adding the cookies
    driver.get(url)

    # Wait for the page to load completely
    time.sleep(5)

    # Step 1: Simulate the click on the "257 Guests" button (or similar button for attendees)
    try:
        # Replace with the correct XPath/CSS selector for the "257 Guests" button
        guests_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "guests-button"))
        )
        guests_button.click()
        print("Guests button clicked successfully!")
    except Exception as e:
        print(f"Error clicking the guests button: {e}")
        driver.quit()
        return []

    # Step 2: Wait for the modal that contains the guest list to appear
    try:
        # Wait for the modal that contains the guest list to appear (adjust based on the structure)
        guests_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'flex-center')]"))
        )
        print("Guests modal and list loaded successfully!")
    except Exception as e:
        print(f"Error waiting for the guest list to load: {e}")
        driver.quit()
        return []

    # Wait for the page to load completely
    time.sleep(15)

    # Step 3: Scrape the guest names from the modal
    html = driver.page_source 

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all guest containers (anchor <a> tags that contain the href attribute and names)
    guest_elements = soup.find_all('a', href=True)

    guest_inspection = []
    # Extract guest names and profile links
    if guest_elements:
        for guest in guest_elements:
            # Extract the profile link from the href attribute
            profile_link = guest['href']
            
            # Extract the guest name (inside nested <div> with the class 'name text-ellipses fw-medium')
            name_div = guest.find('div', class_="name text-ellipses fw-medium")
            if name_div:
                guest_name = name_div.text.strip()
                print(f"Guest: {guest_name}, Profile Link: {profile_link}")
                guest_inspection.append({"name": guest_name, "profile_link": profile_link})
    else:
        print("No guest elements found or incorrect class targeted!")

    # Close the browser after scraping
    driver.quit()

    # Return the list of guests with names and profile links
    return guest_inspection


def get_linkedin_from_guest_profile(profile_url):
    # Initialize Safari WebDriver (you can use any driver)
    driver = webdriver.Safari()

    # Open the guest profile page
    driver.get(profile_url)

    # Wait for the page to load completely
    #time.sleep(5)

    # Step 1: Wait for the social links section to load
    try:
        # Wait for the element with class 'social-links' to appear
        social_links = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "social-links"))
        )
        print("Social links section loaded successfully!")
    except Exception as e:
        print(f"Error waiting for the social links to load: {e}")
        driver.quit()
        return None

    # Step 2: Scrape the LinkedIn URL from the social links
    html = driver.page_source

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')


    
    # Find the social links section
    social_links = soup.find_all('div', class_="social-link")
    
    # Initialize variable to store LinkedIn URL
    linkedin_url = None
    
    # Iterate over social links and look for LinkedIn URL
    for link in social_links:
        a_tag = link.find('a', href=True)
        if a_tag and 'linkedin.com' in a_tag['href']:
            linkedin_url = a_tag['href']
            break
    
    # Return the LinkedIn URL if found
    if linkedin_url:
        return linkedin_url
    else:
        return "LinkedIn URL not found."
    
 
def extract_linkedin_profile(linkedin_url):
    try:
        url = "https://api.prospeo.io/linkedin-email-finder"

        required_headers = {
            'Content-Type': 'application/json',
            'X-KEY': KEY_LINKEDIN
        }
        
        data = {
            'url': linkedin_url
        }
        
        response = requests.post(url, json=data, headers=required_headers)
        return response.json()
    except Exception as e:
        print(f"Error fetching LinkedIn profile: {e}")
        return None
    
def clean_linkedin_profile(linkedin_profile):
    print()

    cleaned_docs = []
    linkedin_data=linkedin_profile['response']

    # Job title and summary
    cleaned_docs.append(f"Actual job is {linkedin_data['job_title'] if 'job_title' in linkedin_data else 'Unavailable'}")
    cleaned_docs.append(linkedin_data['summary'] if 'summary' in linkedin_data else 'No summary available')

    # Skills
    skills = linkedin_data['skills'] if 'skills' in linkedin_data else ''
    cleaned_docs.append(f"Sskills are {skills if skills else 'No skills listed'}")

    # Location
    location_data = linkedin_data['location'] if 'location' in linkedin_data else {}
    location_city = location_data['city'] if 'city' in location_data else 'Unknown city'
    location_country = location_data['country'] if 'country' in location_data else 'Unknown country'
    cleaned_docs.append(f"Based in {location_city}, {location_country}")

    # Company
    company_data = linkedin_data['company'] if 'company' in linkedin_data else {}
    company_name = company_data['name'] if 'name' in company_data else 'Unknown company'
    cleaned_docs.append(f"Work at {company_name}")

    detail_experiences_descriptions=[]
    # Education details
    education_details = linkedin_data['education'] if 'education' in linkedin_data else []
    if education_details:
        education_str = "Studied at the following institutions:"
        for edu in education_details:
            school_data = edu['school'] if 'school' in edu else {}
            school_name = school_data['name'] if 'name' in school_data else 'Unknown school'
            degree = edu['degree_name'] if 'degree_name' in edu else 'No degree listed'
            field_of_study = ', '.join(edu['field_of_study']) if 'field_of_study' in edu else 'No field of study listed'
            start_year = edu['date']['start']['year'] if 'date' in edu and 'start' in edu['date'] and 'year' in edu['date']['start'] else 'Unknown start year'
            end_year = edu['date']['end']['year'] if 'date' in edu and 'end' in edu['date'] and 'year' in edu['date']['end'] else 'Unknown end year'
            education_str += f"\n- {school_name}, {degree} in {field_of_study} ({start_year} - {end_year})"
            tempo_education=f"{school_name}, {degree} in {field_of_study} ({start_year} - {end_year})"
            
            # Extract education description if available
            if 'description' in edu:
                detail_experiences_descriptions.append("{} :{}".format(tempo_education, edu['description']))
        
        cleaned_docs.append(education_str)

    # Work experience details
    work_experience_details = linkedin_data['work_experience'] if 'work_experience' in linkedin_data else []
    if work_experience_details:
        work_str = "Work experience includes:"
        for exp in work_experience_details:
            company_data = exp['company'] if 'company' in exp else {}
            company_name = company_data['name'] if 'name' in company_data else 'Unknown company'
            profile_position = exp['profile_positions'][0] if 'profile_positions' in exp and exp['profile_positions'] else {}
            title = profile_position['title'] if 'title' in profile_position else 'No title'
            work_str += f"\n- {title} at {company_name}"

            tempo_work=f"{title} at {company_name}"

            # Extract work experience description if available
            description = profile_position.get('description')
            if description:
                detail_experiences_descriptions.append("{} :{}".format(tempo_work, description))
                detail_experiences_descriptions.append(description)

        cleaned_docs.append(work_str)

    # Languages details
    languages_details = linkedin_data['languages']['supported_locales'] if 'languages' in linkedin_data and 'supported_locales' in linkedin_data['languages'] else []
    if languages_details:
        languages_str = "Speak the following languages:"
        for lang in languages_details:
            language = lang['language'] if 'language' in lang else 'Unknown language'
            country = lang['country'] if 'country' in lang else 'Unknown country'
            languages_str += f"\n- {language} (from {country})"
        cleaned_docs.append(languages_str)

    # Extract keywords of person
    cleaned_docs.append("Personality keys: {}".format(get_profile_keywords(linkedin_data)))


    # Put the cleaned_docs in a string
    linkedin_profile="\n".join(cleaned_docs)
    detail_experiences="\n".join(detail_experiences_descriptions) 
    return linkedin_profile, detail_experiences


def get_post(linkedin_url):
    url = "https://api.scrapin.io/enrichment/activities"

    querystring = {"apikey":KEY_LINKEDIN_POST,"linkedInUrl":linkedin_url}

    nCount=0
    while True:
        try:
            response = requests.request("GET", url, params=querystring)
            
            response_json=json.loads(response.text)
            if response_json["success"]:
                break
        except:
            print("Error in request, trying again")

        time.sleep(5)
        nCount+=1

        if nCount==5:
            print("Not possible to get post information ")
            return "", []
    
    response_json=json.loads(response.text)
    post_list=[]
    for post in response_json["posts"]:
        post_content = f"Text post: {post['text']}, Date post: {post['activityDate']}"
        post_list.append(post_content)

    post_strings="\n".join(post_list) 

    return post_strings, post_list