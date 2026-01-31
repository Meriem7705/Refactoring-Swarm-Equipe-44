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
    """Exécute pylint sur un fichier de sandbox et renvoie le score."""
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier)

    if not os.path.exists(chemin):
        return {"status": "error", "message": "Fichier introuvable"}

     # On exécute pylint via python -m pylint pour être sûr que c'est le bon pylint
    result = subprocess.run(
         ["python", "-m", "pylint", "--output-format=json", chemin],
        capture_output=True,
        text=True,
         shell=True  
    )

    # Résultat JSON parsé
    try:
        import json
        pylint_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        pylint_data = {"raw_output": result.stdout}

    # Retour structuré
    return {
        "returncode": result.returncode,  # 0 = ok, >0 = problème
        "messages": pylint_data,          # liste de messages ou raw si erreur JSON
        "stderr": result.stderr
    }

# =====================
# 3. PYTEST FUNCTION
# =====================
def run_pytest(nom_fichier_test):
    """Exécute pytest sur un fichier de test dans sandbox et affiche tout."""
    sandbox_path = creer_sandbox()
    chemin = os.path.join(sandbox_path, nom_fichier_test)

    if not os.path.exists(chemin):
        return {"status": "error", "message": "Test introuvable"}

   
    # Exécution de pytest avec sortie condensée (-q pour "quiet") et capture
    result = subprocess.run(
        ["python", "-m", "pytest", chemin, "-q", "--tb=short", "--disable-warnings", "--maxfail=5"],
        capture_output=True,
        text=True
    )

    # Retour structuré exploitable par l'IA
    return {
        "returncode": result.returncode,   # 0 = succès, >0 = échec
        "stdout": result.stdout,           # sortie complète des tests
        "stderr": result.stderr            # erreurs éventuelles
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
    except FileNotFoundError:
        data = []

    data.append({
        "action": action,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
