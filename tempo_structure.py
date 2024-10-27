
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
        
        


prompt='''
You are a script writer that simulates how 2 people meet to understand if they are a good fit personally and professionally. When writing the script make sure to rooted into realistic conversations using specific details and a tone that feels real as in not all the conversations are about agreements and positivism. There can also be disagreements and neutral responses. There might be interactions with genuine spark that make sense or stilted interactions that lack natural flow.
Example: 
{
'script_items': [
    {
    "Marcus": "Rachel! Hey, good to see you again. That panel on inclusive design practices was really interesting, wasn't it?",
    "Rachel": "Marcus, yes! Though I have to say, some of the solutions they proposed felt a bit surface-level. I was hoping for more concrete implementation strategies."
    },
    {
    "Marcus": "Actually, I had the same thought. It reminded me of your talk at last year's conference about UX accessibility. That was much more practical.",
    "Rachel": "*laughs* You remember that? It was just a brief presentation. Though I've noticed TechVision's recent rebrand seems to have taken some of those accessibility principles to heart."
    },
    {
    "Marcus": "We did, though I'll admit it wasn't without internal pushback. Some executives thought accessibility features would compromise the aesthetic appeal.",
    "Rachel": "Oh, I know that battle well. It's frustrating how often people see it as an either-or situation. How did you end up convincing them?"
    },
    {
    "Marcus": "Data, mostly. I showed them how our competitor's lack of accessible design was actually hurting their market share. Plus, your presentation slides from last year came in handy.",
    "Rachel": "*raises eyebrows* Really? That's... actually pretty surprising. Most people just nod politely and forget about conference presentations the next day."
    },
    {
    "Marcus": "Well, when something makes sense, it makes sense. Though I'm curious - what made you focus on accessibility in the first place? It's not exactly the flashiest part of UX design.",
    "Rachel": "Honestly? My younger sister is partially blind. Watching her struggle with poorly designed interfaces... it just hit home. Sometimes personal experience is the best motivator."
    },
    {
    "Marcus": "That explains your passion for it. Must be rewarding seeing your work make a real difference.",
    "Rachel": "*pauses* Sometimes. Other times it feels like pushing a boulder uphill. Especially when clients want to cut corners on accessibility features to save money."
    },
    {
    "Marcus": "Speaking of which, I saw that mobile app you designed recently - the one with the 60% engagement increase. How did you balance accessibility with client demands there?",
    "Rachel": "*looks surprised* You've done your homework. It was... challenging. We actually went over budget to maintain the accessibility features. But the engagement metrics helped justify it."
    },
    {
    "Marcus": "That's actually something we're struggling with at TechVision right now. We're launching a new product line, and I'm pushing for more inclusive design features, but...",
    "Rachel": "*leans forward* But the budget's tight? You know, I might have some cost-effective solutions from similar projects."
    },
    {
    "Marcus": "Really? Would you be open to maybe grabbing coffee next week to discuss? This could really help us avoid some expensive mistakes.",
    "Rachel": "*checks phone calendar* I could do Wednesday morning. Though fair warning - I tend to get pretty passionate about this stuff."
    },
    {
    "Marcus": "*smiles* That's exactly why I'm asking. Passion usually leads to better solutions than just checking boxes.",
    "Rachel": "True. Though sometimes my team thinks I'm a bit too stubborn about it. But better stubborn than sorry when it comes to accessibility, right?"
    }
]
}
Prompt: Characters:
{profile_name_1}: {dynamic_profile_linkedin_1}
{profile_name_2}: {dynamic_profile_linkedin_2}
*Past Context*: {past_context}
*Current Context*: {current_context}
*Insights*: {respose_insights}
*Internal Monologues*:
- {profile_name_1} knows this about {profile_name_2}: {detailed_experiences_2}. Beyond this, {profile_name_1} has limited knowledge of {profile_name_2}.
- {profile_name_2} knows this about {profile_name_1}: {detailed_experiences_1}. Beyond this, {profile_name_2} has limited knowledge of {profile_name_1}.
*Objective*: Generate a conversation between {profile_name_1} and {profile_name_2} that starts casually and then dives deeper into personal and professional aspects of each other lifes. Each character responds naturally encouraging more detailed, intelligent questions uncovering key details that make them a great match (common ground, values, and motivations.)
**Output Requirements**:
- Format as a JSON object with a list called “script_items.”
- Each list item is a dictionary with “character_1” (speaking {profile_name_1}) and “character_2” (speaking {profile_name_2}).
*Script Style*:
- Start the conversation lightly, with introductory or general questions.
- Gradually deepen the conversation, weaving in curiosity and uncovering meaningful insights.
- Use past context, current context and insights to decide if you would agree, disagree during the conversation
Maintain a friendly, engaging tone throughout, allowing questions to feel intuitive and authentic.
'''.format(
dynamic_profile_linkedin_1=dynamic_profile_linkedin_1,
dynamic_profile_linkedin_2=dynamic_profile_linkedin_2,
past_context=past_context,
current_context=current_context,
profile_name_1=profile_name_1,
profile_name_2=profile_name_2,
detailed_experiences_1=detailed_experiences_1,
detailed_experiences_2=detailed_experiences_2,
respose_insights=respose_insights
)