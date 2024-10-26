import gradio as gr
import os
from methods.agent_langchain import langChainHandler, langChainHandlerSearch
import uuid

# Auth Figures
auth_figures=[("Luis", "FounderFigures"), ("Ado", "FounderFigures")]

# Global dictionary to store active users
active_user = {
    "Luis":"e394cdcd-b6b4-42af-9033-2f648a8e71f3",
    "Ado":"24a8a365-39ab-4da2-bb77-47358c662972"
}

# Global dictionary to store session-specific agents
session_agents = {}

def combined_chat_response(input_text, history, request: gr.Request):
    """Manage chat responses in a combined session."""
    # Assign the founder id
    founder=active_user[request.username]

    config={"configurable": {"thread_id": str(founder)}}

    # Check if the lang_chain_agent is already initialized for this session
    if founder not in session_agents:
        #session_agents[founder] = langChainHandler(founder, config)
        session_agents[founder] = langChainHandlerSearch(founder, config)

    # Get the streaming response from the LangChain handler
    response = session_agents[founder].stream_graph_updates(user_input=input_text, linkedin_id="https://www.linkedin.com/in/adonai-vera/")
    print("FINAL RESPONSE")
    print(response)
    return "xD"
    
"""
ChatInterface
"""
def launch_gradio_interface():
    chatbot = gr.ChatInterface(
        combined_chat_response,
        chatbot=gr.Chatbot(height=500, avatar_images=['figure/user.png', 'figure/sha.png']),
        textbox=gr.Textbox(placeholder="Let's talk", container=False, scale=7),
        title="SHA: Your top 3 coaches combined into one, available for you anytime.",
        description="Coaches are key to success. Access to the best coaches in the world and time spent with them are the main problems to get the most out of coaching. You don't need to be Mark to get advice from Steve, Don, and Peter",
        theme=gr.themes.Soft(primary_hue="orange"),
        retry_btn=None,
        undo_btn="Delete Previous",
        clear_btn="Clear",
    )
    
    chatbot.launch(auth=auth_figures)
    
if __name__ == "__main__":
    # Start the camera processing in a separate thread 
    launch_gradio_interface()