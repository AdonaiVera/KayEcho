
from langchain.text_splitter import RecursiveCharacterTextSplitter # Importing text splitter from Langchain
from langchain.vectorstores.chroma import Chroma
from llm import LLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

import requests
import json




class Agent():
    def __init__(self, name, llm, profile = None, seed=False):


        self.name = name
        self.llm = llm.llm
        # self.backstory = ",".join(backstory)
        self.text_splitter = llm.text_splitter
        # self.info = info

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
        
        direct = "memories/"+self.name.lower().strip().replace(" ","_")

        if seed:
            backstory = self.parse_profile_data(profile)
            backstory.append("My name is {name}".format(name=self.name))
            documents = self.text_splitter.create_documents(backstory)
            # chunks = backstory
            self.db = Chroma.from_documents(
            documents,
            llm.embeddings,
            persist_directory=direct
        )
        else:
            self.db=Chroma(persist_directory=direct, embedding_function=llm.embeddings)
        
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

    def save_memory(self, text):
        # doc = Document(page_content=text,
        #                metadata={"source": "conversation", "agent":agent, "id": self.counter})
        
        doc = self.text_splitter.create_documents([text])
        self.db.add_documents(doc)
        # self.counter+=1

    def parse_profile_data(self, file_location):

        with open(file_location, "r") as f:
            data = json.load(f)

        data = data['response']['response']

        collection = []
        for k in data.keys():
            if k not in ['gender','linkedin','email','follower_count','premium']:
                statements = self.get_profile_info(data[k],k)
                if len(statements) > 0:
                    for stat in statements:
                        collection.append(stat)

        return collection



    def get_profile_info(self,field,field_name):

        prompt = """
        You are an expert data analyst who is given a json that represents data on an individual

        Field Name: {field}

        Data = {data}

        -------
        Task: Given the Field Name and the data, produce a series of statements in first person.

        For example:
        - I live in New York
        - I work at Google
        - I went to School at NYU

        Output Format:
        A python list of results:

        ["I Live in New York", "I work at Google", "I went to school at NYU"]

        
        
        """.format(field = field_name, data = json.dumps(field))

        fields = self.llm.invoke(prompt).content
        return fields.split(",")
    

    def get_recent_memory(self, n=10):
        return self.db.get()["documents"][-n:]
    
    def generate_plans(self):
        memory = self.get_recent_memory(20)

        prompt = """Given these memories of previous events, create a plan for what you would like to learn

        Memories: {memories}


        Output: A list of things to learn
        """.format(memories = ",".join(memory))
        
        return self.llm.invoke(prompt)
        


def test_get_profile(profile_linkedin_1):
    url_profile_linkedin = f'{url}/userProfile'
    payload_profile = {
        "linkedin_id": profile_linkedin_1
    }
    response = requests.post(url_profile_linkedin, json=payload_profile)
    if response.status_code == 200:
        print("Response from userProfile:", response.json())
        return response.json()
    else:
        print("Error:", response.status_code, response.text)


    
def download_data(urls):

    for u in urls:
        json_data = test_get_profile(u)
        name = json_data['response']['response']['full_name']
        file_name = "profiles/"+ name.lower().replace(" ","_").strip() + ".json"

        json_data['response']['response']['linkedin'] = None
        json_data['response']['response']['email'] = None

        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

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

    # backstory = [
    #     "I live in from Atlanta, Georgia",
    # "I habe worked at Deloitte for over 2 years as a senior AI consultant.",
    # "I help clients solve problems using AI\n- NLU intent Detection\n- Causal ML\n- Generative AI - GANs and LLMs\n- Obligatory PowerPoint slides.",
    # "I Previously worked at The Home Depot as an innovation engineer where his responsibilities were: Perform Applied Research and Development\n- Work with stakeholders across the business to determine new revenue streams or solve existing - Inefficiencies through modern advances in technology\n- Quickly prototype new technology for retail such as AR, VR, AI/ML, and Robotics\n- Use expertise in Machine Learning and Software Development to architect novel applications from the ground up\n- NLP, Computer Vision, Linear Optimization, Game Development, Time Series Predictions\nMentor and manage developers and interns to complete MVPs and research\n- Organize and archive results from research to hand off to any interested parties\n- Work closely with UX and product management to conduct research and interviews for new products",
    # "I Recieved my Masters from the Georgia Institute of Technology in Computer Science.",
    # "I Receivedd my bachelors from Georgia Institute of Technology in Physics."
    # ]

    # elan_info = "An expeirenced data scientist with expertise in Computer Vision, NLP, and LLMs"

    # elan = Agent("Elan Grossman", llm, profile = "profiles/elan_grossman.json", seed=True)
    # print(elan.retrieve_memory("where do you live?"))
    # urls = [
    #     "https://www.linkedin.com/in/arnav-kumar-66419027a/",
    #     "https://www.linkedin.com/in/jonathan-groberg/",
    #     "https://www.linkedin.com/in/adonai-vera/",
    #     "https://www.linkedin.com/in/luisesilvavargas/",
    #     "https://linkedin.com/in/rishabkalluri/",
    #     "https://www.linkedin.com/in/shreya-mahesh001/",
    #     "https://www.linkedin.com/in/shraya-patel/",
    #     "https://www.linkedin.com/in/adityagupta001/",
    #     "https://www.linkedin.com/in/wyatt-bunch/",
    #     "https://www.linkedin.com/in/elan-grossman/"

    # ]
    urls = ["https://www.linkedin.com/in/dynamicwebpaige/",
            "https://www.linkedin.com/in/alex-albert/",
            "https://www.linkedin.com/in/zaiddoski/",
            "https://www.linkedin.com/in/nathaliaalicea/",
            "https://www.linkedin.com/in/irfanessa/",
            "https://www.linkedin.com/in/kem-ezeoke-149b1a53/",
            "https://www.linkedin.com/in/vaishnavitumsi/",
            "https://www.linkedin.com/in/aaronbegg1/"]

    # download_data(urls)


    # elan = Agent("Elan Grossman", llm, profile = "profiles/elan_grossman.json", seed=True)
    # adonai = Agent("Adonai Vera", llm, profile = "profiles/adonai_vera.json", seed=True)
    # aditya = Agent("Aditya Gupta", llm, profile = "profiles/aditya_gupta.json", seed=True)
    # arnav = Agent("Arnav Kumar", llm, profile = "profiles/arnav_kumar.json", seed=True)
    # jonathan = Agent("Jonathan Groberg", llm, profile = "profiles/jonathan_groberg.json", seed=True)
    # luis = Agent("Luis Silva", llm, profile = "profiles/luis_s.json", seed=True)
    # rishab = Agent("Rishab Kalluri", llm, profile = "profiles/rishab_kalluri.json", seed=True)
    # shraya = Agent("Shraya Patel", llm, profile = "profiles/shraya_patel.json", seed=True)
    # shreya = Agent("Shreya Mahesh", llm, profile = "profiles/shreya_mahesh.json", seed=True)
    # shreya = Agent("Wyatt Bunch", llm, profile = "profiles/wyatt_bunch.json", seed=True)

    # paige = Agent("Paige Bailey", llm, profile = "profiles/paige_bailey.json", seed=True)
    # irfan = Agent("Irfan Essa", llm, profile = "profiles/irfan_essa.json", seed=True)
    # alex = Agent("Alex Albert", llm, profile = "profiles/alex_albert.json", seed=True)
    # kem = Agent("Kem Ezeoke", llm, profile = "profiles/kem_ezeoke.json", seed=True)
    nathalia = Agent("Nathalia Alicea", llm, profile = "profiles/nathalia_alicea.json", seed=True)
    zaid = Agent("Zaid Doski", llm, profile = "profiles/zaid_doski.json", seed=True)
    vaishnavi = Agent("Vaishnavi Tumsi", llm, profile = "profiles/vaishnavi_tumsi.json", seed=True)
    aaron = Agent("Aaron Begg", llm, profile = "profiles/aaron_begg.json", seed=True)

