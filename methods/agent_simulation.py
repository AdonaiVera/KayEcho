import gradio as gr
from methods.agent_mongo import MongoDBHandler
from methods.agent_anthropic import get_profile, fit_profile, find_insights, get_profile_db, match_profile_agent, agent_simulation, agent_simulation_chat

import json
import requests
import base64
import os 
from io import BytesIO
from PIL import Image
import time
from dotenv import load_dotenv, find_dotenv
from methods.agent_llama_index import graphAgent
import uuid

from methods.agent_scrapper import extract_linkedin_profile, clean_linkedin_profile, get_post

collection_type="user_profile"
_ = load_dotenv(find_dotenv()) 

mongo_uri = os.environ['MONGO_URI'] 
openai_api_key= os.environ['OPENAI_API_KEY']

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

mongo_handler = MongoDBHandler(mongo_uri, openai_api_key)

gpt_param = {"engine": "gpt-3.5-turbo-instruct", "max_tokens": 2300, 
            "temperature": 0.8, "top_p": 1, "stream": False,
            "frequency_penalty": 0, "presence_penalty": 0, "stop": [""]}

# Define the function to simulate the chat
def simulate_chat(linkedin_1, linkedin_2, chat_history):
    # Ensure chat_history is initialized
    if chat_history is None:
        chat_history = []

    dynamic_profile_linkedin_1_base = extract_linkedin_profile(linkedin_1)
    dynamic_profile_linkedin_1, detailed_experiences_1 = clean_linkedin_profile(dynamic_profile_linkedin_1_base)
    dynamic_profile_1=get_profile(dynamic_profile_linkedin_1)

    dynamic_profile_linkedin_2_base = extract_linkedin_profile(linkedin_2)
    dynamic_profile_linkedin_2, detailed_experiences_2 = clean_linkedin_profile(dynamic_profile_linkedin_2_base)
    dynamic_profile_2=get_profile(dynamic_profile_linkedin_2)

    post_result_1, list_posts_1=get_post(linkedin_1)
    post_result_2, list_posts_2=get_post(linkedin_2)

    print("Check the profile that we extracted here: ")
    print(dynamic_profile_linkedin_1)

    print("Check the detailed from the user profile 1: ")
    print(detailed_experiences_1)

    print("Check the detailed from the user profile 2: ")
    print(detailed_experiences_2)

    profile_name_1=dynamic_profile_linkedin_1_base['response']['full_name']
    profile_name_2=dynamic_profile_linkedin_2_base['response']['full_name']

    # Simulate autonomous loop with the common topics
    insights_list=[]

    # Add the first two insights from the posts
    insights_list=list_posts_1[:2]+list_posts_2[:2]

    # Improve the way that we introduce the past context
    if not insights_list:
        print("No insights found.")
        topic_discussion=f"Hi, Lets talk about your most successfull story and what is the most exciting thing you have done in this area?"
    else:
        topic_discussion=[f"I saw that {insight}, let's discuss about that." for insight in insights_list]
    
    temporal_memory=[]    
    past_context=""

    respose_insights=[]
    for current_context in topic_discussion:
        print("current context")
        print(current_context)
        prompt='''
            Character 1:{dynamic_profile_linkedin_1}
            Character 2:{dynamic_profile_linkedin_2}

            Past Context: {past_context}

            Current Context: {current_context}

            (This is what is in {profile_name_1}'s head: {detailed_experiences_1} Beyond this, {profile_name_1} doesn't necessarily know anything more about {profile_name_2}!) 

            (This is what is in {profile_name_2}'s head: {detailed_experiences_2} Beyond this, {profile_name_2} doesn't necessarily know anything more about {profile_name_1}!) 

            Generate their conversation here as a script in a list, where each element of the list is a message from one of the characters. 
        '''.format(dynamic_profile_linkedin_1=dynamic_profile_linkedin_1, dynamic_profile_linkedin_2=dynamic_profile_linkedin_2, past_context=past_context, current_context=current_context, profile_name_1=profile_name_1, profile_name_2=profile_name_2, detailed_experiences_1=detailed_experiences_1, detailed_experiences_2=detailed_experiences_2)
        
        print("PROMPT WORKING CONVERSATION HERE DYNAMICS ...")
        response_conversation_json=agent_simulation_chat(prompt, temporal_memory, gpt_param)

        print("RESPONSE CONVERSATION HERE DYNAMICS ...")
        print(response_conversation_json)
        print(type(response_conversation_json))
        
        for nCount in range(0, len(response_conversation_json)-1, 2):
            print(response_conversation_json[nCount])
            chat_history.append((response_conversation_json[nCount], None))
            yield chat_history, ""
            time.sleep(2)
            chat_history.append((None, response_conversation_json[nCount+1]))
            yield chat_history, ""
            time.sleep(2)
            

        response_conversation = "\n".join(f"- {fact}" for fact in response_conversation_json)

        temporal_memory.append({
            'user':prompt,
            'assistant':response_conversation
        })


        #respose_insights_response="\n".join(respose_insights)

        yield chat_history, ""
            


            
# Create Gradio interface
with gr.Blocks(css=".title {color: white; text-align: center; background-color: #007BFF; padding: 10px; border-radius: 5px;}") as demo:
    # Page Title with Styling
    gr.Markdown("<h1 class='title'>🌟 VC Finder App 🌟</h1>")

    # Add your VC linkedIn profile
    linkedin_user = gr.Textbox(label="Enter your LinkedIn profile")
    # Add your VC linkedIn profile
    linkedin_vc = gr.Textbox(label="Enter your VC profile")
    
    # Generate Button
    generate_btn = gr.Button("🔮 Spark the Connection 🔮", elem_id="generate_button")

    # Simulated chat section
    with gr.Row():
        with gr.Column():
            gr.Markdown("<h3 style='text-align: center;'>💬 Simulated Chat</h3>")
            chatbox = gr.Chatbot(label="Pro-Network DJ", avatar_images=['figure/user.png', 'figure/sha.png'])


    # Define the action when the button is clicked
    final_insights_textbox = gr.Textbox(label="Final Insights", placeholder="Insights will be displayed here after the chat.")

    # Define the action when the button is clicked
    generate_btn.click(fn=simulate_chat, 
                       inputs=[linkedin_user, linkedin_vc], 
                       outputs=[chatbox, final_insights_textbox])
    
# Launch the app
demo.launch(share=True)
    