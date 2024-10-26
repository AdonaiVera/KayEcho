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


import random

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
        
        print("DOCUMENTS")
        print(documents)
        print("FINISH")
        # Score each doc
        filtered_docs = []
        for d in documents:
            print(d['profile'])
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
    
    # Define the handler for the Improve
    def stream_graph_updates(self, user_input: str):
        
        inputs={
            "messages": [
                {
                    "role": "user", 
                    "content": user_input
                }
            ]
        }

        print("User input")
        print(inputs)
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

                
            print("\n---\n")
        # Final generation
        return response_agent

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
        llm_model="claude-3-opus-20240229" 
        self.llm_model = ChatAnthropic(model=llm_model)

        self.llm_model_legacy = AnthropicLLM(model='claude-2.1')

        # Create the prompt template using the correct message formats
        prompt_improve_question = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Base on the full converstion, define a clear profile of the profile that they are looking for
                    Your task is to improve this prompt to be more detailed.  
                    Prompt to improve: {context} 
                    """
                ),
                MessagesPlaceholder(variable_name="messages")
            ]
        )

        self.improve_prompt_chain = prompt_improve_question | self.llm_model_legacy

        # Prompt imput user question
        prompt_agent_discover = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are guiding the user to find what specific profile they are searching 
                    Based on their previous answers and the conversation history, 
                    help the user to find the best profile that they are looking for.
                    """
                ),
                MessagesPlaceholder(variable_name="messages")
            ]
        )

        self.agent_discover_prompt = prompt_agent_discover | self.llm_model | StrOutputParser()

        system = """Base of the conversation generate a profile that match what the user is looking for: example: search for a software developer with x and y skills"""
        generate_profile = ChatPromptTemplate.from_messages(
            [
                ("system", system),
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
    
        # Draw the graph
        graph_image_path = "figures/graph_image_discover.png"
        with open(graph_image_path, "wb") as f:
            f.write(self.app.get_graph().draw_mermaid_png())
    
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

        generation = self.agent_discover_prompt.invoke({"messages": messages}, self.config)
        profile = self.generate_profile.invoke({"messages": messages}, self.config)

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
        print("lets do it ")
        for output in self.app.stream(inputs, self.config):
            for key, value in output.items():
                # Node
                print(key)
                print(value)
                print(f"Node '{key}':")
                print(f"Value '{value}':")
                if 'messages' in value:
                    for message in value['messages']:
                        print(message)
                        response_agent=str(message.content)
            print("\n---\n")

        # Final generation
        return response_agent
