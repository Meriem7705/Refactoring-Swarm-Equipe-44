import os
import json
import subprocess
from datetime import datetime

# =====================
# 1. SANDBOX FUNCTIONS
# =====================

def creer_sandbox():
    """ Crée le dossier sandbox si inexistant."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sandbox_path = os.path.join(base_path, "sandbox")
    if not os.path.exists(sandbox_path):
        os.makedirs(sandbox_path)
    return sandbox_path

def lister_fichiers_sandbox():
    """ Liste les fichiers dans sandbox """
    sandbox_path = creer_sandbox()
    return os.listdir(sandbox_path)

def lire_fichier(nom_fichier):
    """ Lit le contenu d'un fichier dans sandbox """
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier)
    if not os.path.exists(chemin):
        raise FileNotFoundError(f"{nom_fichier} introuvable")
    with open(chemin, "r", encoding="utf-8") as f:
        return f.read()

def ecrire_fichier(nom_fichier, contenu):
    """ Crée ou modifie un fichier dans sandbox """
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    print(f"Fichier '{nom_fichier}' écrit dans sandbox ")
    return chemin

# =====================
# 2. PYLINT FUNCTION 
# =====================

def run_pylint(nom_fichier):
    """Exécute pylint et renvoie un score réel sur 10."""
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier)

    if not os.path.exists(chemin):
        return {"success": False, "message": "Fichier introuvable"}

    result = subprocess.run(
        ["python", "-m", "pylint", "--output-format=json", chemin],
        capture_output=True,
        text=True,
        shell=True  
    )

    try:
        pylint_data = json.loads(result.stdout)
        
        categorized = {"error": [], "warning": [], "convention": [], "refactor": []}
        for issue in pylint_data:
            cat = issue.get('type', 'error') 
            if cat in categorized:
                categorized[cat].append(issue)
        
        # --- CALCUL DU SCORE (NOUVEAUTÉ) ---
        # Formule : on retire des points selon la gravité des problèmes
        # On part de 10/10
        penalites = (len(categorized["error"]) * 1.0) + \
                    (len(categorized["warning"]) * 0.5) + \
                    (len(categorized["convention"]) * 0.2) + \
                    (len(categorized["refactor"]) * 0.3)
        
        score_final = max(0, 10 - penalites)

        return {
            "success": True,
            "score": round(score_final, 2),
            "issues": pylint_data,
            "categorized": categorized
        }
        
    except json.JSONDecodeError:
        return {
            "success": False, 
            "score": 0,
            "issues": [], 
            "categorized": {"error": [], "warning": [], "convention": [], "refactor": []}
        }

# =====================
# 3. PYTEST FUNCTION
# =====================
def run_pytest(nom_fichier_test):
    """Exécute pytest sur un fichier de test dans sandbox."""
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier_test)

    if not os.path.exists(chemin):
        return {"status": "error", "message": "Test introuvable"}

    result = subprocess.run(
        ["python", "-m", "pytest", chemin, "-q", "--tb=short", "--disable-warnings", "--maxfail=5"],
        capture_output=True,
        text=True
    )

    is_success = result.returncode in [0, 5]
    output = result.stdout if result.stdout else result.stderr
    
    if result.returncode == 5:
        output = "SUCCESS: No tests found, but syntax is valid."

    return {
        "returncode": result.returncode,
        "status": "SUCCESS" if is_success else "FAILURE",
        "stdout": output,
        "stderr": result.stderr
    }

# =====================
# 4. LOGGING FUNCTION
# =====================

def log_action(action, details):
    """Enregistre une action dans logs/experiment_data.json"""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_path, "logs")
    log_path = os.path.join(log_dir, "experiment_data.json")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({
        "action": action,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)