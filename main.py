import os
from flask import Flask, request, jsonify
from methods.agent_langchain import langChainHandler, langChainHandlerSearch
from methods.agent_scrapper import extract_linkedin_profile
from methods.agent_scrapper import extract_linkedin_profile, clean_linkedin_profile, get_post
from methods.agent_anthropic import get_profile, fit_profile, find_insights, get_profile_db, match_profile_agent, agent_simulation, agent_simulation_chat
import json 
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app) 

# Global dictionary to store session-specific agents
session_agents = {}

# Endpoint to handle langChainHandler requests
@app.route('/langChainHandler', methods=['POST'])
def lang_chain_handler():
    data = request.get_json()
    user_token = data.get("token")
    input_text = data.get("text")

    
    if not user_token or not input_text:
        return jsonify({"error": "Token and text are required"}), 400
    
    config = {"configurable": {"thread_id": str(user_token)}}
    
    if user_token not in session_agents:
        session_agents[user_token] = langChainHandler(user_token, config)
    
    response, profile_user = session_agents[user_token].stream_graph_updates(user_input=input_text)
    return jsonify(
        {
            "response":  {
                "text":response,
                "token":user_token
            },
            "profile_user": profile_user,
        },
    ), 200
    

# Endpoint to handle langChainHandlerSearch requests
@app.route('/langChainHandlerSearch', methods=['POST'])
def lang_chain_handler_search():
    data = request.get_json()
    user_token = data.get("token")
    input_text = data.get("text")
    linkedin_id = data.get("linkedin_id")
    
    if not user_token or not input_text:
        return jsonify({"error": "Token and text are required"}), 400
    
    config = {"configurable": {"thread_id": str(user_token)}}
    
    if user_token not in session_agents:
        session_agents[user_token] = langChainHandlerSearch(user_token, config)
    
    response = session_agents[user_token].stream_graph_updates(user_input=input_text, linkedin_id=linkedin_id)
    return jsonify({"response": response}), 200

# Endpoint to handle langChainHandlerSearch requests
@app.route('/userProfile', methods=['POST'])
def userProfile():
    data = request.get_json()
    linkedin_id = data.get("linkedin_id")

    if not linkedin_id:
        return jsonify({"error": "User profile is required"}), 400
    
    response=extract_linkedin_profile(linkedin_id)
    print(response)
    return jsonify({"response": response}), 200

@app.route('/simulateConversation', methods=['POST'])
def simulate_conversation():
    data = request.get_json()
    linkedin_1 = data.get("linkedin_1")
    linkedin_2 = data.get("linkedin_2")

    if not linkedin_1 or not linkedin_2:
        return jsonify({"error": "Both LinkedIn profiles are required"}), 400
    
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
    
      
    # Generate conversation
    temporal_memory = []
    chat_history = []
    past_context=""
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

            Generate their conversation here as a script in a list, and output in JSON format with “script_items” (list of dicts with “character_1” and “character_2”).
        '''.format(dynamic_profile_linkedin_1=dynamic_profile_linkedin_1, dynamic_profile_linkedin_2=dynamic_profile_linkedin_2, past_context=past_context, current_context=current_context, profile_name_1=profile_name_1, profile_name_2=profile_name_2, detailed_experiences_1=detailed_experiences_1, detailed_experiences_2=detailed_experiences_2)
        
        print("PROMPT WORKING CONVERSATION HERE DYNAMICS ...")
        response=agent_simulation_chat(prompt, temporal_memory)

        response_conversation_json=json.loads(response)
        print("RESPONSE CONVERSATION HERE DYNAMICS ...")
        for i, item in enumerate(response_conversation_json["script_items"]):
            chat_history.append((item['character_1'], item['character_2']))
            time.sleep(5)
            
        response_conversation = "\n".join(f"- {fact}" for fact in response_conversation_json)

        
        temporal_memory.append({
            'user':prompt,
            'assistant':response_conversation
        })
        
        past_context=current_context

    return jsonify({"response": chat_history}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)