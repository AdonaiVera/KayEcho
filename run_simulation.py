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
    insights_list=list_posts_1[:3]+list_posts_2[:3]

    list_posts_1_prefixed = [f"character_1 post: {post}" for post in list_posts_1]
    list_posts_2_prefixed = [f"character_2 post: {post}" for post in list_posts_2]

    # Combine the first two elements from each list
    insights_list = list_posts_1_prefixed[:2] + list_posts_2_prefixed[:2]

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

        print("Responnse Insights")
        print(respose_insights)
        
#        prompt='''
#            Character 1:{dynamic_profile_linkedin_1}
#            Character 2:{dynamic_profile_linkedin_2}
#
#            Past Context: {past_context}
#
#            Current Context: {current_context}
#
#            Toughts: {respose_insights}
#
#            (This is what is in {profile_name_1}'s head: {detailed_experiences_1} Beyond this, {profile_name_1} doesn't necessarily know anything more about {profile_name_2}!) 
#
#            (This is what is in {profile_name_2}'s head: {detailed_experiences_2} Beyond this, {profile_name_2} doesn't necessarily know anything more about {profile_name_1}!) 
#
#            Generate their conversation here as a script in a list, and output in JSON format with “script_items” (list of dicts with “character_1” and “character_2”).
#        '''.format(dynamic_profile_linkedin_1=dynamic_profile_linkedin_1, dynamic_profile_linkedin_2=dynamic_profile_linkedin_2, past_context=past_context, current_context=current_context, profile_name_1=profile_name_1, profile_name_2=profile_name_2, detailed_experiences_1=detailed_experiences_1, detailed_experiences_2=detailed_experiences_2, respose_insights=respose_insights)
        
        prompt = '''
            Characters:
            - {profile_name_1}: {dynamic_profile_linkedin_1}
            - {profile_name_2}: {dynamic_profile_linkedin_2}

            **Past Context**: {past_context}

            **Current Context**: {current_context}

            **Insights**: {respose_insights}

            **Internal Monologues**:
            - {profile_name_1} knows this about {profile_name_2}: {detailed_experiences_2}. Beyond this, {profile_name_1} has limited knowledge of {profile_name_2}.
            - {profile_name_2} knows this about {profile_name_1}: {detailed_experiences_1}. Beyond this, {profile_name_2} has limited knowledge of {profile_name_1}.

            **Objective**: Generate a conversation between {profile_name_1} and {profile_name_2} that starts casually and then progressively dives deeper into personal and professional insights. Each character should respond thoughtfully and build on the other’s responses, naturally encouraging open-ended, intelligent questions to uncover common ground, values, and motivations.

            **Output Requirements**:
            - Format as a JSON object with a list called “script_items.”
            - Each list item is a dictionary with “character_1” (speaking {profile_name_1}) and “character_2” (speaking {profile_name_2}).

            **Script Style**:
            - Start the conversation lightly, with introductory or general questions.
            - Gradually deepen the conversation, weaving in curiosity and uncovering meaningful insights.
            - Maintain a friendly, engaging tone throughout, allowing questions to feel intuitive and authentic.

            Example Structure:
            - [Character 1] Initial greeting or light question.
            - [Character 2] Response, with a follow-up question that adds depth.
            - Continue, progressively exploring new layers of interests, experiences, and professional insights in each exchange.
        '''.format(
            dynamic_profile_linkedin_1=dynamic_profile_linkedin_1, 
            dynamic_profile_linkedin_2=dynamic_profile_linkedin_2, 
            past_context=past_context, 
            current_context=current_context, 
            profile_name_1=profile_name_1, 
            profile_name_2=profile_name_2, 
            detailed_experiences_1=detailed_experiences_1, 
            detailed_experiences_2=detailed_experiences_2, 
            respose_insights=respose_insights
        )

        print("PROMPT WORKING CONVERSATION HERE DYNAMICS ...")
        response=agent_simulation_chat(prompt, temporal_memory, gpt_param)

        print("new responsex")
        print(response)

        response_conversation_json=json.loads(response)
        print("RESPONSE CONVERSATION HERE DYNAMICS ...")
        response_conversation=""
        for i, item in enumerate(response_conversation_json["script_items"]):
            print(item)
            print(f"Left (Character 1): {item['character_1']}")
            print(f"Right (Character 2): {item['character_2']}\n")

            chat_history.append((item['character_1'], None))
            yield chat_history, ""
            time.sleep(2)
            chat_history.append((None, item['character_2']))
            yield chat_history, ""
            time.sleep(2)
            response_conversation+=f"{item['character_1']}\n{item['character_2']}\n"

        temporal_memory.append({
            'user':prompt,
            'assistant':response_conversation
        })

        print("This is what I have to save it")
        print(response_conversation)

        # First Perspective 
        prompt='''
            Here is the conversation that happened between {profile_name_1} and {profile_name_2}. 
            {response_conversation}

            Summarize what {profile_name_1} thought about {profile_name_2} in one short sentence. The sentence needs to be in third person:
        '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        print("This is the prompt that we need")
        print(prompt)
        response_summarize=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_summarize)

        # WE SHOULD DO THIS WITH THE STATEMENTS -> TEMPORAL DO IT WITH THE CONVERSATION
        prompt='''
            [Conversation]
            {response_conversation}

            Write down if there is anything from the conversation that {profile_name_1} might have found interesting from {profile_name_2}'s perspective, in a full sentence. 

            {profile_name_1}          
            '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_interesting=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_interesting)

        # Other perspective
        prompt='''
            Here is the conversation that happened between {profile_name_2} and {profile_name_1}. 
            {response_conversation}

            Summarize what {profile_name_2} thought about {profile_name_1} in one short sentence. The sentence needs to be in third person:
        '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_summarize=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_summarize)

        # WE SHOULD DO THIS WITH THE STATEMENTS -> TEMPORAL DO IT WITH THE CONVERSATION
        prompt='''
            [Conversation]
            {response_conversation}

            Write down if there is anything from the conversation that {profile_name_2} might have found interesting from {profile_name_1}'s perspective, in a full sentence. 

            {profile_name_1}          
            '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_interesting=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_interesting)

        respose_insights_response="\n".join(respose_insights)

        yield chat_history, respose_insights_response
            
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
    