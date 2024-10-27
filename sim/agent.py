
from langchain.text_splitter import RecursiveCharacterTextSplitter # Importing text splitter from Langchain
from langchain.vectorstores.chroma import Chroma
from llm import LLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser




class Agent():
    def __init__(self, name, info, backstory, llm):


        self.name = name
        self.llm = llm.llm
        self.backstory = ",".join(backstory)
        self.text_splitter = llm.text_splitter
        self.info = info

        # chunks = self.get_chunks_self(backstory)
        # documents = []
        # for i, item in enumerate(backstory):
        #     documents.append(Document(
        #         page_content=item,
        #         metadata={
        #             "source": "backstory",
        #             "id":i
        #         }
        #     ))
        # documents.append(Document(
        #     page_content="My name is {name}".format(self.name),
        #     metadata={
        #             "source": "backstory",
        #             "id":i
        #         }
        # ))
        backstory.append("My name is {name}".format(name=self.name))

        documents = self.text_splitter.create_documents(backstory)

        
        self.counter = 0
        # chunks = backstory

        self.db = Chroma.from_documents(
        documents,
        llm.embeddings,
        persist_directory="memories/"+self.name.lower().strip().replace(" ","_")
    )
        
        self.retriever = self.db.as_retriever()

        self.qa = RetrievalQA.from_chain_type(
            llm=self.llm, 
            chain_type="stuff", 
            retriever=self.retriever, 
            verbose=True
        )

        self.active_context = ""
        
    def get_chunks_self(self, data):
        system_prompt = """Given the text output a list of data that summurizes the data as a list of facts in first person. 
        The output should be in a python list format.

        example: "Joey is a PA at Atlanta's Northside Hospital working foccusing on ENT. 
        He previously was in recidency at Emory University 2 years before that. 
        He went to college at Northwestern University in Chicago and studied pre-med.

        output:
        ['I am a PA at Northside Hospital in Atlanta',
        'I work in the ENT department',
        'I was a resident at Emory University',
        'I studied pre-med at Northwestern University for my bachelors']


        Now perform the same for this data
        data {data}
        """

        chunks = self.llm.invoke(system_prompt)
        print(chunks)

        return list(chunks)
    
    def answer_question(self, context, query):

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        

        
        prompt_template = """You are {name} - {info}.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Use three sentences maximum and keep the answer as concise as possible.

            {context}

            Question: {query}
            Answer:"""
        
        custom_rag_prompt = PromptTemplate.from_template(prompt_template)

        rag_chain = (
        {"context": self.retriever | format_docs, "question": RunnablePassthrough(), "info":self.info, "name":self.name}
        | custom_rag_prompt
        | self.llm
        | StrOutputParser()
        )

        
        
        return rag_chain.invoke(rag_chain)
    

    
    def recall_person(self, person):
        print(person)

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
    
        
        custom_rag_prompt = PromptTemplate.from_template(prompt_template)

        rag_chain = (
        {"context": self.retriever | format_docs, "person": RunnablePassthrough()}
        | custom_rag_prompt
        | self.llm
        | StrOutputParser()
        )

        
        
        return rag_chain.invoke(person)
    
    def retrieve_memory(self, query):
        return self.qa(query)

    def save_memory(self, text, agent):
        # doc = Document(page_content=text,
        #                metadata={"source": "conversation", "agent":agent, "id": self.counter})
        
        doc = self.text_splitter.create_documents([text])
        self.db.add_documents(doc,ids=[str(self.counter)])
        self.counter+=1


if __name__ == "__main__":

    llm = LLM()
    # backstory = """
    # Elan lives in from Atlanta, Georgia
    # Elan has worked at Deloitte for over 2 years as a senior AI consultant.
    # Elan helps clients solve problems using AI\n- NLU intent Detection\n- Causal ML\n- Generative AI - GANs and LLMs\n- Obligatory PowerPoint slides.
    # Elan Previously worked at The Home Depot as an innovation engineer where his responsibilities were: Perform Applied Research and Development\n- Work with stakeholders across the business to determine new revenue streams or solve existing - Inefficiencies through modern advances in technology\n- Quickly prototype new technology for retail such as AR, VR, AI/ML, and Robotics\n- Use expertise in Machine Learning and Software Development to architect novel applications from the ground up\n- NLP, Computer Vision, Linear Optimization, Game Development, Time Series Predictions\nMentor and manage developers and interns to complete MVPs and research\n- Organize and archive results from research to hand off to any interested parties\n- Work closely with UX and product management to conduct research and interviews for new products
    # Elan Recieved his Masters from the Georgia Institute of Technology in Computer Science.
    # Elan Receivedd his bachelors from Georgia Institute of Technology in Physics.
    # """

    backstory = [
        "I live in from Atlanta, Georgia",
    "I habe worked at Deloitte for over 2 years as a senior AI consultant.",
    "I help clients solve problems using AI\n- NLU intent Detection\n- Causal ML\n- Generative AI - GANs and LLMs\n- Obligatory PowerPoint slides.",
    "I Previously worked at The Home Depot as an innovation engineer where his responsibilities were: Perform Applied Research and Development\n- Work with stakeholders across the business to determine new revenue streams or solve existing - Inefficiencies through modern advances in technology\n- Quickly prototype new technology for retail such as AR, VR, AI/ML, and Robotics\n- Use expertise in Machine Learning and Software Development to architect novel applications from the ground up\n- NLP, Computer Vision, Linear Optimization, Game Development, Time Series Predictions\nMentor and manage developers and interns to complete MVPs and research\n- Organize and archive results from research to hand off to any interested parties\n- Work closely with UX and product management to conduct research and interviews for new products",
    "I Recieved my Masters from the Georgia Institute of Technology in Computer Science.",
    "I Receivedd my bachelors from Georgia Institute of Technology in Physics."
    ]

    elan = Agent("Elan Grossman", backstory, llm)
    print(elan.retrieve_memory("where do you live?"))


