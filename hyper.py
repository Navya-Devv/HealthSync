# hypertension_monitor.py
from groq import Groq
import json
from datetime import datetime

api_key = os.getenv("GROQ_API_KEY")
HYPERTENSION_MODEL = "llama3-8b-8192"  # Changed to a faster model

def ask_hypertension_questions():
    questions = [
        ("What is your systolic blood pressure (upper number)?", int),
        ("What is your diastolic blood pressure (lower number)?", int),
        ("Have you experienced any dizziness or headaches? (yes/no)", str),
        ("Have you taken hypertension medication?", str),
        ("Did you exercise today? ", str),
        ("How many hours did you sleep last night?", int),
        ("Have you been feeling stressed lately? (yes/no)", str),
        ("Did you consume salty or processed foods today? (yes/no)", str),
        ("How much water have you consumed today? (in liters)", float)
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

def analyze_hypertension_data(data):
    # Create a structured analysis prompt
    prompt = (
        "Analyze the following hypertension-related data and provide a personalized "
        "assessment, lifestyle tips, and warnings (if necessary) within 80 words:\n\n"
    )

    for key, value in data.items():
        prompt += f"- {key}: {value}\n"

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=HYPERTENSION_MODEL,
        temperature=0.3
    )
    
    return response.choices[0].message.content

def store_hypertension_data(data, analysis):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "data": data,
        "analysis": analysis
    }
    
    with open("hypertension_records.json", "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    print("🩺 HealthSync Hypertension Monitoring System\n")
    data = ask_hypertension_questions()
    analysis = analyze_hypertension_data(data)
    store_hypertension_data(data, analysis)
    print("\n📋 Analysis:\n", analysis)
