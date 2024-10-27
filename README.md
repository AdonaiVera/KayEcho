# KayEcho

## Project Overview
**KayEcho** is our AI-driven solution for Atlanta’s **AI ATL 24 Hackathon**, focused on enhancing networking through AI-powered profile analysis, RAG, and agent-based simulations. By integrating LinkedIn data, MongoDB Atlas vector search, and conversational agents, KayEcho creates an optimized environment for finding meaningful connections and generating actionable insights.

## Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Project Workflow](#project-workflow)
- [Technical Stack](#technical-stack)
- [Team Contributors](#team-contributors)
- [Installation](#installation)
- [Deployment to Google Cloud Platform (GCP) - Cloud Run](#deployment-to-google-cloud-platform-gcp---cloud-run)
- [Usage](#usage)
- [Future Improvements](#future-improvements)

## Key Features
1. **LinkedIn Data Integration**: Automated profile scraping and retrieval of professional insights.
2. **Vectorized Profile Matching**: MongoDB Atlas Vector Search for similarity-based retrieval.
3. **RAG Pipeline**: Retrieval-Augmented Generation to refine search results based on user input.
4. **Interactive Prompt Refinement**: Anthropic-powered agent assists in iteratively refining prompts.
5. **Simulation Engine**: Creates compatibility simulations based on user interests and experiences.
6. **Connection Strategies**: Automated generation of emails, icebreakers, and other communication aids.

## Project Workflow
### 1. **Data Collection**
   - Profile and post data were collected via LinkedIn’s API.
   - Data stored in MongoDB Atlas, with extracted insights used for vectorization.

### 2. **Vectorization & RAG Pipeline**
   - Profiles vectorized for high-speed retrieval using MongoDB Atlas Vector Search.
   - RAG pipeline with Anthropic API to iteratively match user inputs to profiles.

### 3. **Prompt Refinement**
   - Anthropic’s Claude API iteratively refines the prompt to ensure optimal profile matching.

### 4. **Simulation & Evaluation**
   - Simulation rounds to assess compatibility based on latest posts and mutual experiences.
   - Self-reflective evaluation of match quality, with the ideal connection identified after multiple simulations.

### 5. **Connection & Engagement**
   - Best match determined, followed by LLM-generated communication strategies.

## Technical Stack
- **Database**: MongoDB Atlas for vectorized data storage.
- **APIs**: LinkedIn API for data retrieval, Anthropic API for conversation refinement.
- **Machine Learning**: Retrieval-Augmented Generation for profile matching.
- **Simulation**: Conversational simulations to evaluate mutual compatibility.
## Frontend

The frontend for **KayEcho** is developed and maintained separately. It can be found at [networkSim](https://github.com/JonCGroberg/networkSim). This frontend application interacts with the backend API to provide a user-friendly interface for running profile analysis, simulations, and generating networking insights.

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/AdonaiVera/KayEcho
   ```
2. **Install dependencies**:
   ```bash
   cd KayEcho
   pip install -r requirements.txt
   ```
3. **Configure API keys** for LinkedIn and Anthropic APIs in the `.env` file.

4. **Run the application locally**:
   ```bash
   python main.py
   ```

## Deployment to Google Cloud Platform (GCP) - Cloud Run
To deploy **KayEcho** on Google Cloud Platform as a Cloud Run service, follow these steps:

1. **Authenticate Docker with GCP**:
   ```bash
   gcloud auth configure-docker
   ```

2. **Build the Docker image**:
   ```bash
   docker build --platform linux/amd64 -t gcr.io/{your_organization}/kay_echo:v1 .
   ```

3. **Build with Google Cloud Build**:
   ```bash
   gcloud builds submit --tag gcr.io/{your_organization}/kay_echo:v1
   ```

4. **Run the Docker image locally**:
   ```bash
   docker run -p 8080:8080 kay_echo:v1
   ```

5. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy kay_echo \
     --image gcr.io/{your_organization}/kay_echo:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## Usage
1. **Profile Analysis**: Input LinkedIn profiles for analysis.
2. **Prompt Interaction**: Use the chat agent to refine prompts for optimal matches.
3. **Run Simulations**: Review simulated conversations with compatibility assessments.
4. **Generate Outreach**: View personalized emails, icebreakers, and engagement techniques.

## Future Improvements
- Integrate additional social data sources for richer profile information.
- Enhance simulation realism with more advanced conversational models.
- Implement live updates for LinkedIn profile information.

## Team Contributors
- [Jon Groberg](https://github.com/JonCGroberg)
- [Arnav Kumar](https://github.com/Arnav2610)
- [Elliot Grossman](https://github.com/egrossman)
- [Adonai Vera](https://github.com/AdonaiVera)