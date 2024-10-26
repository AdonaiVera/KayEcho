import os
from flask import Flask, request, jsonify
from methods.agent_langchain import langChainHandler, langChainHandlerSearch
from methods.agent_scrapper import extract_linkedin_profile
from methods.agent_scrapper import extract_linkedin_profile, clean_linkedin_profile, get_post
from methods.agent_anthropic import get_profile, fit_profile, find_insights, get_profile_db, match_profile_agent, agent_simulation, agent_simulation_chat
import json 
from flask_cors import CORS

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
    
    response = session_agents[user_token].stream_graph_updates(user_input=input_text)
    return jsonify({"response": response}), 200

# Endpoint to handle langChainHandlerSearch requests
@app.route('/langChainHandlerSearch', methods=['POST'])
def lang_chain_handler_search():
    data = request.get_json()
    user_token = data.get("token")
    input_text = data.get("text")
    
    if not user_token or not input_text:
        return jsonify({"error": "Token and text are required"}), 400
    
    config = {"configurable": {"thread_id": str(user_token)}}
    
    if user_token not in session_agents:
        session_agents[user_token] = langChainHandlerSearch(user_token, config)
    
    response, profile_user = session_agents[user_token].stream_graph_updates(user_input=input_text)
    return jsonify(
        {
            "response":  {
                "text": response,
                "token":user_token
            },
            "profile_user": profile_user,
        },
    ), 200

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
    
    # Retrieve and process LinkedIn profiles
    dynamic_profile_1, detailed_experiences_1 = clean_linkedin_profile(extract_linkedin_profile(linkedin_1))
    dynamic_profile_2, detailed_experiences_2 = clean_linkedin_profile(extract_linkedin_profile(linkedin_2))
    profile_name_1 = dynamic_profile_1['response']['full_name']
    profile_name_2 = dynamic_profile_2['response']['full_name']

    # Retrieve recent posts and insights
    post_result_1, list_posts_1 = get_post(linkedin_1)
    post_result_2, list_posts_2 = get_post(linkedin_2)
    insights_list = list_posts_1[:2] + list_posts_2[:2]
    topic_discussion = [f"I saw that {insight}, let's discuss about that." for insight in insights_list] or [
        "Hi, let's talk about your most successful story and what is the most exciting thing you've done in this area?"
    ]

    # Generate conversation
    temporal_memory = []
    chat_history = []
    for current_context in topic_discussion:
        prompt = f'''
            Character 1: {dynamic_profile_1}
            Character 2: {dynamic_profile_2}
            Past Context: {temporal_memory}
            Current Context: {current_context}
            (This is what {profile_name_1} knows about {profile_name_2} and vice-versa.)
            Generate their conversation as a list in JSON format with “script_items” (list of dicts with “character_1” and “character_2”).
        '''
        response = agent_simulation_chat(prompt, temporal_memory)
        response_conversation_json = json.loads(response)

        # Append conversation items to chat history and temporal memory
        for item in response_conversation_json["script_items"]:
            chat_history.append((item['character_1'], item['character_2']))
            temporal_memory.append({
                'user': prompt,
                'assistant': json.dumps(item)
            })

    return jsonify({"response": chat_history}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)