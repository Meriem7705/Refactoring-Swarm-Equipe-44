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
        # Ajout du contexte de score pour motiver le Fixer
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

    # =================== UTILITAIRES (LE CŒUR DE LA CORRECTION) ===================
    def parse_json_response(self, response: str) -> Optional[Dict]:
        """Nettoyage robuste pour éviter les erreurs de caractères de contrôle."""
        if not response:
            return None
        
        try:
            # ÉTAPE A : Nettoyage des caractères de contrôle JSON (le correctif pour ton erreur 429/504)
            # On supprime les caractères non-imprimables qui font planter json.loads
            clean_response = re.sub(r"[\x00-\x1F\x7F]", "", response)
            
            # ÉTAPE B : Extraction du JSON
            # On cherche le premier '{' et le dernier '}'
            json_match = re.search(r"(\{.*\})", clean_response, re.DOTALL)
            
            if json_match:
                content = json_match.group(1)
                # Supprimer les éventuels balisages Markdown restants à l'intérieur
                content = content.strip()
                return json.loads(content)
            
            return None
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"⚠️ Erreur de décodage JSON : {e}")
            # Tentative désespérée si le JSON est mal formé à cause de quotes internes
            try:
                # On essaie de réparer les doubles backslashes de Windows
                content_fixed = response.replace('\\', '\\\\')
                json_match = re.search(r"(\{.*\})", content_fixed, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
            except:
                pass
            return None

    def get_template(self, agent: str) -> str:
        return self.templates_cache.get(agent, "")