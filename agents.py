import logging
from crewai import Agent, Task, Crew
from langchain.tools import Tool
from langchain_openai import OpenAI
from langchain_google_community import GoogleSearchAPIWrapper
from typing import Optional, List
import os
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Set up OpenAI with increased timeout
llm = OpenAI(api_key=OPENAI_API_KEY, request_timeout=300)  # 5 minutes timeout

# Set up Google Search
search = GoogleSearchAPIWrapper(google_api_key=GOOGLE_API_KEY, google_cse_id=GOOGLE_CSE_ID)

def read_pdf(file_path: str) -> str:
    try:
        logger.info(f"Starting to read PDF: {file_path}")
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        
        if not text.strip():
            logger.info("No text extracted, attempting OCR")
            images = convert_from_path(file_path)
            for image in images:
                text += pytesseract.image_to_string(image)
        
        logger.info("PDF reading completed")
        return text
    except Exception as e:
        logger.exception(f"An error occurred while reading the PDF: {e}")
        return ""

# Define tool functions
def analyze_blood_test(report: str) -> str:
    logger.info("Analyzing blood test report")
    analysis = llm(f"Analyze this blood test report and provide a summary of key findings: {report[:1000]}...")
    return f"Analysis of blood test report: {analysis}"

def search_health_articles(query: str) -> str:
    logger.info(f"Searching for health articles: {query}")
    results = search.results(query, num_results=3)
    return "\n".join([f"{r['title']}: {r['link']}" for r in results])

def generate_recommendations(analysis: str, articles: str) -> str:
    logger.info("Generating health recommendations")
    prompt = f"Based on this analysis: {analysis}\nAnd these articles: {articles}\nProvide concise health recommendations:"
    return llm(prompt)

# Create Tool objects
analyze_tool = Tool.from_function(
    func=analyze_blood_test,
    name="Analyze Blood Test",
    description="Analyze a blood test report"
)

search_tool = Tool.from_function(
    func=search_health_articles,
    name="Search Health Articles",
    description="Search for relevant health articles"
)

recommend_tool = Tool.from_function(
    func=generate_recommendations,
    name="Generate Health Recommendations",
    description="Generate health recommendations based on analysis and articles"
)

# Define agents with tools
blood_test_analyzer = Agent(
    role='Blood Test Analyzer',
    goal='Analyze blood test results accurately',
    backstory='Expert in interpreting blood tests with years of laboratory experience',
    verbose=True,
    llm=llm,
    tools=[analyze_tool],
    max_iterations=50,
    max_rpm=20
)

web_search_agent = Agent(
    role='Web Search Specialist',
    goal='Find relevant and reliable health information',
    backstory='Skilled online health researcher with a knack for finding credible medical information',
    verbose=True,
    llm=llm,
    tools=[search_tool],
    max_iterations=50,
    max_rpm=20
)

health_recommendations_agent = Agent(
    role='Health Recommendations Expert',
    goal='Provide personalized health recommendations',
    backstory='Experienced health advisor with a comprehensive understanding of medical test results and lifestyle factors',
    verbose=True,
    llm=llm,
    tools=[recommend_tool],
    max_iterations=50,
    max_rpm=20
)

# Define tasks
def create_tasks(blood_test_report: str) -> List[Task]:
    return [
        Task(
            description=f'Analyze this blood test report and provide a summary: {blood_test_report[:1000]}...',
            agent=blood_test_analyzer,
            expected_output="A detailed summary of the blood test results, highlighting any abnormal values."
        ),
        Task(
            description='Search for relevant health articles based on the blood test analysis',
            agent=web_search_agent,
            expected_output="A list of relevant health articles with their titles and URLs."
        ),
        Task(
            description='Generate personalized health recommendations based on the blood test analysis and research findings',
            agent=health_recommendations_agent,
            expected_output="A set of personalized health recommendations based on the blood test results and researched information."
        )
    ]

# Create crew
def create_crew(blood_test_report: str) -> Crew:
    return Crew(
        agents=[blood_test_analyzer, web_search_agent, health_recommendations_agent],
        tasks=create_tasks(blood_test_report),
        verbose=True,  # Changed from 2 to True
        process_timeout=1800,  # 30 minutes timeout
        max_iterations=150,
        task_callback=lambda task: logger.debug(f"Task completed: {task.description[:50]}...")
    )
# Main function to process a blood test report
def process_blood_test_report(report: str) -> Optional[str]:
    try:
        logger.info("Creating crew...")
        crew = create_crew(report)
        logger.info("Crew created. Starting kickoff...")
        result = crew.kickoff()
        logger.info("Crew kickoff completed.")
        if isinstance(result, str):
            return result
        else:
            logger.info(f"Result type: {type(result)}")
            return str(result)
    except Exception as e:
        logger.exception(f"An error occurred while processing the blood test report: {e}")
        return None

# If you want to test the script independently
if __name__ == "__main__":
    sample_report = "Sample blood test report content..."
    result = process_blood_test_report(sample_report)
    print(result)