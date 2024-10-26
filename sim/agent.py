
from langchain.text_splitter import RecursiveCharacterTextSplitter # Importing text splitter from Langchain
from langchain.vectorstores.chroma import Chroma
from llm import LLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document




class Agent():
    def __init__(self, name, backstory, llm):


        self.name = name
        self.llm = llm.llm
        self.backstory = ",".join(backstory)

        # chunks = self.get_chunks_self(backstory)
        documents = []
        for i, item in enumerate(backstory):
            documents.append(Document(
                page_content=item,
                metadata={
                    "source": "backstory",
                    "id":i
                }
            ))
        self.counter = i+1
        # chunks = backstory

        self.db = Chroma.from_documents(
        documents,
        llm.embeddings,
        persist_directory="memories/"+self.name.lower().strip().replace(" ","_")
    )
        
        retriever = self.db.as_retriever()

        self.qa = RetrievalQA.from_chain_type(
            llm=self.llm, 
            chain_type="stuff", 
            retriever=retriever, 
            verbose=True
        )
        
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

        prompt_template = """Use the following pieces of context to follow the question at the

            {context}

            Question: {query}
            Answer:""".format(context=context, query=query)
        
        print(prompt_template)

        return self.qa(prompt_template)
    
    def retrieve_memory(self, query):
        return self.qa(query)

    def save_memory(self, text, agent):
        doc = Document(page_content=text,
                       metadata={"source": "conversation", "agent":agent, "id": self.counter})
        self.db.add_documents([doc],ids=[str(self.counter)])
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


