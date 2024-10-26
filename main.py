import os
from flask import Flask, request, jsonify
from methods.agent_langchain import langChainHandler, langChainHandlerSearch
from methods.agent_scrapper import extract_linkedin_profile
app = Flask(__name__)

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
    
    response = session_agents[user_token].stream_graph_updates(user_input=input_text)
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)