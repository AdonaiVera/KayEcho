import os
import openai

from dotenv import load_dotenv, find_dotenv
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate, MessagesPlaceholder

# Internal methods
from methods.agent_states import UserStateManager
from methods.agent_mongo import MongoDBHandler

# Additional Tools
from langchain_anthropic import ChatAnthropic

from langchain_community.tools.tavily_search import TavilySearchResults
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import Literal, List

from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document

from typing import Annotated, Sequence
from langgraph.graph.message import add_messages

from langchain_core.messages import HumanMessage, BaseMessage, AnyMessage, AIMessage
from langchain_anthropic import AnthropicLLM

from methods.agent_scrapper import extract_linkedin_profile, clean_linkedin_profile, get_post
from methods.agent_anthropic import get_profile
from methods.agent_openai import fit_match

import random
import json

class GradeProfile(BaseModel):
    """Binary score for relevance check on retrieved profiles.."""

    binary_score: str = Field(
        description="Profiles are relevant to the question, 'yes' or 'no'"
    )

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        profile: profile
        generation: LLM generation
        documents: list of documents
    """
    messages: Annotated[list, add_messages]
    profile: str
    documents: List[str]

class GraphStateDiscover(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        messages: messages
        generation: LLM generation
        documents: list of documents
    """
    messages: Annotated[list, add_messages]
    profile: str


class langChainHandlerSearch:    
    def __init__(self, user_id, config):
        """Initialize LangChain connection and OpenAI embedding generator."""
        _ = load_dotenv(find_dotenv()) 
        openai.api_key = os.environ['OPENAI_API_KEY']
        mongo_uri = os.environ['MONGO_URI']
        self.mongo_handler = MongoDBHandler(mongo_uri, openai.api_key)

        # Config File
        self.config=config

        # Define the memory
        self.memory = MemorySaver()

        # Define the user state manager (Maybe use the new model)
        llm_model="claude-3-opus-20240229" 
        self.llm_model = ChatAnthropic(model=llm_model)

        # Define the tools
        structured_llm_grader = self.llm_model.with_structured_output(GradeProfile)

        system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
            If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
            It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
        grade_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "Retrieved document: \n\n {document} \n\n User profile: {profile}"),
            ]
        )

        self.retrieval_grader = grade_prompt | structured_llm_grader

        
        # Prompt
        system = """You a question re-writer that converts the profile that we are looing in a better version that is optimized \n 
            for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning."""
        re_write_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                (
                    "human",
                    "Here is the initial profile: \n\n {profile} \n Formulate an improved prompt.",
                ),
            ]
        )

        self.question_rewriter = re_write_prompt | self.llm_model | StrOutputParser()

        # Prompt
        workflow = StateGraph(GraphState)

        # Define the nodes
        workflow.add_node("retrieve", self.retrieve) 
        workflow.add_node("grade_profile", self.grade_profiles)
        workflow.add_node("transform_query", self.transform_query)  

        # Build graph edges
        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "grade_profile")
        workflow.add_edge("transform_query", "retrieve")
        workflow.add_conditional_edges(
            "grade_profile",
            self.decide_to_generate,
            {
                "transform_query": "transform_query",
                "generate": END,
            },
        )
        
        # Compile
        self.app = workflow.compile(checkpointer=self.memory)
    
        graph_image_path = "figures/graph_image_main.png"
        with open(graph_image_path, "wb") as f:
            f.write(self.app.get_graph().draw_mermaid_png())

    def retrieve(self, state):
        """
        Retrieve documents

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        print("---RETRIEVE---")
        messages = state["messages"]
        profile = messages[-1].content

        # Retrieve documents
        documents=self.mongo_handler.retrieve_relevant_data_old(profile, "", "user_profile")

        return {"profile":profile,"documents": documents, "messages": [AIMessage(content=profile)]}
    
    def grade_profiles(self, state):
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with only filtered relevant documents
        """

        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        messages=state["messages"]
        documents=state["documents"]
        profile=state['profile']
        
        # Score each doc
        filtered_docs = []
        for d in documents:
            score = self.retrieval_grader.invoke(
                {"messages": messages, "document": d['profile'], "profile": profile, }
            )
            grade = score.binary_score
            if grade == "yes":
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                continue
        return {"documents": filtered_docs, "messages": messages}
    
    def transform_query(self, state):
        """
        Transform the query to produce a better question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates question key with a re-phrased question
        """

        print("---TRANSFORM QUERY---")
        messages=state["messages"]
        documents=state["documents"]
        profile=state["profile"]

        # Re-write question
        profile = self.question_rewriter.invoke({"messages": messages, "profile": profile})
        return {"documents": documents, "profile": profile, "messages": messages}
            
    def decide_to_generate(self, state):
        """
        Determines whether to generate an answer, or re-generate a question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Binary decision for next node to call
        """

        print("---ASSESS GRADED DOCUMENTS---")
        print(state["messages"])
        filtered_documents = state["documents"]

        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            print(
                "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
            )
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            print("---DECISION: GENERATE---")
            return "generate"
    
    # Define the function to simulate the chat
    def get_profile_match(self, linkedin_1, linkedin_2, profile_1_looking_for):

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

        return fit_match(dynamic_profile_linkedin_1, dynamic_profile_linkedin_2, 
              list_posts_1, list_posts_2, 
              detailed_experiences_1, detailed_experiences_2, 
              profile_1_looking_for)
            

            
    # Define the handler for the Improve
    def stream_graph_updates(self, user_input: str, linkedin_id: str):
        
        inputs={
            "messages": [
                {
                    "role": "user", 
                    "content": user_input
                }
            ]
        }

        # Stream the graph
        response_agent=""
        for output in self.app.stream(inputs, self.config):
            for key, value in output.items():
                # Node
                print(f"Node '{key}':")
                if 'messages' in value:
                    for message in value['messages']:
                        print(message)
                        response_agent=str(message.content)

                if 'documents' in value:
                    documents=value['documents']

                
            print("\n---\n")

        print("More relevant documents")
        print(documents)
        print(type(documents))

        # Take the first element
        first_document = documents[0]

        print("first_document")
        print(first_document)
        print(type(first_document))

        # Final prompting and ajustment
        response=self.get_profile_match(first_document["linkedin_url"], linkedin_id, user_input)

        # Final generation
        return {
            "name": first_document["user"],
            "profile": first_document["profile"],
            "linkedin_url": first_document["linkedin_url"],
            "match": response.match,
            "intro": response.intro,
            "profile_agent": response.profile_agent,
            "email": response.email,
            "linkedin_message": response.linkedin_message,
            "twitter_dm": response.twitter_dm,
            "twitter_public_message": response.twitter_public_message,
            "icebreaker": response.icebreaker,
            "casual_intro": response.casual_intro,
            "content_collab_intro": response.content_collab_intro
        }

# Define the handler for the Improve
class langChainHandler:    
    def __init__(self, user_id, config):
        """Initialize LangChain connection and OpenAI embedding generator."""
        _ = load_dotenv(find_dotenv()) 

        # Config File
        self.config=config

        # Define the memory
        self.memory = MemorySaver()

        # Define the user state manager (Maybe use the new model)
        llm_model="claude-3-opus-20240229"  # claude-3-sonnet-20240229 #claude-3-5-sonnet-20241022
        self.llm_model = ChatAnthropic(model=llm_model)

        self.llm_model_legacy = AnthropicLLM(model='claude-2.1')

        # Prompt imput user question
        prompt_agent_discover = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are helping the user outline the ideal profile they are looking for. 
                    Ask focused questions that refine the profile, ensuring each question is directly relevant 
                    to identifying key skills, experience, and attributes. Prioritize only the most essential 
                    details to create a precise match. Only one question is needed.
                    """
                ),
                MessagesPlaceholder(variable_name="messages")
            ]
        )


        self.agent_discover_prompt = prompt_agent_discover | self.llm_model | StrOutputParser()

        # Create the prompt template using the correct message formats
        generate_profile = ChatPromptTemplate.from_messages(
            [
                (
                    "system", 
                    """
                    "Based on the conversation, generate a profile (max 5 sentences) that aligns closely with what the user seeks. 
                    Focus on relevant skills and experience that fulfill their requirements.

                    Example output:
                    Searching for a software developer skilled in Python and machine learning with experience in cloud deployment.
                    """
                ),
                MessagesPlaceholder(variable_name="messages")
            ]
        )

        self.generate_profile = generate_profile | self.llm_model_legacy 

        # Define the tools
        workflow = StateGraph(GraphStateDiscover)

        # Define the nodes.
        workflow.add_node("agent_discover", self.agent_discover) 
        # Define the edges.
        workflow.add_edge(START, "agent_discover")
        workflow.add_edge("agent_discover", END)
      
        # Compile the graph
        self.app = workflow.compile(checkpointer=self.memory)
        
    def agent_discover(self, state):
        """
        Generate casual answer

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        print("---DISCOVER PROFILES---")
        messages = state["messages"]
        # If there is no profile, we will create one    
        profile = state.get("profile", "")  

        print("This is the state informtion x")
        print(state)
        last_message=messages[-1].content

        generation = self.agent_discover_prompt.invoke({"messages": messages}, self.config)

        profile = self.generate_profile.invoke({"messages": messages, "profile":profile, "last_message":last_message}, self.config)

        return {"profile":profile, "messages": [AIMessage(content=generation)]}
    
    def stream_graph_updates(self, user_input: str):
        # Get the current state
        inputs={
            "messages": [
                {
                    "role": "user", 
                    "content": user_input
                }
            ]
        }

        # Stream the graph
        response_agent=""
        for output in self.app.stream(inputs, self.config):
            for key, value in output.items():
                # Node
                if 'messages' in value:
                    for message in value['messages']:
                        print(message)
                        response_agent=str(message.content)

                if 'profile' in value:
                    profile_user=str(value['profile'])
            print("\n---\n")


        # Final generation
        return response_agent, profile_user
