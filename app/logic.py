from datetime import datetime
import json
from pathlib import Path

def extract_symptoms(text):
    keywords = [
        "fever", "chest pain", "headache", "cough", "back pain",
        "dizziness", "nausea", "fatigue", "shortness of breath", "joint pain",
        "sore throat", "abdominal pain", "diarrhea", "constipation",
        "insomnia", "anxiety", "muscle cramps", "heartburn", "ear pain", "rash"
    ]
    return [kw for kw in keywords if kw in text.lower()]

def check_symptoms(symptoms_text, user):
    try:
        base_path = Path(__file__).parent.parent  # Go up to project root
        
        # Load databases
        with open(base_path / 'app' / 'symptom_data.json') as f:
            symptom_db = json.load(f)
            
        with open(base_path / 'app' / 'clinics.json') as f:
            clinics_db = json.load(f)

        extracted = extract_symptoms(symptoms_text)
        if not extracted:
            return {"advice": "No recognizable symptoms found", "type": "error"}

        # Check for severity keywords
        user_input = symptoms_text.lower()
        is_severe = "severe" in user_input or "intense" in user_input or "extreme" in user_input
        
        symptom = extracted[0]
        symptom_info = symptom_db.get(symptom, {})
        
        # Determine severity
        final_severity = "severe" if is_severe else symptom_info.get("severity", "mild")
        
        # Build result object
        result = {
            "advice": f"We recommend consulting a {symptom_info.get('specialist', 'doctor')}",
            "type": "clinic" if final_severity == "severe" else "home_care",
            "remedies": symptom_info.get("remedies", []),
            "exercises": symptom_info.get("exercises", []),
            "severity": final_severity
        }

        if final_severity == "severe":
            result["clinic"] = next(
                (c for c in clinics_db if c['specialist'] == symptom_info['specialist']), 
                None
            )

        # Save to history
        history_path = base_path / 'app' / 'userhistory.json'
        history = {}
        
        if history_path.exists():
            with open(history_path, 'r') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = {}

        if user not in history:
            history[user] = []
            
        history[user].append({
            "input": symptoms_text,
            "output": result,
            "timestamp": datetime.now().isoformat()
        })
        
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=4)

        return result

    except Exception as e:
        return {"error": str(e), "type": "error"}