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
    """Exécute pylint sur un fichier de sandbox et renvoie le score + erreurs triées."""
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier)

    if not os.path.exists(chemin):
        return {"success": False, "message": "Fichier introuvable"}

    # Exécution de pylint
    result = subprocess.run(
         ["python", "-m", "pylint", "--output-format=json", chemin],
        capture_output=True,
        text=True,
         shell=True  
    )

    try:
        # On transforme la sortie texte en vrai JSON
        pylint_data = json.loads(result.stdout)
        
        # --- Tri des erreurs par catégories ---
        categorized = {"error": [], "warning": [], "convention": [], "refactor": []}
        for issue in pylint_data:
            # Pylint utilise 'type' pour classer (error, warning, etc.)
            cat = issue.get('type', 'error') 
            if cat in categorized:
                categorized[cat].append(issue)
        
        # Retour structuré pour le PromptManager
        return {
            "success": True,
            "score": result.returncode, # Une base pour le score
            "issues": pylint_data,      # La liste complète
            "categorized": categorized  # La liste triée (ce que l'IA va lire)
        }
        
    except json.JSONDecodeError:
        # En cas d'erreur de lecture, on renvoie une structure vide mais compatible
        return {
            "success": False, 
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

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
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