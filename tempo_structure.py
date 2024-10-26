
        prompt='''
            Here is the conversation that happened between {profile_name_1} and {profile_name_2}. 
            {response_conversation}

            Summarize what {profile_name_1} thought about {profile_name_2} in one short sentence. The sentence needs to be in third person:
        '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_summarize=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_summarize)

        # WE SHOULD DO THIS WITH THE STATEMENTS -> TEMPORAL DO IT WITH THE CONVERSATION
        prompt='''
            [Conversation]
            {response_conversation}

            Write down if there is anything from the conversation that {profile_name_1} might have found interesting from {profile_name_2}'s perspective, in a full sentence. 

            {profile_name_1}          
            '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_interesting=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_interesting)

        prompt='''
            [Conversation]
            {response_conversation}

            Currently: {profile_name_1}

            Summarize the most relevant statements above that can inform {profile_name_1} in his conversation with {profile_name_2}.
     
            '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_interesting=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_interesting)

        prompt='''
            [Conversation]
            {response_conversation}

            Based on the statements above, summarize {profile_name_1} and {profile_name_2}'s relationship. What do they feel or know about each other?        
            '''.format(response_conversation=response_conversation, profile_name_1=profile_name_1, profile_name_2=profile_name_2)
        
        response_interesting=agent_simulation(prompt, gpt_param)
        respose_insights.append(response_interesting)

        # I'm sending the main topic but here could be the summarize
        past_context=current_context

        print("RESPONSE INSIGHTS X ...")
        print(respose_insights)
        print(type(respose_insights))
        
        