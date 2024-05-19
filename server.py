from flask import Flask, request, jsonify
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import os

app = Flask(__name__)

projectId = os.getenv("GOOGLE_PROJECT_ID")

# Initialize Vertex AI
vertexai.init(project=projectId, location="us-central1")

# Load the model
model = GenerativeModel("gemini-1.5-pro-preview-0514")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json
        response = model.generate_content(
            [
                Part.from_uri(
                    mime_type="image/jpeg",
                    uri="gs://991459277573_us_import_custom/20220126-DSC02617.jpg",
                ),
                """hello how are you""",
                Part.from_text(data["text"]),
            ],
            generation_config={
                "max_output_tokens": 8192,
                "temperature": 1,
                "top_p": 0.95,
            },
        )
        return response.text
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
