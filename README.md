# 💺 HealthSync

**HealthSync** is an AI-powered health assistant built with **Python (Flask)** and integrated with the **Groq API**. It provides intelligent health interactions, document uploads, and a simple web interface — designed for users to receive guided responses to health-related queries like hypertension pre-screening.

---

## ⚡ Features

* 🧠 AI chatbot using Groq's LLM
* 📄 PDF upload and processing
* 🦮 Custom question flow (e.g., for hypertension screening)
* 🌐 Flask-based HTML interface
* 🔐 Secure `.env`-based API key handling

---

## 💠 Tech Stack

* **Backend**: Python 3.11, Flask
* **Frontend**: HTML5, CSS3, Jinja2 Templates
* **AI/LLM**: Groq API (e.g., LLaMA-3)
* **Deployment-ready**: Render, Railway, etc.

---

## 📁 Project Structure

```
HealthSync/
├── app.py               # Main Flask server
├── bot.py               # Chat logic (optional)
├── dia.py               # Question flow / logic
├── hyper.py             # Hypertension model handler
├── templates/           # HTML pages (Jinja2)
│   ├── index.html
│   ├── chatbot.html
│   └── login.html
├── static/uploads/      # Uploaded PDFs
├── requirements.txt     # Dependencies
├── .env                 # Groq API key (not committed)
└── .gitignore           # Excludes .env, venv, etc.
```

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/Navya-Devv/HealthSync.git
cd HealthSync
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Add Your `.env` File

Create a `.env` in the root directory:

```env
GROQ_API_KEY=your_actual_api_key_here
```

> 🔐 **Never commit this file.** It's already in `.gitignore`.

### 5. Run the App

```bash
python3 app.py
```

Open your browser at [http://localhost:5000](http://localhost:5000)

---

## 📀 Notes

* Ensure that Groq API key is active and has access to your selected model (e.g., `llama3-8b-8192`)
* Static PDF files are saved in `static/uploads/`
* All health logic flows (like hypertension screening) are customizable in `hyper.py`

---

## 📦 Future Improvements

* [ ] Frontend redesign with Tailwind or React
* [ ] Add authentication (Flask-Login or Firebase)
* [ ] Deploy backend on Render + frontend on Netlify
* [ ] Store reports/results using SQLite or Supabase

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

---

## 📄 License

This project is under development and currently unlicensed. Feel free to use for learning or inspiration.
