import gradio as gr
from methods.agent_mongo import MongoDBHandler
from methods.agent_openai import get_profile, fit_profile, find_insights, get_profile_db, match_profile_agent, agent_simulation, agent_simulation_chat
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


# Sample function to generate three responses
def generate_responses(linked_user, linked_vc):
    linkedin_profile=[linked_user, linked_vc]

    # Generate responses for each profile
    responses=[]
    nCount=0
    match_profile=[]
    for profile in linkedin_profile:
        # Fetch dynamic profile from LinkedIn 
        profile_info = extract_linkedin_profile(profile)

        # Save the profile to MongoDB        
        match_profile.append(profile_info)

        # Get profile summary using OpenAI (or another agent)
        agent_response = get_profile_db(profile_info)  # Extract profile summary from the API

        # Extract required information from agent_response
        profile_summary = agent_response.profile_user  
        topic = agent_response.topic
        key_words = agent_response.key_words 

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
                if response_image.status_code == 200:
                    # Open image using PIL directly
                    image = Image.open(BytesIO(response_image.content))
                    flag_image = True
                    break
                    

        if flag_image==False:
            image=Image.open("figure/sha.png")

        responses.append({
            "name": profile_info['response']['full_name'],
            "description": profile_summary,
            "topic": topic,
            "key_words": key_words,
            "linkedin": profile,
            "image": image,
        })

    # Do the match in a manual process (Only prompting with CoT)
    agent_response = match_profile_agent(match_profile[0], match_profile[1])

    # Return all 16 values separately for Gradio output
    return (
        responses[0]["image"], responses[0]["name"], responses[0]["description"], responses[0]["topic"], responses[0]["key_words"], responses[0]["linkedin"],
        responses[1]["image"], responses[1]["name"], responses[1]["description"], responses[1]["topic"], responses[1]["key_words"], responses[1]["linkedin"], 
        agent_response, True
    )

def simulate_chat(linkedin_1, linkedin_2, insights_string, chat_history):
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
    insights_list = [insight.strip() for insight in insights_string.splitlines() if insight.strip()]

    # Add the first two insights from the posts
    #insights_list=list_posts_1[:2]+list_posts_2[:2]+insights_list[:2]
    insights_list=list_posts_1[:3]+list_posts_2[:3]

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
        
        
        for nCount in range(0, len(response_conversation_json.script)-1, 2):
            chat_history.append((response_conversation_json.script[nCount], None))
            yield chat_history, ""
            time.sleep(2)
            chat_history.append((None, response_conversation_json.script[nCount+1]))
            yield chat_history, ""
            time.sleep(2)
            

        response_conversation = "\n".join(f"- {fact}" for fact in response_conversation_json.script)

        temporal_memory.append({
            'user':prompt,
            'assistant':response_conversation
        })

        prompt='''
            Here is the conversation that happened between {profile_name_1} and {profile_name_2}. 
            {response_conversation}

            Summarize what {profile_name_1} thought about {profile_name_2} in one short sentence. The sentence needs to be in third person:
        '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
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

        prompt='''
            [Conversation]
            {response_conversation}

            Currently: {profile_name_1}

            Summarize the most relevant statements above that can inform {profile_name_1} in his conversation with {profile_name_2}.
     
            '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_interesting=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_interesting)


        prompt='''
            [Conversation]
            {response_conversation}


            Based on the statements above, summarize {profile_name_1} and {profile_name_2}'s relationship. What do they feel or know about each other?        
            '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_interesting=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_interesting)

        # Pending to add summarize chat ideas.
        # Pending to keywords to thoughts.

        # I'm sending the main topic but here could be the summarize
        past_context=current_context

        respose_insights_response="\n".join(respose_insights)

        yield chat_history, respose_insights_response
            
# Enable simulate_btn based on flag
def update_simulate_btn(flag_value):
    return gr.update(interactive=flag_value)

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

    # Displaying the results in columns with improved styling
    with gr.Row():
        with gr.Column():
            gr.Markdown("<h3 style='text-align: center;'>🔍 Expert 1</h3>")
            img_1 = gr.Image(label="Image 1")
            name_1 = gr.Textbox(label="Name 1")
            desc_1 = gr.Textbox(label="Description 1")
            match_1 = gr.Textbox(label="Topics")
            intro_1 = gr.Textbox(label="Key Words")
            linkedin_1 = gr.Textbox(label="LinkedIn Profile")
        
        with gr.Column():
            gr.Markdown("<h3 style='text-align: center;'>🔍 Expert 2</h3>")
            img_2 = gr.Image(label="Image 2")
            name_2 = gr.Textbox(label="Name 2")
            desc_2 = gr.Textbox(label="Description 2")
            match_2 = gr.Textbox(label="Topics")
            intro_2 = gr.Textbox(label="Key Words")
            linkedin_2 = gr.Textbox(label="LinkedIn Profile")

    final_insights_match = gr.Textbox(label="Final Insights Match", placeholder="Insights will be displayed here after the match.")

    # Define a flag for button enablement
    flag = gr.State(value=False)

    # Button to start the autonomous simulation
    simulate_btn = gr.Button("Start Simulated Chat 🚀", interactive=False)

    
    # Simulated chat section
    with gr.Row():
        with gr.Column():
            gr.Markdown("<h3 style='text-align: center;'>💬 Simulated Chat</h3>")
            chatbox = gr.Chatbot(label="Pro-Network DJ", avatar_images=['figure/user.png', 'figure/sha.png'])

    
    # Define the action when the button is clicked
    generate_btn.click(fn=generate_responses, 
                       inputs=[linkedin_user, linkedin_vc], 
                       outputs=[img_1, name_1, desc_1, match_1, intro_1, linkedin_1, 
                                img_2, name_2, desc_2, match_2, intro_2, linkedin_2, final_insights_match, flag])
    
    # Define the action when the button is clicked
    final_insights_textbox = gr.Textbox(label="Final Insights", placeholder="Insights will be displayed here after the chat.")

    # Automatically check the flag after the `generate_btn` click and update the interactivity of `simulate_btn`
    flag.change(fn=update_simulate_btn, 
                inputs=[flag], 
                outputs=simulate_btn)

    # Here we have to add the text inputs to the simulate_chat function
    simulate_btn.click(fn=simulate_chat,
        inputs=[linkedin_user, linkedin_vc, final_insights_match], 
        outputs=[chatbox, final_insights_textbox])

# Launch the app
demo.launch(share=True)
    