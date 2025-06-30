import base64
import mimetypes
import re
import logging
from pathlib import Path
from openai import OpenAI
from .assets import get_project_assets
import os
from .vector_store import create_vector_store, upload_pdf_files_to_vector_store

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# Path definitions
BASE_DIR = Path(__file__).resolve().parent.parent
ACTIVE_UPLOADS_PATH = BASE_DIR / "data" / "uploads" / "active_report"

def slugify(value: str) -> str:
    """Converts a project name to a slug (lowercase, underscore)."""
    return re.sub(r"[^\w]+", "_", value.lower()).strip("_")

def get_image_inputs_for_project(project_name: str) -> list:
    """Fetch and encode all image files under a project folder for OpenAI."""
    slug = slugify(project_name)
    image_folder = ACTIVE_UPLOADS_PATH / slug / "images"
    if not image_folder.exists():
        return []

    image_inputs = []
    for image_path in image_folder.glob("*"):
        if image_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                continue
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
            image_inputs.append({
                "type": "input_image",
                "image_url": f"data:{mime_type};base64,{encoded}",
                "detail": "low"
            })
    return image_inputs

def generate_image_analysis_response(project_name: str, user_text: str) -> str:
    slug = slugify(project_name)
    image_folder = ACTIVE_UPLOADS_PATH / slug / "images"
    if not image_folder.exists():
        return "No images found."

    input_blocks = [{"type": "input_text", "text": user_text}]

    for image_path in sorted(image_folder.glob("*")):
        if image_path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
            continue

        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            continue

        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        image_filename = image_path.name

        # Add filename context before the image
        input_blocks.append({
            "type": "input_text",
            "text": f"Image filename: {image_filename}"
        })

        input_blocks.append({
            "type": "input_image",
            "image_url": f"data:{mime_type};base64,{encoded}",
            "detail": "low"
        })

    response = client.responses.create(
        model="gpt-4.1",
        input=[{
            "role": "user",
            "content": input_blocks
        }]
    )
    logger.info(f"Generated response: {response.output_text}")
    return response.id

# Example usage:

def generate_full_html(project_name: str,user_input:str) -> str:
    """Generates a full HTML response for the given project."""
    slug = slugify(project_name)
    
    # Try to get assets but don't fail if they're not available
    try:
        assets = get_project_assets(slug)
    except Exception as e:
        print(f"Warning: Could not load assets: {e}")
        assets = {}  # Use empty dict as fallback

    pdf_folder = ACTIVE_UPLOADS_PATH / slug / "pdfs"
    if not pdf_folder.exists():
        raise FileNotFoundError(f"No PDFs found for project {project_name}")
   
    # Rest of the function remains the same...
    # Optionally, get the previous response ID from image analysis
    previous_response_id = generate_image_analysis_response(
        project_name=project_name,
        user_text="Please analyze each image and give a one-sentence description. Start each with the given filename exactly. Example: image_1.png - A child holding an umbrella"
    )



    # Create a new vector store for this project
    vector_store = create_vector_store(project_name, client=client)

    # Upload all PDF files to the vector store
    upload_stats = upload_pdf_files_to_vector_store(vector_store["id"], dir_pdfs=pdf_folder, client=client)
    print(upload_stats)
    

    metroway_prompt = BASE_DIR / "data" / "prompts" / "metroway_prompt.md"
    generic_prompt = BASE_DIR / "data" / "prompts" / "htmlprompt.md"
    # Prepare the prompt for the response
    def read_prompt_from_md(md_path) -> str:
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()

    if(project_name == "V_Metroway"):
        prompt = read_prompt_from_md(metroway_prompt)
        # Add the assets to the prompt
        if assets:
            prompt += "\n\nAssets:\n"
            for key, value in assets.items():
                prompt += f"{key}: {value}\n"
    else:
        prompt = read_prompt_from_md(generic_prompt) 

    
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        instructions=user_input,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store['id']],
        }],
        previous_response_id=previous_response_id,
        temperature=0.2,
        top_p=0.9,
    )

    return response.output_text

if __name__ == "__main__":
    result = generate_full_html(
        project_name="V_Metroway",
    )
    print(result)