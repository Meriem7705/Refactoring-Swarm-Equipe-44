import json
import os
from typing import List, Dict, Optional
from pathlib import Path
import re 

class PromptManager:
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            self.templates_dir = Path(__file__).parent
        else:
            self.templates_dir = Path(templates_dir)
            
        self.templates_cache: Dict[str, str] = {}
        self.files_map = {
            "auditor": "auditor_prompt.txt",
            "fixer": "fixer_prompt.txt",
            "judge": "judge_prompt.txt"
        }
        self._load_templates()

    def _load_templates(self):
        if not self.templates_dir.exists():
            print(f"⚠️ Erreur : Dossier templates inexistant : {self.templates_dir.absolute()}")
            return

        print(f"📂 Chargement des templates depuis : {self.templates_dir.absolute()}")
        for agent, filename in self.files_map.items():
            file_path = self.templates_dir / filename
            if file_path.exists():
                try:
                    self.templates_cache[agent] = file_path.read_text(encoding="utf-8")
                    print(f"✅ Template chargé pour {agent}")
                except Exception as e:
                    print(f"❌ Erreur lecture {filename} : {e}")
            else:
                self.templates_cache[agent] = ""

    # =================== AUDITOR ===================
    def build_auditor_prompt(self, file_name: str, content: str, lint_data: Optional[Dict] = None) -> str:
        template = self.templates_cache.get("auditor", "")
        context = f"FICHIER: {file_name}\n\nCODE:\n```python\n{content}\n```\n"

        if lint_data:
            score = lint_data.get('score', 0)
            context += f"\nLINT:\n- Score Actuel: {score}/10\n"
            issues = lint_data.get("categorized", {})
            context += f"- Erreurs: {len(issues.get('error', []))}\n- Avertissements: {len(issues.get('warning', []))}\n"
            context += "- Top problèmes:\n"
            for i, issue in enumerate(lint_data.get("issues", [])[:5], 1):
                context += f"{i}. Ligne {issue.get('line', '?')}: {issue.get('message', 'Inconnu')}\n"

        return f"{template}\n\n{context}\nVeuillez fournir votre analyse au format JSON."

    # =================== FIXER ===================
    def build_fixer_prompt(self, file_name: str, content: str, plan: List[Dict], prev_errors: Optional[List[str]] = None) -> str:
        template = self.templates_cache.get("fixer", "")
        context = f"FICHIER À CORRIGER: {file_name}\n\nCODE ACTUEL:\n```python\n{content}\n```\n\nPLAN DE REFACTORING:\n"
        
        for idx, step in enumerate(plan, 1):
            context += f"{idx}. {step.get('step', 'Corriger problème')}\n"
            if step.get('rationale'):
                context += f"   Raison: {step['rationale']}\n"

        if prev_errors:
            context += "\nERREURS PRÉCÉDENTES À CORRIGER ABSOLUMENT:\n"
            for e in prev_errors:
                context += f"- {e}\n"

        context += "\nCONSIGNES DE SORTIE:\n"
        context += "- Retourne UNIQUEMENT l'objet JSON.\n"
        context += "- Ne change pas les noms des fonctions existantes.\n"
        
        return f"{template}\n\n{context}"

    # =================== UTILITAIRES (CORRIGÉ) ===================
    def parse_json_response(self, response: str) -> Optional[Dict]:
        """
        Analyse la réponse du LLM pour extraire l'objet JSON.
        Préserve les sauts de ligne pour éviter les SyntaxError dans le code généré.
        """
        if not response:
            return None
        
        try:
            # 1. Extraction du bloc JSON entre accolades { }
            # re.DOTALL permet de capturer les sauts de ligne à l'intérieur du bloc
            json_match = re.search(r"(\{.*\})", response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                # 2. json.loads convertit les \\n textuels en vrais sauts de ligne \n
                return json.loads(json_str)
            
            # Si aucune accolade n'est trouvée, tentative de parsing direct
            return json.loads(response.strip())
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"⚠️ Erreur de décodage JSON : {e}")
            
            # TENTATIVE DE RÉCUPÉRATION : 
            # Nettoyage minimal des caractères de contrôle dangereux uniquement
            try:
                # On garde \t (09), \n (0a), \r (0d) et on vire le reste de 0-31
                clean_minimal = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", response)
                json_match = re.search(r"(\{.*\})", clean_minimal, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
            except Exception:
                pass
            
            return None

    def get_template(self, agent: str) -> str:
        return self.templates_cache.get(agent, "")