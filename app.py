import google.generativeai as genai
import requests
import os
from flask import Flask, render_template, request, send_file, session
from config import GEMINI_API_KEY, STABILITY_API_KEY

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session storage

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Ensure directories exist
os.makedirs("static/thumbnails", exist_ok=True)


# Function to enhance title using Gemini AI
def enhance_title(title):
    response = model.generate_content(f"Make the title more engaging for a YouTube thumbnail: '{title}'")
    return response.text.strip()


# Function to expand concept note into a better prompt
def generate_ai_prompt(concept_note, title):
    response = model.generate_content(
        f"Generate a high-quality YouTube thumbnail with the title '{title}' prominently displayed, based on the concept: '{concept_note}'")
    return response.text.strip()


# Function to generate images using Stability AI
def generate_images(prompt, filename):
    url = f"https://api.stability.ai/v2beta/stable-image/generate/sd3"
    headers = {
        "authorization": f"Bearer {STABILITY_API_KEY}",
        "accept": "image/*",
        #"Content-Type": "application/json"
    }

    final_prompt = (
        f"{prompt}, photo-realistic, UHD, highly detailed, ultra-sharp, cinematic lighting, "
        "perfect composition, depth of field, 8K resolution, title mentioned should be there on image"
    )

    negative_prompt = "cartoon, anime, CGI, 3D render, low resolution, artifacts"

    payload = {
        "model": "sd3-medium",
        "prompt": final_prompt,
        "negative_prompt": negative_prompt,
        "output_format": "jpeg",
        "height": 720,
        "width": 1280,
        "aspect_ratio": "16:9",  # Force correct aspect ratio
        "samples": 1
    }

    response = requests.post(url, headers=headers, files={"none": ''}, data=payload)
    if response.status_code == 200:
        path = f"static/thumbnails/{filename}.jpeg"
        with open(path, "wb") as file:
            file.write(response.content)
        return path
    else:
        #raise Exception(str(response.json()))
        print("❌ Image not generated")
        return None


# Flask routes
@app.route("/", methods=["GET", "POST"])
def index():
    thumbnails = [
        f"static/thumbnails/{img}" for img in os.listdir("static/thumbnails") if img.endswith((".jpeg", ".png", ".jpg"))
    ]

    if request.method == "POST":
        title = request.form["title"]
        concept_note = request.form["concept_note"]

        # Enhance title
        ai_title = enhance_title(title)

        # Generate AI prompt
        user_better_prompt = generate_ai_prompt(concept_note, title)
        ai_better_prompt = generate_ai_prompt(concept_note, ai_title)

        img1_filename = f"thumbnail_{len(thumbnails) + 1}"
        img2_filename = f"thumbnail_{len(thumbnails) + 1 + 1}"

        # Generate thumbnails
        user_thumbnail_path = generate_images(user_better_prompt, img1_filename)
        ai_thumbnail_path = generate_images(ai_better_prompt, img2_filename)


        return render_template("result.html", title=title, ai_title=ai_title, img1=user_thumbnail_path, img2=ai_thumbnail_path)

    return render_template("index.html", thumbnails=thumbnails)


@app.route("/download/<filename>")
def download(filename):
    path = f"static/thumbnails/{filename}"
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found", 404


if __name__ == "__main__":
    app.run(debug=True)
