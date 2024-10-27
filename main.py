import os
from flask import Flask, request, jsonify
from methods.agent_langchain import langChainHandler, langChainHandlerSearch
from methods.agent_scrapper import extract_linkedin_profile
from methods.agent_scrapper import extract_linkedin_profile, clean_linkedin_profile, get_post
from methods.agent_anthropic import get_profile, fit_profile, find_insights, get_profile_db, match_profile_agent, agent_simulation, agent_simulation_chat
import json 
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app) 

# Global dictionary to store session-specific agents
session_agents = {}

# Endpoint to handle langChainHandler requests
@app.route('/langChainHandler', methods=['POST'])
def lang_chain_handler():
    data = request.get_json()
    user_token = data.get("token")
    input_text = data.get("text")

    
    if not user_token or not input_text:
        return jsonify({"error": "Token and text are required"}), 400
    
    config = {"configurable": {"thread_id": str(user_token)}}
    
    if user_token not in session_agents:
        session_agents[user_token] = langChainHandler(user_token, config)
    
    response, profile_user = session_agents[user_token].stream_graph_updates(user_input=input_text)
    return jsonify(
        {
            "response":  {
                "text":response,
                "token":user_token
            },
            "profile_user": profile_user,
        },
    ), 200
    

# Endpoint to handle langChainHandlerSearch requests
@app.route('/langChainHandlerSearch', methods=['POST'])
def lang_chain_handler_search():
    data = request.get_json()
    user_token = data.get("token")
    input_text = data.get("text")
    linkedin_id = data.get("linkedin_id")
    
    if not user_token or not input_text:
        return jsonify({"error": "Token and text are required"}), 400
    
    # Temporal
    return jsonify({'response': {'casual_intro': "Hey Jonathan! Your recent hackathon success is impressive, and your work at Hillsborough County Sheriff's Office caught my eye. I'm Paige, and I work on AI developer tools at Google. Let's chat about our shared interests in AI and tech!", 'content_collab_intro': "Hi Jonathan, your work with AI-powered applications and hackathon experiences are truly inspiring. I'm currently focused on improving developer tools at Google for AI applications. How about we co-author an article or a piece on the future of AI in hackathons or tech development? I think we can bring some valuable insights together.", 'email': "Subject: Exciting AI Collaboration Opportunity\n\nHi Jonathan,\n\nI hope this message finds you well! I was impressed by your recent achievements at the Morgan Stanley #CodeToGive Hackathon and your innovative work with AI and law enforcement applications at the Hillsborough County Sheriff's Office. \n\nI share your passion for AI and machine learning, particularly in creating impactful solutions. As a GenAI Advisor and Product Manager with a background in AI and developer tools, I see great potential in exploring collaborative opportunities.\n\nWould you be open to a conversation to exchange ideas and explore how we might align our projects further?\n\nLooking forward to hearing from you.\n\nBest,\nPaige Bailey", 'icebreaker': 'Jonathan, I saw you won a first place at the Morgan Stanley Hackathon - what was the most unexpected challenge your team faced during the event?', 'intro': 'These profiles align well due to their shared enthusiasm for AI technology, particularly in contexts involving machine learning and innovative solutions. Both have experience in participating in hackathons and appreciate the value of collaborative tech environments, potentially making for a dynamic pairing in AI development discussions or projects.', 'linkedin_message': "Hi Jonathan! I came across your profile and was impressed by your recent success at the #CodeToGive Hackathon. Your innovative approach to AI in software development resonates with my work in enhancing developer tools at Google. I'd love to connect and discuss potential ideas or collaborations we might explore together.", 'linkedin_url': 'https://www.linkedin.com/in/dynamicwebpaige', 'match': "Both profiles are deeply rooted in the AI and software development space, with a shared enthusiasm for projects that blend machine learning and applied tech solutions. Profile 1, Paige Bailey, brings extensive experience in AI product development and evangelism as seen in roles at Google and GitHub, which aligns well with Profile 2, Jonathan Groberg's burgeoning career in software engineering and AI-driven hackathons. Both show a keen interest in hackathons and innovative tech solutions, suggesting they could collaborate effectively on cutting-edge AI projects.", 'name': 'Paige Bailey', 'profile': 'Paige Bailey is an experienced professional with over 12 years in applied machine learning, predictive modeling, data science, and visualization. Currently, she works as an Angel Investor at AngelList and advises on generative AI for Google Ventures. With expertise in Python, R, and various ML frameworks such as TensorFlow and PyTorch, she has a strong background in developing ML tools to enhance developer productivity. Her career spans roles at companies like Microsoft, Google, GitHub, and Chevron, specializing in ML developer tools, data science in geology, and cloud computing advocacy.', 'profile_agent': 'Paige Bailey is a seasoned professional with over 12 years of experience in applied machine learning, predictive modeling, and data science. She excels in driving the creation and development of generative AI tools and is passionate about improving developer experiences through technology. Her expertise extends to machine learning frameworks and cloud-based ML infrastructure, making her an influential voice in AI product development and community engagement.', 'twitter_dm': "Hi Jonathan! I saw your tweet about the Morgan Stanley Hackathon victory - that's amazing! Your approach to integrating AI with software engineering aligns with some of my projects at Google. Let's connect and maybe brainstorm some tech ideas!", 'twitter_public_message': "@JonathanG_coding Congrats on your #CodeToGive Hackathon success! 🎉 Your AI-driven solutions are inspiring and echo some exciting projects I'm involved in too. Let's connect and share ideas! #AIInnovation #TechTalks"}}), 200
    
    config = {"configurable": {"thread_id": str(user_token)}}
    
    if user_token not in session_agents:
        session_agents[user_token] = langChainHandlerSearch(user_token, config)
    
    response = session_agents[user_token].stream_graph_updates(user_input=input_text, linkedin_id=linkedin_id)
    return jsonify({"response": response}), 200

# Endpoint to handle langChainHandlerSearch requests
@app.route('/userProfile', methods=['POST'])
def userProfile():
    data = request.get_json()
    linkedin_id = data.get("linkedin_id")

    if not linkedin_id:
        return jsonify({"error": "User profile is required"}), 400
    
    response=extract_linkedin_profile(linkedin_id)
    print(response)
    return jsonify({"response": response}), 200

@app.route('/simulateConversation', methods=['POST'])
def simulate_conversation():
    data = request.get_json()
    linkedin_1 = data.get("linkedin_1")
    linkedin_2 = data.get("linkedin_2")

    if not linkedin_1 or not linkedin_2:
        return jsonify({"error": "Both LinkedIn profiles are required"}), 400
    
    # Temporal
    #return jsonify({'response': [["Wow, Meta's Movie Gen looks really impressive! As someone working with Gemini APIs, I'm curious about how it compares to other video generation models. Have you had any experience working with video generation models at Google?", "Yes, I've definitely kept a close eye on developments in this space! What's particularly interesting about Movie Gen is its comprehensive approach - combining both video and audio generation in a single framework. The 30B parameter model for video and 13B for audio shows Meta is making a serious investment here. During my time at Google, I worked more on the developer tooling side rather than directly with video models, but I can say that precise video editing and personalization capabilities are going to be game-changing for creators."], ["That's fascinating! In my recent projects with Gemini, I've mainly focused on text and image analysis. The video editing capabilities of Movie Gen sound really powerful. Do you think we'll start seeing these kinds of AI video tools becoming more accessible to developers through APIs soon, similar to how we currently use LLMs?", "Absolutely! Based on what I've seen advising at GV and GitHub, we're definitely moving in that direction. The real challenge will be making these powerful tools accessible while ensuring responsible development practices. I'm particularly interested in how this might integrate with existing developer workflows. Given your experience with building CRUD applications and working with various APIs, what kind of developer tooling would you want to see around these video generation capabilities?"], ["I'd love to see something similar to how we're currently implementing Gemini - maybe a simple SDK that handles the complex video processing in the background while providing clear methods for customization and control. From my experience building user-facing applications, having good documentation and clear error handling would be crucial. Also, considering my work with ADA compliance, I think built-in accessibility features would be really valuable.", "Those are excellent points! The accessibility angle is particularly important and often overlooked in early API implementations. Your experience with ADA compliance would be valuable as these tools mature. I think we'll also need robust testing frameworks specifically designed for AI-generated video content - something I've been advocating for in the ML tooling space. It's exciting to see developers like yourself already thinking about these practical implementation details!"], ["Hey Paige, this PyTorch Conference talk looks really interesting! As someone working with Gemini API in my projects, I'd love to learn more about LLM inference optimization. Have you had experience with TRT-LLM during your time at Google?", "Yes, absolutely! During my time working with TensorFlow and now advising on GenAI, I've seen how crucial understanding inference optimization is. The shift from just using APIs to really understanding what's happening under the hood is becoming increasingly important. Based on your experience with fullstack development, you'll probably find the sections on performance benchmarking and system sizing particularly relevant."], ["Definitely! In my current work, we're starting to hit some performance bottlenecks with our AI features. The balancing of costs and use case profiling sounds particularly relevant. Are there any specific optimization techniques you'd recommend for someone just starting to dive deeper into LLM deployment?", "From my experience at GitHub and Google, I'd suggest starting with quantization - it's one of the most effective ways to improve inference performance without sacrificing too much accuracy. Given your background with C# and TypeScript, you might also find NVIDIA's Triton interesting for deployment optimization. Have you worked with any model optimization techniques in your current projects?"], ["Not yet - mostly I've been working at the API level with Gemini for features like our AI pantry tracker and chatbot. But I'm really interested in learning more about the infrastructure side. Would you say understanding these optimization techniques is becoming essential for fullstack developers working with AI?", "Absolutely! As AI becomes more integrated into standard applications, understanding these concepts will be crucial. I've seen this transition during my time at Microsoft and Google - we're moving from AI being a specialized field to something every developer needs to understand at some level. Your experience with building full-stack applications puts you in a great position to bridge that gap."], ["Paige, thank you so much for the Gemini API support at the TEDAI hackathon! Our team's project winning 2nd place wouldn't have been possible without the incredible capabilities of Gemini.", "Congratulations on your win! I'm thrilled to see how you've leveraged Gemini in your hackathon project. Given your experience with building AI-powered applications, I'd love to hear more about how you integrated Gemini into your solution."], ['We built on our experience from previous projects like our AI pantry tracker and chatbot to create something really innovative. The Gemini API was particularly powerful for handling complex multimodal interactions in our solution.', "That's exactly the kind of creative implementation we love to see! Your background in fullstack development combined with AI shows in your approach. How did you handle any performance considerations while integrating the API?"], ['We actually implemented some of the optimization techniques I learned from your earlier talks! Particularly focused on efficient API calls and response handling to maintain a smooth user experience. Meeting the Mayor of San Francisco was just the icing on the cake!', "That's fantastic! It's rewarding to see developers like yourself taking those concepts and applying them in real-world applications. Looking forward to hearing your presentation tomorrow - these kinds of success stories really help showcase the practical potential of GenAI tools."], ["Hey Paige! I just wanted to say thank you again for the Gemini team's support at TEDAI San Francisco. Winning 2nd place was incredible, and meeting the Mayor was such an honor!", 'Congratulations on your victory, Jonathan! Your track record with Gemini implementations - from your pantry tracker to chatbot projects - really shows in this achievement. What unique aspects of Gemini did you leverage for your winning solution?'], ["We built on our experience with Gemini's multimodal capabilities that we developed during the Headstarter AI fellowship. The real breakthrough came from combining those features with some of the scalability patterns we learned from your team's documentation.", "That's exactly what we love to see - developers taking our tools and pushing them in innovative directions. I'm particularly interested in how you've evolved from your earlier projects to this award-winning implementation. Looking forward to hearing more details in your presentation tomorrow!"], ["Thanks! We'll be going into detail about how we integrated Gemini with our existing stack tomorrow at 12:30. Having both Microsoft and Google's support really helped us push the boundaries of what we thought was possible.", 'This kind of cross-platform innovation is what drives the field forward. Your background in full-stack development combined with your growing expertise in AI tools makes you well-positioned to create these kinds of impactful solutions. Make sure to share your presentation materials afterward - it could be valuable for other developers in the community!']]}), 200
    
    return jsonify({
    "response": [
        {
            "speaker": "A",
            "text": "David! Great to finally meet in person. That panel was fascinating, though I noticed you shaking your head during the predictive modeling section."
        },
        {
            "speaker": "B",
            "text": "*chuckles* Was it that obvious? Some of their assumptions about data collection in remote areas seemed a bit... optimistic."
        },
        {
            "speaker": "A",
            "text": "Actually, I was thinking the same thing. We faced similar challenges with our zero-waste tracking system. Real-world data is never as clean as these presentations make it seem."
        },
        {
            "speaker": "B",
            "text": "Exactly! *takes a sip of coffee* Speaking of your zero-waste initiative - 70% reduction in one year is impressive. How did you manage the human factor? That's usually where our models break down."
        },
        {
            "speaker": "A",
            "text": "*sighs* Honestly? It was messy. The data showed clear benefits, but changing people's daily habits was the real challenge. Some departments were... let's say less enthusiastic than others."
        },
        {
            "speaker": "B",
            "text": "That sounds familiar. My wildfire prediction model is technically 85% accurate, but getting agencies to actually implement the recommended changes is a whole different battle."
        },
        {
            "speaker": "A",
            "text": "Oh, I read about your model! But I'm curious - what made you focus on wildfires specifically? There are so many environmental issues to tackle with AI."
        },
        {
            "speaker": "B",
            "text": "*pauses thoughtfully* I grew up in California. Watched my aunt lose her home in 2018. Sometimes the most compelling problems are the ones that hit close to home."
        },
        {
            "speaker": "A",
            "text": "I get that. It's different when it's personal. Though I have to admit, I'm a bit envious of how clear-cut your success metrics are. With sustainability initiatives, it's often harder to prove immediate impact."
        },
        {
            "speaker": "B",
            "text": "Clear-cut? *laughs* Try explaining confidence intervals to forest service veterans who've been doing this job for 30 years. They trust their gut more than any algorithm."
        },
        {
            "speaker": "A",
            "text": "*leans forward* How do you handle that skepticism? I'm facing similar resistance with our new packaging initiative. People see sustainability as an unnecessary expense."
        },
        {
            "speaker": "B",
            "text": "I've learned to speak their language. Instead of talking about algorithms, I focus on practical outcomes. Though I probably learned that from my STEM mentoring - teenagers can be even tougher critics."
        },
        {
            "speaker": "A",
            "text": "You mentor high school students? That's amazing. Must be challenging balancing that with everything else."
        },
        {
            "speaker": "B",
            "text": "*shrugs* It keeps me grounded. Plus, their questions often make me think about problems differently. How about you? Any side projects beyond the corporate world?"
        },
        {
            "speaker": "A",
            "text": "*hesitates* I've been trying to start a community composting program in my neighborhood, but it's moving slower than I'd like. Turns out people are even more resistant to change at home than at work."
        },
        {
            "speaker": "B",
            "text": "That's interesting... have you considered using data to track participation rates? Might help identify what motivates people to join."
        },
        {
            "speaker": "A",
            "text": "*brightens* Actually, no, I hadn't thought of that. Though I'd need help setting up something like that... *gives questioning look*"
        },
        {
            "speaker": "B",
            "text": "Are you subtly asking for my help? *grins* Because I might have some ideas about using simple IoT sensors to track composting patterns."
        },
        {
            "speaker": "A",
            "text": "Maybe I am. Though fair warning - my budget is exactly zero dollars, and the only payment would be helping save the planet, one compost bin at a time."
        },
        {
            "speaker": "B",
            "text": "*laughs* Well, my wildfire model could use some real-world sustainability metrics. Maybe we could help each other out?"
        }
    ]
})
    #return jsonify({'response': [{'speaker': 'A', 'text': "Wow, Meta's Movie Gen seems really impressive! As someone working with Gemini API, I'm curious about how it compares to other video generation models. Have you had any experience working with similar systems at Google?"}, {'speaker': 'B', 'text': "Yes, this is quite exciting! Having worked closely with ML frameworks at Google and being involved in developer tools, I can say that text-to-video generation is one of the most challenging frontiers in AI. The 30B parameter transformer model they're using is substantial. What interests me most is their approach to precise video editing - that's where I see the most immediate practical applications for developers."}, {'speaker': 'A', 'text': 'The video editing capabilities caught my eye too! In my current internship work, we focus a lot on user experience and accessibility. I wonder how tools like Movie Gen could be integrated into enterprise applications while maintaining ADA compliance. What are your thoughts on the accessibility considerations for these types of AI tools?'}, {'speaker': 'B', 'text': "That's an excellent question and shows great foresight! From my experience advising on GenAI tools, accessibility needs to be baked in from the start, not added as an afterthought. The personalized video feature they mentioned could actually help with accessibility by generating more inclusive content, but we'd need robust guidelines. Your experience with ADA compliance in government systems could offer valuable insights here."}, {'speaker': 'A', 'text': "Definitely! I've been working on achieving 100/100 lighthouse scores for our public-facing components. Do you think we'll see specific accessibility standards develop for AI-generated content? It seems like an area that might need new frameworks beyond traditional WCAG guidelines."}, {'speaker': 'B', 'text': "I can bring data to this discussion - in my work with GitHub Copilot and other ML-enabled developer tools, we've found that AI can actually help enforce accessibility standards automatically. I believe we'll need a combination of technical standards and ethical guidelines specific to AI-generated media. Would love to hear more about how you're implementing these considerations in your current projects!"}, {'speaker': 'A', 'text': "This PyTorch Conference talk on LLM inference looks fascinating! As someone working with the Gemini API in my projects, I'm really interested in learning more about optimizing inference performance. Have you had experience with different quantization approaches?"}, {'speaker': 'B', 'text': 'Yes! Having worked extensively with TensorFlow and now advising on GenAI tools, I can tell you that quantization is crucial for practical deployment. The balance between model performance and resource utilization is especially important. What kind of performance requirements are you dealing with in your current projects?'}, {'speaker': 'A', 'text': "In our law enforcement applications, we need quick response times while maintaining accuracy. I've been working with Gemini API calls, but I'm curious about the trade-offs between cloud-based inference and local deployment. What's your take on that decision process?"}, {'speaker': 'B', 'text': "That's a great question! From my experience at Google and GitHub, the decision really depends on your specific use case. For law enforcement applications, you need to consider data privacy, latency requirements, and cost. Local deployment with TRT-LLM or similar optimizations can be powerful, but it requires careful system sizing. Have you looked into batching strategies for your API calls?"}, {'speaker': 'A', 'text': "We've implemented some basic request batching, but I'm interested in learning more about the piggybacking and balancing techniques mentioned in the talk. Given your experience with developer tools, what best practices would you recommend for optimizing our inference pipeline?"}, {'speaker': 'B', 'text': "Based on my work with developer platforms, I'd recommend starting with profiling your current workload patterns. The key is understanding your prefill vs. generation balance. For law enforcement applications, you might want to look into NVIDIA's Triton Inference Server - it handles a lot of the optimization automatically. I'd be happy to share some resources from my TensorFlow advocacy days that cover these concepts in detail."}, {'speaker': 'A', 'text': "Thank you so much for the Gemini team's support at the TEDAI Hackathon! We were able to secure 2nd place, and the capabilities of the Gemini API really helped us push our project to the next level."}, {'speaker': 'B', 'text': "Congratulations on your hackathon win! I'm really excited to see how you leveraged Gemini's capabilities. Having been involved in developer platforms for years, I always love seeing innovative applications. Would you mind sharing what unique problem your team tackled?"}, {'speaker': 'A', 'text': 'We built on my experience from the Headstarter AI fellowship, where I worked with Gemini for vision and text applications. For this hackathon, we focused on creating an accessible AI solution that could handle both multimodal inputs and complex processing requirements.'}, {'speaker': 'B', 'text': "That's fantastic! The combination of accessibility and multimodal AI is particularly interesting. From my experience at Google and now advising GenAI projects, that's exactly the kind of practical application that pushes the technology forward. How did you handle the integration challenges?"}, {'speaker': 'A', 'text': "The biggest challenge was balancing performance with accessibility requirements - something I learned from my work at the Sheriff's Office where we maintain strict ADA compliance. We used Gemini's API for the heavy lifting while keeping the frontend lightweight and responsive."}, {'speaker': 'B', 'text': "That's a really thoughtful approach! It's great to see your experience with government compliance informing hackathon projects. Would love to hear your presentation tomorrow - the developer community can learn a lot from real-world applications like this that consider both technical performance and accessibility."}, {'speaker': 'A', 'text': "Thank you so much for the Gemini team's support at TEDAI San Francisco! Meeting the Mayor and winning 2nd place was incredible. Your team's guidance on the Gemini API really helped us push our project to the next level."}, {'speaker': 'B', 'text': "Congratulations on the win! It's fantastic to see your innovative use of the Gemini API. Having advised numerous GenAI projects, I'm always excited to see real-world applications. Looking forward to your presentation tomorrow - what aspect of Gemini did you find most impactful for your solution?"}, {'speaker': 'A', 'text': "The multimodal capabilities were game-changing! Building on my experience from Headstarter AI fellowship, where we built several Gemini-powered applications, we were able to create something that really showcased the API's versatility while maintaining enterprise-grade standards."}, {'speaker': 'B', 'text': "That's exactly the kind of implementation we love to see! Your background with both hackathon projects and enterprise development at the Sheriff's Office brings a unique perspective. Would you be interested in sharing your insights with our developer community? We're always looking for case studies that demonstrate practical applications."}, {'speaker': 'A', 'text': "I'd be honored! Especially since our project focused on combining cutting-edge AI capabilities with real-world accessibility requirements - something I've become passionate about through my work on ADA-compliant government systems."}, {'speaker': 'B', 'text': "Perfect! This kind of cross-pollination between government compliance requirements and innovative AI applications is invaluable. I'll make sure to attend your presentation tomorrow at 12:30 PM. Your experience could provide valuable insights for our future developer tools and documentation."}]})
    
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

    profile_name_1=dynamic_profile_linkedin_1_base['response']['full_name']
    profile_name_2=dynamic_profile_linkedin_2_base['response']['full_name']
    # Simulate autonomous loop with the common topics
    insights_list=[]

    # Add the first two insights from the posts
    insights_list=list_posts_1[:2]+list_posts_2[:2]

    # Improve the way that we introduce the past context
    if not insights_list:
        print("No insights found.")
        topic_discussion=f"Hi, Lets talk about your most successfull story and what is the most exciting thing you have done in this area?"
    else:
        topic_discussion=[f"I saw that {insight}, let's discuss about that." for insight in insights_list]
    
      
    # Generate conversation
    temporal_memory = []
    chat_history = []
    past_context=""
    for current_context in topic_discussion:
        print("current context")
        print(current_context)
        prompt='''
            Character 1:{dynamic_profile_linkedin_1}
            Character 2:{dynamic_profile_linkedin_2}

            Past Context: {past_context}

            Current Context: {current_context}

            (This is what is in {profile_name_1}'s head: {detailed_experiences_1} Beyond this, {profile_name_1} doesn't necessarily know anything more about {profile_name_2}!) 

            (This is what is in {profile_name_2}'s head: {detailed_experiences_2} Beyond this, {profile_name_2} doesn't necessarily know anything more about {profile_name_1}!) 

            Generate their conversation here as a script in a list, and output in JSON format with “script_items” (list of dicts with “character_1” and “character_2”).
        '''.format(dynamic_profile_linkedin_1=dynamic_profile_linkedin_1, dynamic_profile_linkedin_2=dynamic_profile_linkedin_2, past_context=past_context, current_context=current_context, profile_name_1=profile_name_1, profile_name_2=profile_name_2, detailed_experiences_1=detailed_experiences_1, detailed_experiences_2=detailed_experiences_2)
        
        print("PROMPT WORKING CONVERSATION HERE DYNAMICS ...")
        response=agent_simulation_chat(prompt, temporal_memory)

        response_conversation_json=json.loads(response)
        response_conversation=""
        print("RESPONSE CONVERSATION HERE DYNAMICS ...")
        for i, item in enumerate(response_conversation_json["script_items"]):
            
            
            chat_history.append({"speaker":"A","text":item['character_1']})
            chat_history.append({"speaker":"B","text":item['character_2']})
            #chat_history.append((item['character_1'], item['character_2']))
            
            #time.sleep(2)
            response_conversation+=f"{item['character_1']}\n{item['character_2']}\n"
        
        temporal_memory.append({
            'user':prompt,
            'assistant':response_conversation
        })
        
        past_context=current_context

    return jsonify({"response": chat_history}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)