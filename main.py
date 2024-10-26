from flask import Flask, request, jsonify
import os
from methods.agent_langchain import langChainHandler, langChainHandlerSearch

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

if __name__ == "__main__":
    # Start the Flask server for API endpoints
    app.run(port=5000)
