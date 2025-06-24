import base64
import mimetypes
import re
from pathlib import Path
from openai import OpenAI
from .assets import get_project_assets




# Initialize OpenAI client
client = OpenAI()


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

    return response.id

# Example usage:

def generate_full_html(project_name: str) -> str:
    """Generates a full HTML response for the given project."""
    slug = slugify(project_name)
    assets = get_project_assets(slug)

    pdf_folder = ACTIVE_UPLOADS_PATH / slug / "pdfs"
    if not pdf_folder.exists():
        raise FileNotFoundError(f"No PDFs found for project {project_name}")
   

    # Optionally, get the previous response ID from image analysis
    previous_response_id = generate_image_analysis_response(
        project_name=project_name,
        user_text="Please analyze each image and give a one-sentence description. Start each with the given filename exactly. Example: image_1.png - A child holding an umbrella"
    )

    # Create a new vector store for this project
    vector_store = client.vector_stores.create(
        name=f"{project_name} PDFs"
    )

    # Upload all PDF files to the vector store
    for pdf_path in sorted(pdf_folder.glob("*.pdf")):
        with open(pdf_path, "rb") as pdf_file:
            client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store.id,
                file=pdf_file
            )
    # Prepare the prompt for the response
    def read_prompt_from_md() -> str:
        """Placeholder: Reads prompt text from a markdown file."""
        md_path = BASE_DIR / "data" / "prompts" / "htmlprompt.md"  # Change this path as needed
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()

    prompt = read_prompt_from_md()
    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store.id]
        }],
        previous_response_id=previous_response_id
    )

    return response
  

if __name__ == "__main__":
    result = generate_image_analysis_response(
        project_name="V_Mall",
        user_text="Please analyze each image and give a one-sentence description. Start each with the given filename exactly. Example: image_1.png - A child holding an umbrella"
    )
    print(result)