from llm import LLM
from agent import Agent
import numpy as np
from langchain.docstore.document import Document


class Convo():

    def __init__(self, llm):

        self.llm = llm
        self.conversation = ''

    def generate_prompt(self, prompt, variables):
        for i,var in enumerate(variables):
            prompt = prompt.replace("!<INPUT {}>!".format(i), str(var))

        if "<commentblockmarker>###</commentblockmarker>" in prompt: 
            prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
    
        return prompt.strip()


    def converse(self,agent1, agent2, N=4):

        curr_chat = []

        for n in range(N):
            print(n,": --------------------------------------------------------")
            relevant_context = self.retrieve(agent1,agent2.name,5)
            relationship = self.get_relationship(agent1,agent2.name,relevant_context)

            last_chat = ''
            answer_context = ''
            for i in curr_chat[-4:]:
                last_chat += ": ".join(i) + "\n"
            if last_chat: 
                answer_context  = self.retrieve(agent1,last_chat,5)
                # if last_chat: 
                #     focal_points = [f"{relationship}",  
                #                     last_chat]
                # else: 
                #     focal_points = [f"{relationship}"]
            utterance = self.generate_utterance(agent1,agent2.name, relevant_context, relationship, last_chat, answer_context)
            utterance = utterance.split(":")[-1].replace("}","")
            curr_chat += [[agent1.name, utterance]]
            print(curr_chat[-1])


            relevant_context = self.retrieve(agent2,agent1.name,5)
            relationship = self.get_relationship(agent2,agent1.name,relevant_context)
            last_chat = ''
            for i in curr_chat[-4:]:
                last_chat += ": ".join(i) + "\n"
            if last_chat: 
                answer_context  = self.retrieve(agent1,last_chat,5)
                #     focal_points = [f"{relationship}",  
                #                     last_chat]
                # else: 
                #     focal_points = [f"{relationship}"]


            
            
            utterance = self.generate_utterance(agent2,agent1.name, relevant_context, relationship, last_chat, answer_context)
            utterance = utterance.split(":")[-1].replace("}","")
            curr_chat += [[agent2.name, utterance]]

            print(curr_chat[-1])
        memory = self.get_memo(agent1,agent2.name,curr_chat)

        agent1.save_memory(memory)

        memory = self.get_memo(agent2,agent1.name,curr_chat)

        agent2.save_memory(memory)

    def generate_utterance(self, init_agent, target_agent_name, context, relationship, chat, answer_context):

        prompt_template = """Variables: 
                !<INPUT 0>! -- Chat History
                !<INPUT 1>! -- Current Persona Name
                !<INPUT 2>! -- Target Persona Name
                !<INPUT 3>! -- Relationship
                !<INPUT 4>! -- Statements
                !<INPUT 4>! -- answer

                <commentblockmarker>###</commentblockmarker>
                [Chat History]
                !<INPUT 0>!

                [Relationship]
                !<INPUT 3>! 

                [Statements]
                !<INPUT 4>!
                !<INPUT 5>!


                -----
                Task: 
                Based on the chat history above, along with the Statements and relationship known about !<INPUT 2>! by !<INPUT 1>!, how should !<INPUT 1>! answer !<INPUT 2>!'

                Step 1:
                If chat history is present, generate an answer to the last question in the Chat History using the context, otherwise, ask them about what they do for thier job. Do not repeat any precious questions

                Step 2:
                Ask a question from !<INPUT 1>! to !<INPUT 2>! from the perspective of!<INPUT 1>!

                Output format: Output a json of the following format: 
                {
                "!<INPUT 1>!": "<!<INPUT 1>!'s utterance>"
                }


                """
        
        variables = [
            chat,
            init_agent.name,
            target_agent_name,
            relationship,
            context,
            answer_context
        ]

        new_prompt = self.generate_prompt(prompt_template, variables)

        return self.llm.invoke(new_prompt)

    def retrieve(self, init_person, target_person_name, N=5):

        relevant_context = init_person.retriever.vectorstore.similarity_search_with_score(target_person_name)


        ## Filter on relevant results
        new_context = []
        for context in relevant_context:
            if context[1] < 1.5:
                new_context.append(context)
        if len(new_context) > 0:
            relevant_context = new_context[0:N]
        else:
            relevant_context = [(Document(page_content="I don't know about {target_person_name}".format(target_person_name=target_person_name)),0)]

        return relevant_context
    
    def get_relationship(self, init_person, target_person_name, relevant_context):


        prompt_template = """Variables: 
                !<INPUT 0>! -- Statements
                !<INPUT 1>! -- curr persona name
                !<INPUT 2>! -- target_persona.scratch.name

                <commentblockmarker>###</commentblockmarker>
                [Statements]
                !<INPUT 0>!

                Based on the statements above, summarize !<INPUT 1>! and !<INPUT 2>!'s relationship. What do they feel or know about each other?"""
        
        variables = [
            [doc[0].page_content for doc in relevant_context],
            init_person.name,
            target_person_name,

        ]

        new_prompt = self.generate_prompt(prompt_template, variables)
                
        
        return self.llm.invoke(new_prompt), relevant_context
    
    def get_memo(self, init_person, target_person_name, statements):


        prompt_template = """Variables: 
                !<INPUT 0>! -- Statements
                !<INPUT 1>! -- curr persona name
                !<INPUT 2>! -- target_persona.scratch.name

                <commentblockmarker>###</commentblockmarker>
                [Statements]
                !<INPUT 0>!

                Based on the statements above, summarize the conversation in 4 sentences or less from !<INPUT 1>! 's perspective about !<INPUT 2>! in first person using I statements as if you were !<INPUT 1>!"""
        
        variables = [
            statements,
            init_person.name,
            target_person_name,

        ]

        new_prompt = self.generate_prompt(prompt_template, variables)
                
        
        return self.llm.invoke(new_prompt)

    def converse_old(self, agent1, agent2, N=5):

        ## first what do you know about this person? If not, what will you ask
        agent1_q1 = self.start_convo(agent1,agent2)
        self.update_conversation(agent1.name, agent1_q1)

        next_question = agent1_q1
        for n in range(N):
            ### Agent 2 now answers the question
            next_question  = self.next_convo(agent2,agent1,next_question)
            next_question = self.next_convo(agent1,agent2,next_question)


        print("-------------------------")
        print(self.conversation)


    def next_convo(self, active_agent, inactive_agent, previous_answer):

        print("Retreiving Answer to:", previous_answer)
        q2_answer = active_agent.retrieve_memory(previous_answer)['result']

        print(q2_answer)


        print("Collecting Memory...")
        ### now learn about the other user


        prompt = """ Given the previous question from {agent}, your answer, and context about {agent}, what would you like to ask them?

        previous question: {previous_answer}
        your answer: {your_answer}
        context: {inactive_agent_memory}


        Question: 
        """.format(agent=inactive_agent.name,previous_answer = previous_answer, your_answer = q2_answer, inactive_agent_memory = active_agent.active_context)

        new_response = self.llm.invoke(prompt)

        full_response = "{q2_answer}/n{new_response}".format(q2_answer= q2_answer, new_response=new_response)

        print("Full Response: ",full_response)

        self.update_conversation(active_agent.name, full_response)


        return full_response



    def start_convo(self, agent1, agent2):



        ## Start by keeping a memory of the intro (this will save time)
        agent1.save_memory(agent2.name + " : " + agent2.info, agent2.name)
        agent2.save_memory(agent1.name + " : " + agent1.info, agent1.name)


        # start_prompt = """What do you know or remember about {agent}?
        # """


        agent1_start = agent1.recall_person(agent2.name)
        print(agent1_start)
        agent1.active_context = agent1_start

        q_prompt = """
        
        Given the context about your conversational partner: {agent} follow the following directions
        Only respond with the question
        
        Partner context: {context}

        directions: If you know {agent} respond with a question relevant to the context. Otherwise introduce yourself and ask them about themselves

        Question:
        """.format(agent=agent2.name, background = agent1.backstory, context = agent1.active_context)


        agent1_q1 = self.llm.invoke(q_prompt)


        # memory_agent_q = """What do you know or remember about {agent}?""".format(agent =agent1.name)
        inactive_agent_memory = agent2.recall_person(agent1.name)
        agent2.active_context = inactive_agent_memory
        
        print(inactive_agent_memory)

        return agent1_q1

    def update_conversation(self, user, text):
        self.conversation += "\n\n{user}: {text}".format(user=user,text=text)

        

        


if __name__ == "__main__":

    llm = LLM()

    # backstory_elan = [
    # "I live in from Atlanta, Georgia",
    # "I have worked at Deloitte for over 2 years as a senior AI consultant at Deloitte.",
    # "I help clients solve problems using AI\n- NLU intent Detection\n- Causal ML\n- Generative AI - GANs and LLMs\n- Obligatory PowerPoint slides.",
    # "I Previously worked at The Home Depot as an innovation engineer where his responsibilities were: Perform Applied Research and Development\n- Work with stakeholders across the business to determine new revenue streams or solve existing - Inefficiencies through modern advances in technology\n- Quickly prototype new technology for retail such as AR, VR, AI/ML, and Robotics\n- Use expertise in Machine Learning and Software Development to architect novel applications from the ground up\n- NLP, Computer Vision, Linear Optimization, Game Development, Time Series Predictions\nMentor and manage developers and interns to complete MVPs and research\n- Organize and archive results from research to hand off to any interested parties\n- Work closely with UX and product management to conduct research and interviews for new products",
    # "I Recieved my Masters from the Georgia Institute of Technology in Computer Science.",
    # "I Received my bachelors from Georgia Institute of Technology in Physics."
    # ]

    # elan_info = "An expeirenced data scientist with expertise in Computer Vision, NLP, and LLMs"

    # elan = Agent("Elan Grossman", elan_info, backstory_elan, llm)

    # backstory_ado = [
    # "I live in Cincinnati, Ohio",
    # "I work as a machine learning developer at SubterraAI",
    # "I specialise in underground mapping and digitisation of underground infrastructure using photogrammetry, SLAM and AI to build digital twins.",
    # "I used to work at as Cofounder and CTO at SwitchAI",
    # "I worked to understand the behavior of your customers in the store and help the retail sector to enhance the impact of its strategies through variables such as gender, age, heat zones, among others, thanks to the power of intelligence artificial in your security cameras."
    # ]

    # ado_info = "A Machine Learning Engineer with skills in Computer Vision and Digital twins"

    # ado = Agent("Ado Vera", ado_info ,backstory_ado, llm)

    convo = Convo(llm)

    elan = Agent("Elan Grossman", llm)
    adonai = Agent("Adonai Vera", llm)
    aditya = Agent("Aditya Gupta", llm)
    arnav = Agent("Arnav Kumar", llm)
    jonathan = Agent("Jonathan Groberg", llm)
    luis = Agent("Luis Silva", llm)
    rishab = Agent("Rishab Kalluri", llm)
    shraya = Agent("Shraya Patel", llm)
    shreya = Agent("Shreya Mahesh", llm)
    wyatt = Agent("Wyatt Bunch", llm)

    paige = Agent("Paige Bailey", llm)
    irfan = Agent("Irfan Essa", llm)
    alex = Agent("Alex Albert", llm)
    kem = Agent("Kem Ezeoke", llm)
    nathalia = Agent("Nathalia Alicia",llm)
    zaid = Agent("Zaid Doski", llm)
    vaishnavi = Agent("Vaishnavi Tumsi",llm)
    aaron = Agent("Aaron Begg", llm)

    agents = np.array([elan,adonai,arnav,aditya,jonathan,luis,rishab,shraya,shreya,wyatt, paige,irfan,alex,kem,nathalia, zaid, vaishnavi, aaron])

    np.random.shuffle(agents)



    for i in range(6):
        np.random.shuffle(agents)
        print(agents)
        print(agents[0])
        for k in range(5):
            agent1 = agents[k]
            agent2 = agents[k+1]

            convo.converse(agent1,agent2, 4)