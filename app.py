from flask import Flask, render_template, redirect, url_for, request, session, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
from datetime import datetime
import os
import requests
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import uuid
import time

app = Flask(__name__)
CORS(app)
app.secret_key = 'GROQ_API_KEY'
socketio = SocketIO(app, cors_allowed_origins="*")

# Load environment variables for Groq
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("Warning: GROQ_API_KEY not found in environment variables")

# Hardcoded credentials
HARDCODED_CREDENTIALS = {
    'patient': {'password': 'patient123', 'role': 'patient'},
    'doctor': {'password': 'doctor123', 'role': 'doctor'}
}

# Create data directory if it doesn't exist
DATA_DIR = "data"
UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

# Store latest readings, appointments and shared files
latest_readings = {
    'diabetes': None,
    'hypertension': None
}

appointments = []
shared_files = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def chat_with_groq(prompt):
    """Simple, direct implementation of chat functionality"""
    if not api_key:
        return "Groq API key not configured. Please check your environment variables."

    if not isinstance(prompt, str) or not prompt.strip():
        return "Please provide a valid question."

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a helpful healthcare assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 200
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            return f"Error: API returned status {response.status_code}"

        try:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "Error: Invalid response format"
        except Exception as e:
            return f"Error parsing response: {str(e)}"

    except requests.Timeout:
        return "Error: Request timed out"
    except requests.RequestException as e:
        return f"Error making request: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# ================== Authentication Routes ==================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if role == 'patient' and username == 'patient' and password == HARDCODED_CREDENTIALS['patient']['password']:
            session['user'] = {'username': username, 'role': 'patient'}
            return redirect(url_for('patient_dashboard'))
        
        if role == 'doctor' and username == 'doctor' and password == HARDCODED_CREDENTIALS['doctor']['password']:
            session['user'] = {'username': username, 'role': 'doctor'}
            return redirect(url_for('doctor_interface'))
        
        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route('/patient-dashboard')
def patient_dashboard():
    if 'user' not in session or session['user']['role'] != 'patient':
        return redirect(url_for('login'))
    return render_template('index2.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/doctor-interface')
def doctor_interface():
    if 'user' not in session or session['user']['role'] != 'doctor':
        return redirect(url_for('login'))
    return render_template('index3.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# ================== File Upload API ==================
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{unique_id}_{filename}"
        
        # Save the file
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # Create file record
        file_record = {
            'id': unique_id,
            'original_name': filename,
            'filename': unique_filename,
            'path': filepath,
            'uploaded_by': session['user']['username'],
            'upload_date': datetime.now().isoformat(),
            'file_type': filename.rsplit('.', 1)[1].lower(),
            'description': request.form.get('description', ''),
            'category': request.form.get('category', 'Other')
        }
        
        # Add to shared files
        shared_files.append(file_record)
        
        # Notify all connected clients about the new file
        socketio.emit('new_file_uploaded', file_record, broadcast=True)
        
        return jsonify({'success': True, 'file': file_record}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/files')
def get_files():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    return jsonify({'files': shared_files}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    return send_from_directory(UPLOAD_FOLDER, filename)

# ================== Appointment API ==================
@app.route('/api/appointments', methods=['GET', 'POST'])
def handle_appointments():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'POST':
        data = request.json
        
        # Create appointment
        appointment = {
            'id': str(uuid.uuid4()),
            'patient': 'patient',  # Using hardcoded patient
            'doctor': data.get('doctor', 'Dr. Smith'),  # Default doctor
            'date': data.get('date'),
            'time': data.get('time'),
            'reason': data.get('reason'),
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        appointments.append(appointment)
        
        # Notify all connected clients about the new appointment
        socketio.emit('new_appointment', appointment, broadcast=True)
        
        return jsonify({'success': True, 'appointment': appointment}), 200
    
    # For GET requests
    return jsonify({'appointments': appointments}), 200

@app.route('/api/appointments/<appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    if 'user' not in session or session['user']['role'] != 'doctor':
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.json
    
    # Find appointment
    for appointment in appointments:
        if appointment['id'] == appointment_id:
            appointment['status'] = data.get('status')
            appointment['updated_at'] = datetime.now().isoformat()
            
            # Notify all connected clients about the updated appointment
            socketio.emit('appointment_updated', appointment, broadcast=True)
            
            return jsonify({'success': True, 'appointment': appointment}), 200
    
    return jsonify({'error': 'Appointment not found'}), 404

# ================== Chatbot Functionality ==================
def save_to_json(data, filename):
    """Save data to a JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.join(DATA_DIR, f"{filename}_{timestamp}.json")
    
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {filepath}")
        return True
    except Exception as e:
        print(f"Error saving data: {str(e)}")
        return False

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.emit('bot_response', {
        'response': "Hello! I'm your HealthSync Assistant. How can I help you today? You can ask about:\n\n" +
                   "• General health questions\n" +
                   "• Diabetes monitoring\n" +
                   "• Blood pressure monitoring\n" +
                   "• Medication information\n" +
                   "• Lifestyle advice"
    })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('user_message')
def handle_message(data):
    message = data.get('message', '').lower().strip()
    print(f"Received message: {message}")
    
    if not message:
        socketio.emit('bot_response', {'response': "Please send a message."})
        return

    if message in ['sugar', 'diabetes']:
        emit('message', {'response': 'Starting diabetes monitoring. Please answer the following questions:'})
        emit('start_questions', {
            'type': 'diabetes',
            'questions': [
                "What is your current blood sugar level (mg/dL)?",
                "Is this a fasting reading or post-meal? (fasting/post)",
                "Have you taken your medication today? (yes/no)",
                "Did you consume any sugary or high-carb food today? (yes/no)",
                "Have you exercised today? (yes/no)",
                "How many hours did you sleep last night?",
                "Do you feel any symptoms like fatigue, thirst, or blurred vision? (yes/no)",
                "Did you monitor your sugar level at the same time as yesterday? (yes/no)"
            ]
        })
    elif message in ['hypertension', 'blood pressure']:
        emit('message', {'response': 'Starting blood pressure monitoring. Please answer the following questions:'})
        emit('start_questions', {
            'type': 'hypertension',
            'questions': [
                "What is your systolic blood pressure (upper number)?",
                "What is your diastolic blood pressure (lower number)?",
                "Have you experienced any dizziness or headaches? (yes/no)",
                "Have you taken hypertension medication? (yes/no)",
                "Did you exercise today? (yes/no)",
                "How many hours did you sleep last night?",
                "Have you been feeling stressed lately? (yes/no)",
                "Did you consume salty or processed foods today? (yes/no)",
                "How much water have you consumed today? (in liters)"
            ]
        })
    else:
        # Use Groq for general health questions
        response = chat_with_groq(message)
        socketio.emit('bot_response', {'response': response})

@socketio.on('analyze_data')
def analyze_data(data):
    data_type = data.get('type')
    answers = data.get('answers')
    
    if data_type == 'diabetes':
        analysis = analyze_diabetes(answers)
    elif data_type == 'hypertension':
        analysis = analyze_hypertension(answers)
    else:
        analysis = "Invalid data type for analysis"
    
    emit('message', {'response': analysis})
    
@socketio.on('request_latest_readings')
def handle_request_latest_readings():
    """Handle requests for latest readings and emit updates"""
    emit('readings_update', latest_readings)

def analyze_diabetes(answers):
    try:
        # Format the answers into a structured prompt for Groq
        sugar_level = answers.get("What is your current blood sugar level (mg/dL)?", "")
        is_fasting = answers.get("Is this a fasting reading or post-meal? (fasting/post)", "")
        took_medication = answers.get("Have you taken your medication today? (yes/no)", "")
        high_carb_food = answers.get("Did you consume any sugary or high-carb food today? (yes/no)", "")
        exercised = answers.get("Have you exercised today? (yes/no)", "")
        sleep_hours = answers.get("How many hours did you sleep last night?", "")
        has_symptoms = answers.get("Do you feel any symptoms like fatigue, thirst, or blurred vision? (yes/no)", "")
        same_time = answers.get("Did you monitor your sugar level at the same time as yesterday? (yes/no)", "")

        prompt = f"""As a healthcare AI assistant, analyze the following diabetes monitoring data and provide a detailed assessment with recommendations:

Blood Sugar Reading:
- Current Level: {sugar_level} mg/dL
- Reading Type: {is_fasting}
- Taken at same time as yesterday: {same_time}

Lifestyle Factors:
- Medication taken: {took_medication}
- High-carb food consumed: {high_carb_food}
- Exercise today: {exercised}
- Sleep hours: {sleep_hours}
- Symptoms present: {has_symptoms}

Please provide:
1. Analysis of blood sugar level (including whether it's in normal, pre-diabetic, or diabetic range)
2. Risk assessment
3. Specific recommendations based on the lifestyle factors
4. Any warning signs that need immediate attention
5. Tips for better management

Format the response with appropriate emoji indicators:
⚠️ for warnings
✅ for normal/good readings
ℹ️ for informational points
🎯 for targets
📝 for recommendations"""

        # Get analysis from Groq
        analysis = chat_with_groq(prompt)
        
        # Save the reading
        risk_level = "medium"  # Default risk level
        if "critical" in analysis.lower() or "immediate attention" in analysis.lower():
            risk_level = "high"
        elif "normal range" in analysis.lower() and "good" in analysis.lower():
            risk_level = "low"
            
        latest_readings['diabetes'] = {
            'value': float(sugar_level),
            'timestamp': datetime.now().isoformat(),
            'risk_level': risk_level
        }
        
        # After saving the reading, emit an update to all connected clients
        socketio.emit('readings_update', latest_readings, broadcast=True)
        
        return analysis

    except Exception as e:
        return f"Error analyzing diabetes data: {str(e)}"

def analyze_hypertension(answers):
    try:
        # Format the answers into a structured prompt for Groq
        systolic = answers.get("What is your systolic blood pressure (upper number)?", "")
        diastolic = answers.get("What is your diastolic blood pressure (lower number)?", "")
        has_symptoms = answers.get("Have you experienced any dizziness or headaches? (yes/no)", "")
        took_medication = answers.get("Have you taken hypertension medication? (yes/no)", "")
        exercised = answers.get("Did you exercise today? (yes/no)", "")
        sleep_hours = answers.get("How many hours did you sleep last night?", "")
        is_stressed = answers.get("Have you been feeling stressed lately? (yes/no)", "")
        salty_food = answers.get("Did you consume salty or processed foods today? (yes/no)", "")
        water_intake = answers.get("How much water have you consumed today? (in liters)", "")

        prompt = f"""As a healthcare AI assistant, analyze the following blood pressure monitoring data and provide a detailed assessment with recommendations:

Blood Pressure Reading:
- Systolic (upper number): {systolic} mmHg
- Diastolic (lower number): {diastolic} mmHg

Current Symptoms and Lifestyle Factors:
- Experiencing dizziness/headaches: {has_symptoms}
- Medication taken: {took_medication}
- Exercise today: {exercised}
- Sleep hours: {sleep_hours}
- Stress level: {is_stressed}
- Salty/processed food intake: {salty_food}
- Water consumption: {water_intake} liters

Please provide:
1. Analysis of blood pressure (categorize as normal, elevated, Stage 1, Stage 2, or Crisis)
2. Risk assessment
3. Evaluation of lifestyle factors' impact
4. Urgent warnings if needed
5. Specific recommendations for improvement
6. Hydration and dietary advice
7. Stress management suggestions if needed

Format the response with appropriate emoji indicators:
🚨 for critical/emergency situations
⚠️ for warnings
✅ for normal/good readings
ℹ️ for informational points
🎯 for targets
📝 for recommendations
💧 for hydration advice
🧘‍♀️ for stress management tips"""

        # Get analysis from Groq
        analysis = chat_with_groq(prompt)
        
        # Save the reading
        risk_level = "medium"  # Default risk level
        if "crisis" in analysis.lower() or "emergency" in analysis.lower() or "immediate" in analysis.lower():
            risk_level = "critical"
        elif "stage 2" in analysis.lower() or "severe" in analysis.lower():
            risk_level = "high"
        elif "normal" in analysis.lower() and "good" in analysis.lower():
            risk_level = "low"
            
        latest_readings['hypertension'] = {
            'value': f"{systolic}/{diastolic}",
            'timestamp': datetime.now().isoformat(),
            'risk_level': risk_level
        }
        
        # After saving the reading, emit an update to all connected clients
        socketio.emit('readings_update', latest_readings, broadcast=True)
        
        return analysis

    except Exception as e:
        return f"Error analyzing hypertension data: {str(e)}"

@app.route('/api/latest_readings')
def get_latest_readings():
    return jsonify(latest_readings)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
