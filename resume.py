import os
from flask import Flask, request, jsonify, render_template
from google import genai
import PyPDF2

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


client = genai.Client(api_key="AIzaSyB7DU-nyUzKZhoppsVTY7XP2VXv-2nLkEA")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def parse_resume(resume_text):
    prompt = f"You are a resume parser. Extract Skills, Experience, Education, and Tools from this text in bullet points:\n{resume_text}"
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

def parse_job_description(jd_text):
    prompt = f"Extract Required skills, Responsibilities, and Preferred qualifications from this Job Description:\n{jd_text}"
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

def ats_match(parsed_resume, parsed_jd):
    prompt = f"Compare Resume:\n{parsed_resume}\n\nWith Job Description:\n{parsed_jd}\n\nProvide Match %, Matching Skills, Missing Skills, Strengths, and Suggestions."
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text



@app.route("/")
def home():
    return render_template("ats.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "Resume PDF is required"}), 400

    resume_file = request.files["resume"]
    jd_text = request.form.get("job_description")

    if not jd_text:
        return jsonify({"error": "Job description is required"}), 400

    # Save PDF
    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(pdf_path)

    # Process
    resume_text = extract_text_from_pdf(pdf_path)
    parsed_resume = parse_resume(resume_text)
    parsed_jd = parse_job_description(jd_text)
    ats_result = ats_match(parsed_resume, parsed_jd)

    return jsonify({
        "parsed_resume": parsed_resume,
        "parsed_job_description": parsed_jd,
        "ats_result": ats_result
    })

if __name__ == "__main__":
    app.run(debug=True, port=8080)