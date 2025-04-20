import os
import openai
from agency_swarm.tools import BaseTool
from pydantic import Field
from dotenv import load_dotenv
import logging

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables (ensure OPENAI_API_KEY is set)
load_dotenv()

# Configure OpenAI client
# It's generally recommended to initialize the client once if possible,
# but doing it in run() ensures it uses the latest key if env changes.
# Consider initializing at the agent level if performance is critical.

class InvestorReportGenerator(BaseTool):
    """
    Generates a professional investor report text based on provided project name 
    and flattened content. It directly utilizes the OpenAI API to create the narrative.
    """
    project_name: str = Field(..., description="The name of the project for context.")
    flattened_content: str = Field(..., description="A single string containing all pre-processed component answers and relevant data provided by the CEO Agent.")
    # Removed user_input field as per user edits.

    class ToolConfig:
        one_call_at_a_time = True
        strict = True
        
    def run(self) -> str:
        """
        Constructs prompts, calls the OpenAI API to generate the report text, 
        and returns the generated text as a string.
        """
        logger.info(f"Running InvestorReportGenerator for project: {self.project_name}")

        try:
            # Initialize OpenAI client within the run method
            client = openai.OpenAI()
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY environment variable not set.")
                raise ValueError("OpenAI API key is not configured.")
            # client.api_key = api_key # The client typically uses the env var automatically

            # Define the prompts for the LLM
            system_prompt = """
            You are an expert financial analyst and report writer specializing in investor communications. 
            Your task is to synthesize the provided information into a clear, concise, professional, and insightful investor report.
            Structure the report using Markdown headings (## for main sections, ### for subsections). 
            Focus on objective analysis and avoid overly promotional language.
            The report should generally include sections like Executive Summary, Project Status, Financial Analysis, Operational Data, Projections, and Recommendations, if the provided data supports them.
            Directly output the report text without any introductory or concluding remarks outside the report content itself.
            """

            user_prompt = f"""
            Generate a comprehensive investor report for the project: '{self.project_name}'.
            Use the following consolidated information as the basis for the report:

            --- BEGIN CONSOLIDATED DATA ---
            {self.flattened_content}
            --- END CONSOLIDATED DATA ---

            Ensure the report flows logically and professionally addresses key points relevant to an investor.
            """

            logger.info("Calling OpenAI API for report generation...")
            # Make the API call
            response = client.chat.completions.create(
                model="gpt-4o",  # Or your preferred model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5, # Adjust temperature for desired creativity/factuality
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content
            logger.info("Successfully generated report text from OpenAI.")
            
            if not generated_text or not generated_text.strip():
                 logger.warning("OpenAI API returned empty content.")
                 return "Error: AI failed to generate report content."

            return generated_text.strip()

        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API request failed to connect: {e}")
            return f"Error: Failed to connect to OpenAI API: {e}"
        except openai.RateLimitError as e:
             logger.error(f"OpenAI API request exceeded rate limit: {e}")
             return f"Error: OpenAI API rate limit exceeded: {e}"
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API returned an API Error: {e.status_code} {e.response}")
            return f"Error: OpenAI API returned status {e.status_code}: {e.message}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during report generation: {e}", exc_info=True)
            return f"Error: An unexpected error occurred: {str(e)}"


if __name__ == "__main__":
    # Example usage (requires OPENAI_API_KEY in environment)
    print("Testing InvestorReportGenerator Tool...")
    
    test_flattened_content = """
    Project Alpha Status: Phase 2 completed ahead of schedule. Budget utilization at 95%.
    Financial Overview: Q3 Revenue increased 15% QoQ. Net Profit Margin stable at 12%.
    Operational Metrics: User acquisition up 20%, churn rate reduced by 5%.
    Projections: Expecting 10% revenue growth in Q4.
    Key Risks: Potential supply chain disruptions identified for component X.
    CEO Note: Focus on mitigating supply chain risk immediately.
    """
    
    tool = InvestorReportGenerator(
        project_name="Project Alpha Q3 Update",
        flattened_content=test_flattened_content
    )
    
    # In a real test, you might need to mock the openai call
    # or ensure the API key is available.
    print("Simulating run... (Actual API call requires API key)")
    
    # This will attempt a real API call if key is available
    # generated_report = tool.run()
    # print("\n--- Generated Report (Sample) ---")
    # print(generated_report)
    
    # For demonstration without calling API:
    print("\n--- Test Setup --- ")
    print(f"Project Name: {tool.project_name}")
    # print(f"Flattened Content:\n{tool.flattened_content}") # Can be very long
    print("(Skipping actual API call in this basic test execution)")
    # Simulate a possible output structure
    print("\n--- Expected Output Type ---")
    print("A string containing the generated Markdown report.")
