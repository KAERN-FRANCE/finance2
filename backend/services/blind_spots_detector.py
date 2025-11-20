"""
Blind spots detector service for identifying gaps in meeting discussions.
Analyzes what wasn't discussed but should have been.
"""
from typing import List, Dict, Any
from backend.config import settings
from backend.utils.logger import log
from backend.services.vector_store import get_vector_store
from backend.models.schemas import BlindSpotsAnalysis
from anthropic import Anthropic
import json
import re


class BlindSpotsDetectorService:
    """Service for detecting blind spots and gaps in meeting discussions."""

    def __init__(self):
        """Initialize the blind spots detector service."""
        self.vector_store = get_vector_store()
        self.claude_client = Anthropic(api_key=settings.anthropic_api_key)

    async def analyze_blind_spots(
        self,
        transcription_text: str,
        meeting_context: Dict[str, Any]
    ) -> BlindSpotsAnalysis:
        """
        Perform comprehensive blind spots analysis.

        Args:
            transcription_text: Full meeting transcription
            meeting_context: Context about the meeting (title, agenda, etc.)

        Returns:
            BlindSpotsAnalysis with all identified gaps
        """
        try:
            log.info("Starting blind spots analysis")

            # Get relevant company context
            company_context = await self._gather_company_context(transcription_text)

            # Perform each type of analysis
            unmentioned_risks = await self._identify_risks(
                transcription_text, company_context, meeting_context
            )

            missed_opportunities = await self._identify_opportunities(
                transcription_text, company_context, meeting_context
            )

            alternative_solutions = await self._identify_alternatives(
                transcription_text, company_context, meeting_context
            )

            forgotten_constraints = await self._identify_constraints(
                transcription_text, company_context, meeting_context
            )

            unconsidered_stakeholders = await self._identify_stakeholders(
                transcription_text, company_context, meeting_context
            )

            improvement_points = await self._identify_improvements(
                transcription_text, company_context, meeting_context
            )

            analysis = BlindSpotsAnalysis(
                unmentioned_risks=unmentioned_risks,
                missed_opportunities=missed_opportunities,
                alternative_solutions=alternative_solutions,
                forgotten_constraints=forgotten_constraints,
                unconsidered_stakeholders=unconsidered_stakeholders,
                improvement_points=improvement_points
            )

            log.info("Blind spots analysis complete")
            return analysis

        except Exception as e:
            log.error(f"Error analyzing blind spots: {e}")
            return BlindSpotsAnalysis()

    async def _gather_company_context(self, transcription_text: str) -> str:
        """
        Gather relevant company context for the discussion.

        Args:
            transcription_text: Meeting transcription

        Returns:
            Formatted company context
        """
        try:
            # Search for relevant documents
            search_results = self.vector_store.search(
                transcription_text[:2000],  # Use beginning of meeting as query
                n_results=15
            )

            # Format context
            context_parts = []
            for result in search_results[:10]:
                context_parts.append(
                    f"[{result['metadata'].get('category', 'unknown')}] "
                    f"{result['metadata'].get('filename', 'Unknown')}:\n"
                    f"{result['text'][:500]}"
                )

            return "\n\n".join(context_parts)

        except Exception as e:
            log.error(f"Error gathering company context: {e}")
            return "Contexte non disponible"

    async def _identify_risks(
        self,
        transcription: str,
        company_context: str,
        meeting_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify unmentioned risks."""
        try:
            prompt = f"""Tu es un conseiller en gestion des risques.

CONTEXTE DE LA RÉUNION:
Titre: {meeting_context.get('title', 'N/A')}
Agenda: {meeting_context.get('agenda', 'N/A')}

DISCUSSION:
{transcription[:10000]}

DONNÉES ENTREPRISE:
{company_context[:5000]}

ANALYSE: Identifie les RISQUES importants qui n'ont PAS été mentionnés dans la discussion mais qui sont pertinents selon:
1. Le contexte de l'entreprise
2. Le sujet de la réunion
3. Les décisions prises

Pour chaque risque, fournis:
- Type (financier, opérationnel, stratégique, légal, réputationnel, technique)
- Description
- Impact potentiel
- Probabilité (faible/moyenne/élevée)

Réponds avec JSON:
{{
    "risks": [
        {{
            "type": "type de risque",
            "description": "description du risque",
            "impact": "impact potentiel",
            "probability": "probabilité"
        }}
    ]
}}

JSON uniquement. Maximum 10 risques les plus importants."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=2048,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("risks", [])

            return []

        except Exception as e:
            log.error(f"Error identifying risks: {e}")
            return []

    async def _identify_opportunities(
        self,
        transcription: str,
        company_context: str,
        meeting_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify missed opportunities."""
        try:
            prompt = f"""Tu es un conseiller stratégique.

CONTEXTE DE LA RÉUNION:
Titre: {meeting_context.get('title', 'N/A')}

DISCUSSION:
{transcription[:10000]}

DONNÉES ENTREPRISE:
{company_context[:5000]}

ANALYSE: Identifie les OPPORTUNITÉS qui auraient dû être mentionnées mais qui ont été oubliées:
- Synergies possibles
- Optimisations évidentes
- Innovations potentielles
- Partenariats
- Économies
- Améliorations de processus

Pour chaque opportunité:
- Type
- Description
- Valeur potentielle (faible/moyenne/élevée)
- Facilité de mise en œuvre

JSON:
{{
    "opportunities": [
        {{
            "type": "type d'opportunité",
            "description": "description",
            "potential_value": "valeur potentielle",
            "ease_of_implementation": "facilité"
        }}
    ]
}}

Maximum 8 opportunités."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=2048,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("opportunities", [])

            return []

        except Exception as e:
            log.error(f"Error identifying opportunities: {e}")
            return []

    async def _identify_alternatives(
        self,
        transcription: str,
        company_context: str,
        meeting_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify alternative solutions."""
        try:
            prompt = f"""Tu es un expert en résolution de problèmes.

DISCUSSION:
{transcription[:10000]}

DONNÉES ENTREPRISE:
{company_context[:5000]}

ANALYSE: Identifie des SOLUTIONS ALTERNATIVES qui n'ont pas été évoquées mais qui pourraient être pertinentes.

Pour chaque alternative:
- Description de la solution
- Avantages par rapport aux solutions discutées
- Inconvénients potentiels
- Faisabilité

JSON:
{{
    "alternatives": [
        {{
            "description": "description de la solution",
            "advantages": "avantages",
            "disadvantages": "inconvénients",
            "feasibility": "faisabilité"
        }}
    ]
}}

Maximum 6 alternatives."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=2048,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("alternatives", [])

            return []

        except Exception as e:
            log.error(f"Error identifying alternatives: {e}")
            return []

    async def _identify_constraints(
        self,
        transcription: str,
        company_context: str,
        meeting_context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Identify forgotten constraints."""
        try:
            prompt = f"""Tu es un analyste de faisabilité.

DISCUSSION:
{transcription[:10000]}

DONNÉES ENTREPRISE:
{company_context[:5000]}

ANALYSE: Identifie les CONTRAINTES qui n'ont pas été mentionnées mais qui sont importantes:

Catégories:
1. Légales/Réglementaires
2. Techniques
3. Budgétaires
4. Temporelles (délais)
5. Ressources Humaines
6. Infrastructure

JSON:
{{
    "legal": ["contrainte 1", "contrainte 2"],
    "technical": ["contrainte 1", "contrainte 2"],
    "budgetary": ["contrainte 1", "contrainte 2"],
    "temporal": ["contrainte 1", "contrainte 2"],
    "human_resources": ["contrainte 1", "contrainte 2"],
    "infrastructure": ["contrainte 1", "contrainte 2"]
}}

Sois concis."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1536,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result

            return {}

        except Exception as e:
            log.error(f"Error identifying constraints: {e}")
            return {}

    async def _identify_stakeholders(
        self,
        transcription: str,
        company_context: str,
        meeting_context: Dict[str, Any]
    ) -> List[str]:
        """Identify unconsidered stakeholders."""
        try:
            prompt = f"""Tu es un expert en gestion des parties prenantes.

DISCUSSION:
{transcription[:10000]}

ANALYSE: Identifie les PARTIES PRENANTES (stakeholders) qui devraient être considérées mais qui n'ont pas été mentionnées:
- Départements internes
- Équipes
- Clients
- Partenaires
- Fournisseurs
- Régulateurs
- Investisseurs
- Utilisateurs finaux

JSON:
{{
    "stakeholders": [
        "nom du stakeholder et pourquoi il devrait être considéré"
    ]
}}

Maximum 8 stakeholders."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1024,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("stakeholders", [])

            return []

        except Exception as e:
            log.error(f"Error identifying stakeholders: {e}")
            return []

    async def _identify_improvements(
        self,
        transcription: str,
        company_context: str,
        meeting_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify improvement points for proposed ideas."""
        try:
            prompt = f"""Tu es un consultant en amélioration continue.

DISCUSSION:
{transcription[:10000]}

DONNÉES ENTREPRISE:
{company_context[:5000]}

ANALYSE: Pour les idées et propositions faites en réunion, identifie des points d'AMÉLIORATION spécifiques et actionnables.

JSON:
{{
    "improvements": [
        {{
            "original_idea": "résumé de l'idée discutée",
            "improvement": "comment l'améliorer",
            "rationale": "pourquoi cette amélioration est pertinente",
            "priority": "high/medium/low"
        }}
    ]
}}

Maximum 6 améliorations."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=2048,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("improvements", [])

            return []

        except Exception as e:
            log.error(f"Error identifying improvements: {e}")
            return []


# Global instance
_blind_spots_detector_service = None


def get_blind_spots_detector_service() -> BlindSpotsDetectorService:
    """Get or create the global blind spots detector service instance."""
    global _blind_spots_detector_service
    if _blind_spots_detector_service is None:
        _blind_spots_detector_service = BlindSpotsDetectorService()
    return _blind_spots_detector_service
