import openai
from openai import OpenAI
from pydantic import BaseModel

from dotenv import load_dotenv, find_dotenv
import os

_ = load_dotenv(find_dotenv()) 

mongo_uri = os.environ['MONGO_URI'] 
API_KEY= os.environ['OPENAI_API_KEY']
model = "gpt-4o" 

open_ai_client = OpenAI(api_key=API_KEY)

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
    

    messages=[
        {
            "role": "system",
            "content": [
                {
                "type": "text",
                "text": system_context
                }
            ]
        }
    ] 
    
    # Make the API call with structured output
    completion = open_ai_client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=InformationProfile,
    )

    # Extract the structured output
    return completion.choices[0].message.parsed

def agent_simulation(prompt, gpt_parameter):
    """
    Call OpenAI API to generate a response based on a given prompt.
    """
    response = openai.completions.create(
        model=gpt_parameter["engine"],
        prompt=prompt,
        temperature=gpt_parameter["temperature"],
        max_tokens=gpt_parameter["max_tokens"],
        top_p=gpt_parameter["top_p"],
        frequency_penalty=gpt_parameter["frequency_penalty"],
        presence_penalty=gpt_parameter["presence_penalty"],
        stream=gpt_parameter["stream"],
        #stop=gpt_parameter["stop"],
        )
    
    print("here response")
    print(response)
    return response.choices[0].text


class ScriptConversation(BaseModel):
    script: list[str]

def agent_simulation_chat(prompt, temporal_memory, gpt_parameter):
    """
    Call OpenAI API to generate a response based on a given prompt.
    """

    messages=[]

    for memory in temporal_memory:
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text":  memory['user']
                }
            ]
        })

        messages.append({
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": memory['assistant']
                }
            ]
        })

    messages.append({
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": prompt
            }
        ]
    })


    completion = open_ai_client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=ScriptConversation,
        max_tokens=16384,
        top_p=gpt_parameter["top_p"],
        frequency_penalty=gpt_parameter["frequency_penalty"],
        presence_penalty=gpt_parameter["presence_penalty"],
        temperature=gpt_parameter["temperature"],
    )

    # Extract the structured output
    extracted_facts = completion.choices[0].message.parsed

    return extracted_facts

def agent_simulation_chat__(prompt, temporal_memory, gpt_parameter):
    """
    Call OpenAI API to generate a response based on a given prompt.
    """

    messages=[]

    for memory in temporal_memory:
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text":  memory['user']
                }
            ]
        })

        messages.append({
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": memory['assistant']
                }
            ]
        })

    messages.append({
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": prompt
            }
        ]
    })


    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=gpt_parameter["temperature"],
        max_tokens=16384,
        top_p=gpt_parameter["top_p"],
        frequency_penalty=gpt_parameter["frequency_penalty"],
        presence_penalty=gpt_parameter["presence_penalty"],
        stream=gpt_parameter["stream"],
        response_format={ "type": "json_object" }
        #stop=gpt_parameter["stop"],
        )
    
    return response.choices[0].message.content

def find_insights(conversation, model=model):
    """
    Call OpenAI API to check if there is enough information about the user to suggest mentors.
    """
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
        
        Example Output:
        - "Both individuals are experts in AI, with the founder developing machine learning models for autonomous drones, and the VC having a track record of investing in defense startups, specifically in drone technology."
        - "Both users share a passion for sustainable technology, with the founder exploring carbon-neutral blockchain solutions and the VC funding renewable energy startups."
        - "They have complementary experience in scaling tech businesses—while the founder focuses on product innovation and patenting new algorithms, the VC has successfully led multiple startups through IPO."
        - "Both users have worked with leading figures in the industry, with the founder collaborating with Elon Musk on AI ethics initiatives, and the VC having a close working relationship with Peter Thiel in tech ventures."
        - "The founder's interest in virtual reality aligns with the VC's investment in metaverse-related startups, creating an opportunity for joint exploration in immersive tech."
        - "Both users share similar leadership philosophies, with the founder promoting remote-first teams, and the VC advocating for decentralized, global talent networks."

        Only return the output as a list of tailored insights, no additional explanation or text is needed.
        """.format(str(conversation))
    )

    response = open_ai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": system_context,
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content

def match_profile_agent(profile_founder, profile_vc, model=model):
    """
    Call OpenAI API to analyze the profiles of a founder and a VC, identifying connections in research, work, personal life, sports, and more.
    """
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

        Example Output:
        - "Both individuals have a background in AI, with the founder working on AI-driven healthcare solutions using TensorFlow, and the VC having previously invested in DeepMind’s machine learning ventures."
        - "They share a passion for sustainability, with the founder focusing on eco-friendly product design at Tesla, and the VC actively involved in funding green technology startups like Beyond Meat."
        - "Both are avid marathon runners and have participated in the Boston Marathon, supporting charity initiatives for the World Wildlife Fund (WWF)."
        - "The founder’s experience in scaling SaaS businesses, having led growth at Slack, aligns with the VC's expertise in supporting early-stage tech companies like Stripe to achieve rapid growth."
        - "Both are alumni of Stanford University and have participated in entrepreneurial mentorship programs alongside leaders like Peter Thiel and Marc Andreessen."
        - "They share a keen interest in blockchain technology, with the founder integrating Ethereum-based smart contracts into their business model, and the VC having made significant investments in Coinbase and Chainlink."
        - "The founder’s focus on product innovation, having developed cutting-edge solutions at SpaceX, complements the VC's track record of guiding companies like Uber and Airbnb through successful mergers and acquisitions."
        
        Only return the output as a list of shared interests or potential connections, no explanations or additional text needed.
        """.format(str(profile_founder), str(profile_vc))
    )

    response = open_ai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_context,
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content



def get_profile_keywords(profile_user, model=model):
    """
    Call OpenAI API to check if there is enough information about the user to suggest mentors.
    """
    system_context = (
        """
        I need to extract the personality of this person in 5 words.
        Below is the user's information:
    
        {}
        """.format(str(profile_user))
    )

    response = open_ai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": system_context,
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content

def get_profile(profile_user, model=model):
    """
    Call OpenAI API to check if there is enough information about the user to suggest mentors.
    """
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
        
        Example Output:
        - "You are Ado, a visionary entrepreneur with a technical background, known for your innovative thinking and concise, strategic communication style."
        
        Only return the output as a string.
        """.format(str(profile_user))
    )

    response = open_ai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": system_context,
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


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

    messages=[
        {
            "role": "system",
            "content": [
                {
                "type": "text",
                "text": system_context
                }
            ]
        }
    ] 

    
    # Make the API call with structured output
    completion = open_ai_client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=MatchProfile,
    )

    # Extract the structured output
    return completion.choices[0].message.parsed