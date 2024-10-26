from llm import LLM
from agent import Agent


class Convo():

    def __init__(self, llm):

        self.llm = llm
        self.conversation = ''

    def converse(self, agent1, agent2, N=5):

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

        previous_answer_aug = previous_answer + "\n Answer the question in 4 sentences or less"
        print("Retreiving Answer to:", previous_answer)
        q2_answer = active_agent.retrieve_memory(previous_answer_aug)["result"]

        print(q2_answer)


        print("Collecting Memory...")
        ### now learn about the other user
        memory_agent_q = """What do you know or remember about {agent}?""".format(agent =inactive_agent.name)
        inactive_agent_memory = active_agent.retrieve_memory(memory_agent_q)["result"]
        
        print(inactive_agent_memory)

        ## Now we get the llm to respond:

        prompt = """ Given the previous question from {agent}, your answer, and context about {agent}, what would you like to ask them?

        previous question: {previous_answer}
        your answer: {your_answer}
        context: {inactive_agent_memory}


        Question: 
        """.format(agent=inactive_agent.name,previous_answer = previous_answer, your_answer = q2_answer, inactive_agent_memory = inactive_agent_memory)

        new_response = llm.invoke(prompt)

        full_response = "{q2_answer}/n{new_response}".format(q2_answer= q2_answer, new_response=new_response)

        print("Full Response: ",full_response)

        self.update_conversation(active_agent.name, full_response)


        ## Now we update the memory
        print("Adding Memory")
        memory_prompt = """
        Given the below conversation, summurize it and add it your memory in first person. Keep the summary to two sentences

        {agent}'s conversation: {previous_answer}

        Summary:
        """.format(your_name= active_agent.name, agent = active_agent.name, previous_answer=q2_answer)

        question_memory = llm.invoke(memory_prompt)
        print(question_memory)
        inactive_agent.save_memory(question_memory, inactive_agent.name)

        return full_response



    def start_convo(self, agent1, agent2):

        start_prompt = """What do you know or remember about {agent}?
        """

        agent1_start = agent1.retrieve_memory(start_prompt.format(agent=agent2.name))
        print(agent1_start)

        q_prompt = """
        Your background: {background}
        
        Given your background and context about your conversational partner: {agent} follow the following directions
        Only respond with the question
        
        Partner context: {context}

        directions: If you know {agent} respond with a question relevant to the context. Otherwise introduce yourself and ask them about themselves

        Question:
        """.format(agent=agent2.name, background = agent1.backstory, context = agent1_start["result"] )


        agent1_q1 = self.llm.invoke(q_prompt)

        return agent1_q1

    def update_conversation(self, user, text):
        self.conversation += "\n\n{user}: {text}".format(user=user,text=text)

        

        


if __name__ == "__main__":

    llm = LLM()

    backstory_elan = [
    "I live in from Atlanta, Georgia",
    "I have worked at Deloitte for over 2 years as a senior AI consultant at Deloitte.",
    "I help clients solve problems using AI\n- NLU intent Detection\n- Causal ML\n- Generative AI - GANs and LLMs\n- Obligatory PowerPoint slides.",
    "I Previously worked at The Home Depot as an innovation engineer where his responsibilities were: Perform Applied Research and Development\n- Work with stakeholders across the business to determine new revenue streams or solve existing - Inefficiencies through modern advances in technology\n- Quickly prototype new technology for retail such as AR, VR, AI/ML, and Robotics\n- Use expertise in Machine Learning and Software Development to architect novel applications from the ground up\n- NLP, Computer Vision, Linear Optimization, Game Development, Time Series Predictions\nMentor and manage developers and interns to complete MVPs and research\n- Organize and archive results from research to hand off to any interested parties\n- Work closely with UX and product management to conduct research and interviews for new products",
    "I Recieved my Masters from the Georgia Institute of Technology in Computer Science.",
    "I Received my bachelors from Georgia Institute of Technology in Physics."
    ]

    elan = Agent("Elan Grossman", backstory_elan, llm)

    backstory_ado = [
    "I live in Cincinnati, Ohio",
    "I work as a machine learning developer at SubterraAI",
    "I specialise in underground mapping and digitisation of underground infrastructure using photogrammetry, SLAM and AI to build digital twins.",
    "I used to work at as Cofounder and CTO at SwitchAI",
    "I worked to understand the behavior of your customers in the store and help the retail sector to enhance the impact of its strategies through variables such as gender, age, heat zones, among others, thanks to the power of intelligence artificial in your security cameras."
    ]

    ado = Agent("Ado Vera", backstory_ado, llm)

    convo = Convo(llm)
    convo.converse(elan,ado)