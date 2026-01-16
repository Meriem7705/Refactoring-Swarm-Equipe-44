import json
from typing import List, Dict, Optional
from pathlib import Path


class PromptManager:
    """
    Gère le chargement, le stockage et le formatage des prompts pour tous les agents.
    Injecte dynamiquement le contexte (code, résultats, tests) dans les templates.
    """

    def __init__(self, templates_dir: str = "prompts"):
        """
        Initialisation du gestionnaire de prompts.

        Args:
            templates_dir: Répertoire contenant les fichiers de templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_cache: Dict[str, str] = {}
        self._load_templates()

    def _load_templates(self):
        """Charge tous les templates depuis le disque"""
        files_map = {
            "auditor": "auditor_prompt.txt",
            "fixer": "fixer_prompt.txt",
            "judge": "judge_prompt.txt"
        }
        for agent, filename in files_map.items():
            file_path = self.templates_dir / filename
            if file_path.exists():
                with open(file_path, encoding="utf-8") as f:
                    self.templates_cache[agent] = f.read()
                print(f"✅ Template chargé pour {agent}")
            else:
                print(f"⚠️ Template manquant : {filename}")
                self.templates_cache[agent] = ""

    # =================== AUDITOR ===================

    def build_auditor_prompt(self, file_name: str, content: str, lint_data: Optional[Dict] = None) -> str:
        """
        Prépare le prompt pour l'agent Auditor.

        Args:
            file_name: Chemin du fichier
            content: Contenu du code
            lint_data: Résultats de lint optionnels (pylint)

        Returns:
            Prompt complet prêt à envoyer au LLM
        """
        template = self.templates_cache.get("auditor", "")
        context = f"FICHIER: {file_name}\n\nCODE:\n```python\n{content}\n```\n"

        if lint_data and lint_data.get("success"):
            context += f"\nLINT:\n- Score: {lint_data.get('score', 'N/A')}/10\n"
            issues = lint_data.get("categorized", {})
            context += f"- Erreurs: {len(issues.get('error', []))}\n- Avertissements: {len(issues.get('warning', []))}\n"
            context += "- Top problèmes:\n"
            for i, issue in enumerate(lint_data.get("issues", [])[:5], 1):
                context += f"{i}. Ligne {issue.get('line', '?')}: {issue.get('message', 'Inconnu')}\n"

        return f"{template}\n\n{context}\nVeuillez fournir votre analyse au format JSON."

    # =================== FIXER ===================

    def build_fixer_prompt(self, file_name: str, content: str, plan: List[Dict], prev_errors: Optional[List[str]] = None) -> str:
        """
        Prépare le prompt pour l'agent Fixer avec le plan de refactoring.

        Args:
            file_name: Fichier à corriger
            content: Contenu actuel du fichier
            plan: Plan de refactoring issu de l'Auditor
            prev_errors: Erreurs précédentes pour self-healing

        Returns:
            Prompt complet pour corriger le code
        """
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
            context += "\nVeuillez corriger ces erreurs également.\n"

        context += "\nIMPORTANT:\n- Retourner uniquement le code corrigé, sans explications.\n- Respecter PEP8 et ajouter les docstrings manquantes.\n"
        context += "Fournir le code complet corrigé :"
        return f"{template}\n\n{context}"

    def build_fixer_prompt_from_tests(self, file_name: str, content: str, test_log: str, test_stats: Dict) -> str:
        """
        Prompt pour Fixer basé sur les résultats de tests échoués.

        Args:
            file_name: Fichier ayant échoué aux tests
            content: Contenu actuel
            test_log: Log de pytest
            test_stats: Statistiques des tests

        Returns:
            Prompt complet pour correction
        """
        template = self.templates_cache.get("fixer", "")
        context = f"FICHIER: {file_name}\n\nCODE ACTUEL:\n```python\n{content}\n```\n"
        context += f"\nTESTS:\n- Passés: {test_stats.get('passed', 0)}\n- Échoués: {test_stats.get('failed', 0)}\n- Erreurs: {test_stats.get('errors', 0)}\n\n"
        context += f"LOG TEST:\n```\n{test_log}\n```\n"
        context += "Analysez les erreurs et corrigez le code pour que tous les tests passent.\nFournir le code complet corrigé :"
        return f"{template}\n\n{context}"

    # =================== JUDGE ===================

    def build_judge_prompt(self, test_log: str, stats: Dict, prev_score: Optional[float] = None, current_score: Optional[float] = None) -> str:
        """
        Prépare le prompt pour l'agent Judge basé sur les résultats de tests.

        Args:
            test_log: Log complet des tests
            stats: Statistiques des tests
            prev_score: Ancien score Pylint
            current_score: Score Pylint actuel

        Returns:
            Prompt complet pour juger la mission
        """
        template = self.templates_cache.get("judge", "")
        context = f"RÉSULTATS DES TESTS:\n- Passés: {stats.get('passed', 0)}\n- Échoués: {stats.get('failed', 0)}\n- Erreurs: {stats.get('errors', 0)}\n- Total: {stats.get('total', 0)}\n"
        if prev_score is not None and current_score is not None:
            improvement = current_score - prev_score
            context += f"\nSCORE PYLINT:\n- Ancien: {prev_score}/10\n- Actuel: {current_score}/10\n- Amélioration: {improvement:+.2f}\n"
        elif current_score is not None:
            context += f"\nSCORE PYLINT:\n- Actuel: {current_score}/10\n- Ancien: N/A\n- Amélioration: N/A\n"
        else:
            context += "\nSCORE PYLINT: N/A\n"

        context += f"\nLOG COMPLET DES TESTS:\n```\n{test_log}\n```\n"
        context += "Analysez et indiquez si le code est prêt. Fournir votre verdict en JSON :"
        return f"{template}\n\n{context}"

    # =================== UTILITAIRES ===================

    def truncate_prompt(self, prompt: str, max_lines: int = 100) -> str:
        """
        Réduit un prompt trop long pour économiser des tokens LLM.

        Args:
            prompt: Texte complet du prompt
            max_lines: Nombre maximal de lignes conservées

        Returns:
            Prompt tronqué
        """
        lines = prompt.splitlines()
        if len(lines) <= max_lines:
            return prompt
        half = max_lines // 2
        return "\n".join(lines[:half] + ["\n... [TRONQUÉ] ...\n"] + lines[-half:])

    def parse_json_response(self, response: str) -> Optional[Dict]:
        """
        Extrait du JSON d'une réponse LLM, supprime les blocs markdown.

        Args:
            response: Texte brut LLM

        Returns:
            Dict JSON ou None
        """
        cleaned = response.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print("❌ Erreur JSON détectée dans la réponse LLM")
            return None

    def get_template(self, agent: str) -> str:
        """Retourne le template brut pour un agent"""
        return self.templates_cache.get(agent, "")

    def reload_templates(self):
        """Recharge tous les templates depuis le disque"""
        self.templates_cache.clear()
        self._load_templates()
        print("🔄 Templates rechargés avec succès")
