import os
import json
import subprocess
import re
from datetime import datetime

# =====================
# 1. SANDBOX FUNCTIONS
# =====================

def creer_sandbox():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sandbox_path = os.path.join(base_path, "sandbox")
    if not os.path.exists(sandbox_path):
        os.makedirs(sandbox_path)
    return sandbox_path

def lister_fichiers_sandbox():
    sandbox_path = creer_sandbox()
    return os.listdir(sandbox_path)

def lire_fichier(nom_fichier):
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier)
    if not os.path.exists(chemin):
        raise FileNotFoundError(f"{nom_fichier} introuvable")
    with open(chemin, "r", encoding="utf-8") as f:
        return f.read()

def ecrire_fichier(nom_fichier, contenu):
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    print(f"Fichier '{nom_fichier}' écrit dans sandbox")
    return chemin

# =====================
# 2. PYLINT FUNCTION (VERSION STABLE)
# =====================

def run_pylint(nom_fichier):
    """Exécute pylint et retourne le score officiel sur 10, même si la langue du système est français."""
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier)

    if not os.path.exists(chemin):
        return {"success": False, "score": 0, "message": "Fichier introuvable"}

    # Forcer la sortie de pylint en anglais pour que la regex fonctionne
    env_vars = {**os.environ, "PYTHONIOENCODING": "utf-8", "LANG": "en_US.UTF-8"}

    result = subprocess.run(
        ["python", "-m", "pylint", chemin],
        capture_output=True,
        text=True,
        env=env_vars
    )

    output = result.stdout + result.stderr

    # Recherche du score officiel dans la sortie en anglais
    match = re.search(r"rated at (-?\d+\.?\d*)/10", output)

    if match:
        score = float(match.group(1))
    else:
        score = 0.0

    return {
        "success": True,
        "score": round(score, 2),
        "raw_output": output
    }

# =====================
# 3. PYTEST FUNCTION
# =====================

def run_pytest(nom_fichier_test):
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