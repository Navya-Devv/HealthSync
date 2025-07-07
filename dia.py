# diabetes_monitor.py
from groq import Groq
import json
from datetime import datetime

api_key = os.getenv("GROQ_API_KEY")

DIABETES_MODEL = "llama3-8b-8192"  # Updated to Groq-supported faster model

def ask_diabetes_questions():
    questions = [
        ("What is your current blood sugar level (mg/dL)?", float),
        ("Is this a fasting reading or post-meal? (fasting/post)", str),
        ("Have you taken your medication today? (yes/no)", str),
        ("Did you consume any sugary or high-carb food today? (yes/no)", str),
        ("Have you exercised today? (yes/no)", str),
        ("How many hours did you sleep last night?", int),
        ("Do you feel any symptoms like fatigue, thirst, or blurred vision? (yes/no)", str),
        ("Did you monitor your sugar level at the same time as yesterday? (yes/no)", str)
    ]
    
    responses = {}
    print("\nPlease answer the following questions about your health:\n")
    for question, dtype in questions:
        while True:
            try:
                response = input(f"{question} ").strip().lower()
                responses[question] = dtype(response) if dtype != str else response
                break
            except ValueError:
                print("Please enter a valid response.")
    
    return responses

def analyze_diabetes_data(data):
    prompt = (
        "Analyze the following diabetes-related data and provide short dietary advice, "
        "warnings if needed, and daily wellness tips within 80 words:\n\n"
    )
    
    for key, value in data.items():
        prompt += f"- {key}: {value}\n"

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=DIABETES_MODEL,
        temperature=0.3
    )
    
    return response.choices[0].message.content

def store_diabetes_data(data, analysis):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "data": data,
        "analysis": analysis
    }
    
    with open("diabetes_records.json", "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    print("🩺 HealthSync Diabetes Monitoring System\n")
    data = ask_diabetes_questions()
    analysis = analyze_diabetes_data(data)
    store_diabetes_data(data, analysis)
    print("\n📋 Analysis:\n", analysis)
