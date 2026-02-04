import json
import os
from typing import List, Dict, Optional
from pathlib import Path
import re 

class PromptManager:
    def __init__(self, templates_dir: str = None):
        # Si aucun dossier n'est précisé, on prend le dossier où est ce fichier (src/prompts)
        if templates_dir is None:
            self.templates_dir = Path(__file__).parent
        else:
            self.templates_dir = Path(templates_dir)
            
        self.templates_cache: Dict[str, str] = {}
        
        # Mapping exact entre les clés utilisées dans le code et les noms de fichiers
        self.files_map = {
            "auditor": "auditor_prompt.txt",
            "fixer": "fixer_prompt.txt",
            "judge": "judge_prompt.txt"
        }
        
        self._load_templates()

    def _load_templates(self):
        """Charge les fichiers texte dans le cache"""
        if not self.templates_dir.exists():
            print(f"⚠️ Erreur : Le dossier des templates n'existe pas : {self.templates_dir.absolute()}")
            return

        print(f"📂 Chargement des templates depuis : {self.templates_dir.absolute()}")
        
        for agent, filename in self.files_map.items():
            file_path = self.templates_dir / filename
            if file_path.exists():
                try:
                    self.templates_cache[agent] = file_path.read_text(encoding="utf-8")
                    print(f"✅ Template chargé pour {agent} ({filename})")
                except Exception as e:
                    print(f"❌ Erreur lors de la lecture de {filename} : {e}")
                    self.templates_cache[agent] = ""
            else:
                print(f"⚠️ Template manquant sur le disque : {filename}")
                self.templates_cache[agent] = ""

    # =================== AUDITOR ===================

    def build_auditor_prompt(self, file_name: str, content: str, lint_data: Optional[Dict] = None) -> str:
        template = self.templates_cache.get("auditor", "")
        context = f"FICHIER: {file_name}\n\nCODE:\n```python\n{content}\n```\n"

        if lint_data:
            context += f"\nLINT:\n- Score: {lint_data.get('score', 'N/A')}/10\n"
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
            context += "\nERREURS PRÉCÉDENTES:\n"
            for e in prev_errors:
                context += f"- {e}\n"

        context += "\nCONSIGNES DE SORTIE:\n"
        context += "- Retourne uniquement un JSON.\n"
        context += "- Inclus le code complet corrigé dans le champ 'code_corrige'.\n"
        
        return f"{template}\n\n{context}"

    def build_fixer_prompt_from_tests(self, file_name: str, content: str, test_log: str, test_stats: Dict) -> str:
        template = self.templates_cache.get("fixer", "")
        context = f"FICHIER: {file_name}\n\nCODE ACTUEL:\n```python\n{content}\n```\n"
        context += f"\nTESTS:\n- Passés: {test_stats.get('passed', 0)}\n- Échoués: {test_stats.get('failed', 0)}\n\n"
        context += f"LOG TEST:\n```\n{test_log}\n```\n"
        context += "\nCORRECTION REQUISE:\n"
        context += "Corrige le code pour valider les tests et retourne le JSON avec le champ 'code_corrige'.\n"
        
        return f"{template}\n\n{context}"

    # =================== JUDGE ===================

    def build_judge_prompt(self, test_log: str, stats: Dict, current_score: Optional[float] = None) -> str:
        template = self.templates_cache.get("judge", "")
        context = f"RÉSULTATS DES TESTS:\n- Passés: {stats.get('passed', 0)}\n- Échoués: {stats.get('failed', 0)}\n"
        if current_score:
            context += f"SCORE PYLINT: {current_score}/10\n"
        context += f"\nLOGS:\n```\n{test_log}\n```\n"
        
        return f"{template}\n\n{context}"

    # =================== UTILITAIRES ===================

    def parse_json_response(self, response: str) -> Optional[Dict]:
        """Nettoie la réponse du LLM pour extraire le JSON de manière robuste."""
        if not response:
            return None
        
        try:
            # 1. On cherche un bloc de texte entre ```json et ```
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            
            if json_match:
                content = json_match.group(1)
            else:
                # 2. Si pas de balises json, on cherche simplement ce qui ressemble à un dictionnaire { ... }
                json_match_simple = re.search(r"(\{.*\})", response, re.DOTALL)
                if json_match_simple:
                    content = json_match_simple.group(1)
                else:
                    # 3. Dernier recours : nettoyage manuel basique
                    content = response.strip().replace("```json", "").replace("```", "").strip()

            return json.loads(content)
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"⚠️ Erreur de décodage JSON : {e}")
            # On affiche un extrait pour le debug
            print("Extrait du contenu problématique :", response[:100] + "...")
            return None

    def get_template(self, agent: str) -> str:
        return self.templates_cache.get(agent, "")