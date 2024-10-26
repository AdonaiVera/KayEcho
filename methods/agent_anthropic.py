import anthropic
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os

_ = load_dotenv(find_dotenv())

# Set up your API keys
mongo_uri = os.environ['MONGO_URI']
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
model="claude-3-5-sonnet-20241022" 

anthropic_client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
)

# Define the model for structured responses
class InformationProfile(BaseModel):
    profile_user: str
    topic: str
    key_words: str  
    main_topic: str

def get_profile_db(profile_user):
    system_context = (
        """You are an assistant designed to summarize professional profiles and extract relevant research topics based on provided data. Follow a step-by-step reasoning process to ensure the accuracy and completeness of your output. Below is the user's information:
        
        {}

        Follow these steps to generate your response:
        1. Analyze the user's information to understand their background, expertise, and main areas of work.
        2. Summarize the user's professional profile in a clear and concise manner.
        3. Identify and suggest key areas of work or research interests based on the user's profile.
        4. Highlight specific key words that represent the user's main topics of interest.
        5. Categorize the main topics of work or research based on predefined fields (e.g., artificial_intelligence, reasoning, engineer, research).

        Output:
        profile_user: str -> Summary of the user's professional profile
        topic: str -> Main area of work or research interest
        key_words: str -> Keywords representing important concepts in the user's profile
        main_topic: str -> Global category of the user's main area of work or research

        Use a step-by-step approach to ensure the information is extracted accurately and comprehensively.
        """.format(str(profile_user))
    )
    
    messages = [
        {
            "role": "system",
            "content": system_context
        }
    ]

    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )

    return message.content

def agent_simulation(prompt, gpt_parameter):
    '''
    response = anthropic_client.completion.create(
        model=model,
        prompt=prompt,
        temperature=gpt_parameter["temperature"],
        max_tokens_to_sample=gpt_parameter["max_tokens"],
        top_p=gpt_parameter["top_p"],
        frequency_penalty=gpt_parameter["frequency_penalty"],
        presence_penalty=gpt_parameter["presence_penalty"],
        stream=gpt_parameter["stream"]
    )
    '''
    
    messages=[{
        "role": "user",
        "content": prompt
    }]

    
    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )
    
    return message.content

class ScriptConversation(BaseModel):
    script: list[str]

def agent_simulation_chat(prompt, temporal_memory, gpt_parameter=None):
    messages = []

    for memory in temporal_memory:
        messages.append({
            "role": "user",
            "content": memory['user']
        })
        messages.append({
            "role": "assistant",
            "content": memory['assistant']
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    message = anthropic_client.messages.create(
        model=model,
        max_tokens=4096,
        messages=messages
    )
   
    return message.content[0].text

def find_insights(conversation, model=model):
    system_context = (
        """You are an intelligent assistant designed to extract deep, tailored insights from a conversation between two individuals based on their profiles and dialogue. Your goal is to highlight the unique, non-generic connections and areas of synergy between the two individuals.

        Below is the conversation between the two users:
        
        {}

        Follow these steps to generate insights:

        Step 1: Analyze the Conversation in Detail
        - Thoroughly examine the topics discussed, focusing on specific experiences, industries, and expertise shared.
        - Detect areas of overlap or mutual interest that go beyond the obvious or generic.
        - Pay special attention to nuanced themes, including professional goals, personal values, work ethics, and leadership approaches.
        - Identify complementary skills or expertise that could foster collaboration between the two individuals.

        Step 2: Extract Unique and Tailored Insights
        - Extract insights based on both professional and personal experiences discussed in the conversation.
        - Highlight unique accomplishments, niche areas of expertise, or specialized knowledge that could create synergy between the users.
        - Identify shared challenges or opportunities where one individual’s skills or background can support the other.
        - Look for non-obvious connections, such as similar career trajectories, shared mentors, or innovative approaches to solving problems.

        Step 3: Summarize Tailored Insights from the Conversation
        - Create a concise, tailored list of key insights, emphasizing the unique connections, complementary skills, and specific collaboration opportunities.
        - Each insight should be a direct reflection of the actual conversation, avoiding generic statements. Focus on detailed aspects such as specific technologies, industries, or achievements.

        Output: Return a list of highly tailored insights based on the conversation.
        """.format(str(conversation))
    )

    messages = [
        {
            "role": "user",
            "content": system_context,
        }
    ]

    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )
    
    return message.content

def match_profile_agent(profile_founder, profile_vc, model=model):
    system_context = (
        """You are a highly skilled assistant focused on creating the best match between a founder and a venture capitalist (VC).
        
        Your task is to deeply analyze both profiles and return a clean, actionable list of what they share in common, helping to establish a strong connection. 

        The goal is to match them in areas like work, research, hobbies, sports, personal life, or anything that aligns their interests and potential collaboration.

        Below are the profiles:
        
        Profile Founder: {}
        Profile Venture Capitalist: {}

        Follow these steps to generate a detailed connection:

        Step 1: Analyze Individual Profiles
        - Examine both profiles for key elements: professional background, skills, industries, interests, research fields, hobbies, personal life aspects (e.g., sports, family, values).
        - Detect any overlapping experiences or common goals, including education, career milestones, or shared challenges.

        Step 2: Compare Profiles
        - Identify similarities between their professional journeys (industries, sectors, career levels).
        - Look for shared research areas, common sporting interests, or personal hobbies.
        - Highlight areas where their skills, expertise, or values align or complement each other.

        Step 3: Chain of Thought Reasoning for Deeper Insights
        - Use step-by-step reasoning to detect subtle or non-obvious connections (e.g., founder's challenge that matches VC's previous investments).
        - Explore synergies based on complementary strengths (e.g., founder excels in product development, VC in scaling businesses).
        - Analyze how their networks, business philosophies, or personal interests might intersect for potential collaboration.

        Step 4: Generate a Clean, Actionable List
        - Provide a list of connections, from most direct to indirect.
        - The list should be simple, clear, and actionable, highlighting specific areas they share.
        """.format(str(profile_founder), str(profile_vc))
    )

    messages = [
        {
            "role": "system",
            "content": system_context,
        }
    ]

    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )
    
    return message.content

def get_profile_keywords(profile_user, model=model):
    system_context = (
        """
        I need to extract the personality of this person in 5 words.
        Below is the user's information:
    
        {}
        """.format(str(profile_user))
    )

    messages = [
        {
            "role": "user",
            "content": system_context,
        }
    ]

    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )
    
    return message.content

def get_profile(profile_user, model=model):
    system_context = (
        """You are an intelligent assistant designed to create a dynamic digital replica of a person, based on the provided user profile information. Your task is to carefully analyze and summarize their identity, professional background, and communication style.

        Below is the user's information:
        
        {}

        Follow these steps to generate the user's digital profile:

        Step 1: Analyze Background and Expertise
        - Identify the user's main areas of expertise, professional experiences, and key accomplishments.
        - Extract relevant details from their education, work experience, skills, and areas of specialization.
        - Pay attention to any industries, companies, or roles that reflect the user's expertise.

        Step 2: Summarize Professional Profile
        - Concisely summarize the user's professional background, highlighting their expertise, industries, and career progression.
        - Ensure the summary captures key aspects of their work and professional identity.

        Step 3: Capture the User's Voice and Identity
        - Based on their background, infer the user's communication style, tone, and identity voice.
        - Consider how the user might present themselves in conversations, and their unique qualities (e.g., formal, visionary, technical, friendly).
        - Create a sentence that encapsulates the user's identity and communication style in the digital profile.

        Output: Generate a dynamic and concise representation of the user.
        """.format(str(profile_user))
    )

    messages = [
        {
            "role": "user",
            "content": system_context,
        }
    ]

    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )
    
    return message.content

class MatchProfile(BaseModel):
    match: str
    intro: str
    profile_agent: str

def fit_profile(search, profile_expected):
    system_context = """
    **search:** {search}

    **Expected Match Profile:** {profile_expected}

    ---

    **Your Task:** Provide two outputs by following these reasoning steps:

    ### Step 1: Analyze the Match
    - Compare the key attributes of the search and the profile (skills, interests, experiences).
    - Identify the common ground or complementing traits that make them a good match.

    ### Step 2: Generate a Short Explanation
    - Based on your analysis, write a concise explanation (1-2 sentences) of why these profiles are a good match.

    ### Step 3: Brainstorm an Intro Topic
    - Think about what topics or mutual interests could spark an engaging conversation.
    - Consider the expected match’s profile and what might resonate with them.

    ### Step 4: Write the main topic in common
    - Craft the last experience that can be used to start the conversation (Go to the most detailed possible.)

    ### Step 5: Create a profile of the agent
    - Based on the profile expected, generate a comprehensive profile for the agent, only use the profile information. The profile should include the agent's name, areas of expertise, and key strengths. Structure it in a way that reads naturally and provides context to the agent’s capabilities.
    Example: "You are Alex, an expert in artificial intelligence, data analysis, and machine learning. With extensive experience in predictive modeling and automation, you specialize in providing innovative solutions to complex data-driven challenges. Your strengths include strategic thinking, problem-solving, and technical leadership, enabling you to deliver actionable insights and guide businesses toward data-driven decision-making."

    **Outputs:**
    1. match: **Why This is a Good Match:** 
    2. intro: **Taking point detailled (Be more specific possible) to Start a Conversation:**'
    3. profile_agent: **Profile of the agent:**'
    """.format(search=search, profile_expected=profile_expected)

    messages = [
        {
            "role": "system",
            "content": system_context,
        }
    ]

    message = anthropic_client.messages.create(
        model=model,
        max_tokens=1024,
        messages=messages
    )
    
    return message.content
