import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel, FunctionDeclaration
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Initialize Vertex AI client
init(project=os.getenv("GOOGLE_PROJECT_ID"), location=os.getenv("GOOGLE_LOCATION"))

# Define the model and configuration
model = GenerativeModel.from_pretrained("gemini-1.5-pro-preview-0514")

# Define the dummy function call
fetch_data_function = FunctionDeclaration(
    name="fetchData",
    description="Fetch data from a given URL and return the content as text",
    parameters={
        "type": FunctionDeclarationSchemaType.OBJECT,
        "properties": {
            "url": {
                "type": 'string',
                "description": "The URL to fetch data from",
                "nullable": False,
            },
        },
        "required": ["url"],
    }
)

class GenerateRequest(BaseModel):
    contents: list
    tools: list = [fetch_data_function]

@app.post("/generate")
async def generate_content(request: GenerateRequest):
    try:
        req_payload = {
            "contents": request.contents,
            "tools": request.tools,
        }

        # Generate the response from the model
        streaming_resp = model.generate_text_stream(
            prompt=req_payload["contents"][0]["parts"][0]["text"],
            generation_config={
                "max_output_tokens": 8192,
                "temperature": 1,
                "top_p": 0.95,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
            tools=[fetch_data_function]
        )

        # Process the streaming response
        for response in streaming_resp:
            for part in response.parts:
                if part.function_call:
                    if part.function_call.name == "fetchData":
                        url = part.function_call.args["url"]
                        response_text = fetch_data(url)
                        return {"url": url, "data": response_text}

        aggregated_response = await streaming_resp.response()
        return aggregated_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
