import uuid
from pathlib import Path

import requests
from decouple import config
from langchain.tools import tool
from openai import OpenAI
from pydantic import BaseModel, Field

IMAGE_DIRECTORY = Path(__file__).parent.parent / "images"
CLIENT = OpenAI(api_key=str(config("OPENAI_API_KEY")))

def image_downloader(image_url: str | None) -> str:
    if image_url is None:
        return "No image URL returned from API."
    response = requests.get(image_url)
    if response.status_code != 200:
        return "Could not download image from URL."
    unique_id: uuid.UUID = uuid.uuid4()
    image_path = IMAGE_DIRECTORY / f"{unique_id}.png"
    with open(image_path, "wb") as file:
        file.write(response.content)
    return str(image_path)

# We use pydantic to define a GenerateImageInput class which inherits from BaseModel This will allow us to clearly define the input arguments our tool will need in order to run, as the LLM will need this information when calling a tool or deciding whether to call a tool or not.
# We define a single field image_description which is a string and we use Field to add a description to the field. So we want an input argument of image_description which is a string that describes the image we want to generate. If you need multiple arguments you can define these here as well in the same fashion. For our uses, this one argument will do here.
class GenerateImageInput(BaseModel):
    image_description: str = Field(
        description="A detailed description of the desired image."
    )

# After that, we declare the function itself, which takes a string as input with the image description and will return an image path in string format. Note that we included a docstring that describes what the tool does: """Generate an image based on a detailed description.""".
# This docstring is required when defining tools using the @tool decorator and is the description that will be used for the OpenAI tool schema generated behind the scenes that helps the LLM agent choose which function(s) to call. For this reason you must make sure it is an adequate description of what the tool does and what it’s purpose is.
@tool("generate_image", args_schema=GenerateImageInput)
def generate_image(image_description: str) -> str:
    """Generate an image based on a detailed description."""
    response = CLIENT.images.generate(
        model="dall-e-3",
        prompt=image_description,
        size="1024x1024",
        quality="standard",  # standard or hd
        n=1,
    )
    image_url = response.data[0].url
    return image_downloader(image_url)

if __name__ == "__main__":
    print(generate_image.run("A picture of sharks eating pizza in space."))