import base64
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.generative_models import Part, FinishReason
import os

projectId = os.getenv('PROJECT_ID')

def generate():
    vertexai.init(project=projectId, location="us-central1")
    model = GenerativeModel("gemini-1.5-flash-preview-0514")

    user_prompt = "Please provide a detailed summary of the current state of artificial intelligence."

    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": user_prompt,
                }
            ],
        }
    ]

    responses = model.generate_content(
        contents,
        generation_config=generation_config,
        # safety_settings=safety_settings,
        stream=True,
    )

    for response in responses:
        print(response.text, end="")

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}

safety_settings = {
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
}

generate()
