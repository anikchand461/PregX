# PregaCab

This project is a **Flask-based web application** that eliminates the traditional hospital role in ambulance allocation.  
Instead, **patients can directly connect with available ambulance drivers**. Once a driver accepts a request, they can:  

- 📍 View the **route from the ambulance to the patient’s home**.  
- 🏥 See **nearby hospitals** relative to the patient’s location.  

---

## 🛠️ Tech Stack
- **Frontend**: HTML, CSS, Vanilla JavaScript  
- **Backend**: Flask (Python)  
- **Database**: SQLite  
- **Mapping**: Leaflet.js / Google Maps API (for live route + hospitals)  

---

## ⚙️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/ambulance-direct-connect.git
cd ambulance-direct-connect
```

### Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### install dependencies
```bash
pip install -r requirements.txt
```

### Initialize database
```bash
flask db init
flask db migrate -m "Initial migration."
flask db upgrade
```

### Run the application
```bash
python app.py
```
the app will be available at http://127.0.0.1:5000

---

## 🔑 Core Features
- **Patient** → Driver direct connection** (no hospital intermediate).  
- **Ambulance Route Tracking**: Driver can see the shortest path to patient’s location.  
- **Nearby Hospital Locator**: Once patient’s address is confirmed, nearby hospitals are shown.  
- **Lightweight Frontend** using Vanilla JS + Leaflet/Maps API.  
- **SQLite Database** for storing patients, drivers, and ride logs.  

---

## 📊 Future Enhancements
- 📡 **Real-time updates** via WebSockets  
- 📱 **Mobile-first UI** for faster patient requests  
- 🤖 **AI-based risk predictor** (integration with patient health data)  