import os
import sys
import argparse
import time  # Import indispensable pour les pauses
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# -----------------------------
# PATH CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "src"))

from src.utils.logger import log_experiment, ActionType
from src.utils.toolsmith_utils import run_pylint, run_pytest, lire_fichier, ecrire_fichier
from src.prompts.PromptManager import PromptManager

# -----------------------------
# ENV
# -----------------------------
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Clé API manquante (.env)")
    sys.exit(1)

# -----------------------------
# LLM
# -----------------------------
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    google_api_key=api_key,
    temperature=0,
    verbose=True
)

# =====================================================
# ORCHESTRATEUR (Audit → Fix → Test → Loop)
# =====================================================
def orchestrator(file_path, max_iterations):
    pm = PromptManager()
    abs_path = os.path.abspath(file_path)
    current_score = 0  # Suivi du score de qualité

    print(f"\n🚀 [MISSION] {file_path}")

    for iteration in range(1, max_iterations + 1):
        print(f"\n🔁 ITERATION {iteration}/{max_iterations}")

        # =====================================
        # 1️⃣ AUDIT
        # =====================================
        try:
            code_original = lire_fichier(abs_path)
            lint = run_pylint(abs_path)
            
            # Récupération du score pour l'IA
            current_score = lint.get("score", 0)
            print(f"📊 Qualité actuelle : {current_score}/10")

            prompt = pm.build_auditor_prompt(file_path, code_original, lint)
            response = llm.invoke(prompt)

            log_experiment(
                "Auditor",
                "models/gemini-2.5-flash",
                ActionType.ANALYSIS,
                {
                    "file": file_path,
                    "input_prompt": prompt,
                    "output_response": response.content,
                    "score": current_score
                },
                "SUCCESS"
            )

            analyse = pm.parse_json_response(response.content)
            plan = analyse.get("refactoring_plan", [])
            print(f"✅ Audit OK ({len(plan)} problèmes détectés)")

            # Petite pause pour éviter l'erreur 429 entre deux appels
            time.sleep(5)

        except Exception as e:
            print(f"❌ Audit failed: {e}")
            return

        # =====================================
        # 2️⃣ FIXER
        # =====================================
        try:
            prompt_fix = pm.build_fixer_prompt(file_path, code_original, plan)
            response_fix = llm.invoke(prompt_fix)

            log_experiment(
                "Fixer",
                "models/gemini-2.5-flash",
                ActionType.FIX,
                {
                    "file": file_path,
                    "input_prompt": prompt_fix,
                    "output_response": response_fix.content
                },
                "SUCCESS"
            )

            data = pm.parse_json_response(response_fix.content)

            if data and "code_corrige" in data:
                ecrire_fichier(abs_path, data["code_corrige"])
                print("📝 Code corrigé écrit")

        except Exception as e:
            print(f"❌ Fix failed: {e}")
            return

        # =====================================
        # 3️⃣ JUDGE (pytest)
        # =====================================
        print("🧪 Running tests...")
        # Pause avant les tests pour laisser le système de fichiers respirer
        time.sleep(2)
        result_pytest = run_pytest(abs_path)
        
        # Logique flexible basée sur le "status" renvoyé par toolsmith_utils
        success = False
        logs = "Aucun log"

        if isinstance(result_pytest, dict):
            # On utilise le 'status' SUCCESS/FAILURE qu'on a défini ensemble
            success = result_pytest.get("status") == "SUCCESS"
            logs = result_pytest.get("stdout", "Aucun log")
        else:
            success = result_pytest[0]
            logs = result_pytest[1]

        log_experiment(
            agent_name="Judge",
            model_used="pytest",
            action=ActionType.DEBUG,
            details={
                "file": file_path,
                "input_prompt": "Exécution des tests unitaires",
                "output_response": str(logs)
            },
            status="SUCCESS" if success else "FAILURE"
        )

        if success:
            # Si le score est parfait ou les tests passent, on s'arrête
            if current_score >= 9.5:
                print(f"🎉 MISSION ACCOMPLIE (Score: {current_score}/10) → fichier validé")
                return
            else:
                print(f"✅ Tests OK, mais score Pylint ({current_score}) améliorable. Itération suivante...")
        else:
            print(f"❌ Tests FAIL ou Code incomplet → nouvelle tentative")

        # Pause de fin d'itération pour reset le quota Gemini
        print("⏳ Pause de 10s pour le quota API...")
        time.sleep(10)

    print("⚠️ Max iterations atteintes → fin de mission")

# =====================================================
# MAIN CLI (Reste inchangé)
# =====================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", required=True)
    parser.add_argument("--max_iterations", type=int, default=5)

    args = parser.parse_args()
    print("🤖 Refactoring Swarm démarré")
    target = Path(args.target_dir)

    if target.is_file():
        orchestrator(str(target), args.max_iterations)
    elif target.is_dir():
        for f in target.glob("*.py"):
            orchestrator(str(f), args.max_iterations)
    else:
        print("❌ Chemin invalide")

if __name__ == "__main__":
    main()