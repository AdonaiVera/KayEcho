from langchain_openai import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings






class LLM():

    def __init__(self, base_url="http://localhost:8080",embeddings="sentence-transformers/all-mpnet-base-v2"):

        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            max_tokens=512,
            timeout=None,
            max_retries=2,
            api_key="something",  # if you prefer to pass api key in directly instaed of using env vars
            base_url=base_url,
        )
    
        # model_name = "sentence-transformers/all-mpnet-base-v2"
        # model_kwargs = {"device": "cuda"}
        self.embeddings = HuggingFaceEmbeddings(model_name=embeddings)

        

    def invoke(self, query):

        return self.llm(query).content