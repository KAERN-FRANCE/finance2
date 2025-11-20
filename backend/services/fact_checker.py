"""
Fact-checking service for comprehensive post-meeting analysis.
Verifies all factual claims against company knowledge base.
"""
from typing import List, Dict, Any
from backend.config import settings
from backend.utils.logger import log
from backend.services.vector_store import get_vector_store
from backend.models.schemas import FactCheck
from anthropic import Anthropic
import json
import re


class FactCheckerService:
    """Service for comprehensive fact-checking of meeting content."""

    def __init__(self):
        """Initialize the fact checker service."""
        self.vector_store = get_vector_store()
        self.claude_client = Anthropic(api_key=settings.anthropic_api_key)

    async def extract_factual_statements(self, transcription_text: str) -> List[Dict[str, Any]]:
        """
        Extract all factual statements from transcription.

        Args:
            transcription_text: Full meeting transcription

        Returns:
            List of factual statements with metadata
        """
        try:
            log.info("Extracting factual statements from transcription")

            prompt = f"""Analyse cette transcription de réunion et extrais TOUTES les affirmations factuelles vérifiables.

TRANSCRIPTION:
{transcription_text[:15000]}

Une affirmation factuelle est:
- Un chiffre, KPI, métrique
- Une date, deadline, timing
- Un fait sur un projet, produit, ou initiative
- Une déclaration sur des ressources, budget, personnel
- Une affirmation sur des performances passées ou actuelles

Réponds avec un JSON contenant une liste "statements":
{{
    "statements": [
        {{
            "text": "affirmation exacte",
            "category": "numbers/dates/projects/resources/performance",
            "context": "contexte court"
        }}
    ]
}}

JSON uniquement."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=4096,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                statements = result.get("statements", [])
                log.info(f"Extracted {len(statements)} factual statements")
                return statements
            else:
                log.warning("Could not parse factual statements response")
                return []

        except Exception as e:
            log.error(f"Error extracting factual statements: {e}")
            return []

    async def verify_statement(
        self,
        statement: str,
        context: str = ""
    ) -> FactCheck:
        """
        Verify a single factual statement against company knowledge.

        Args:
            statement: The statement to verify
            context: Additional context

        Returns:
            FactCheck result
        """
        try:
            log.info(f"Verifying statement: {statement[:50]}...")

            # Search for relevant documents
            search_results = self.vector_store.search(statement, n_results=10)

            if not search_results:
                # No relevant data found
                return FactCheck(
                    statement=statement,
                    is_accurate=False,
                    confidence_score=0,
                    explanation="Aucune donnée pertinente trouvée dans la base de connaissances",
                    supporting_sources=[],
                    contradictions=[]
                )

            # Filter results by similarity threshold
            relevant_results = [r for r in search_results if r['similarity'] > 0.7]

            if not relevant_results:
                return FactCheck(
                    statement=statement,
                    is_accurate=False,
                    confidence_score=30,
                    explanation="Données trouvées mais peu pertinentes pour vérifier cette affirmation",
                    supporting_sources=[],
                    contradictions=[]
                )

            # Build context from relevant documents
            context_docs = "\n\n".join([
                f"[Source: {r['metadata'].get('filename', 'Unknown')}]\n{r['text']}"
                for r in relevant_results[:5]
            ])

            # Use Claude for detailed verification
            prompt = f"""Tu es un vérificateur de faits expert pour une entreprise.

AFFIRMATION À VÉRIFIER:
"{statement}"

CONTEXTE ADDITIONNEL:
{context}

DONNÉES DE L'ENTREPRISE:
{context_docs}

ANALYSE REQUISE:
1. Cette affirmation est-elle exacte selon les données?
2. Quel est le niveau de confiance (0-100%)?
3. Quelles sources supportent ou contredisent cette affirmation?
4. Explication détaillée

Réponds avec ce JSON:
{{
    "is_accurate": true/false,
    "confidence_score": 0-100,
    "explanation": "explication détaillée de la vérification",
    "supporting_sources": ["nom des sources qui confirment"],
    "contradictions": ["nom des sources qui contredisent avec détails"]
}}

JSON uniquement."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1024,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                fact_check = FactCheck(
                    statement=statement,
                    is_accurate=result.get("is_accurate", False),
                    confidence_score=result.get("confidence_score", 0),
                    explanation=result.get("explanation", ""),
                    supporting_sources=result.get("supporting_sources", []),
                    contradictions=result.get("contradictions", [])
                )

                log.info(f"Verification complete: {fact_check.confidence_score}% confidence")
                return fact_check
            else:
                raise ValueError("Could not parse verification response")

        except Exception as e:
            log.error(f"Error verifying statement: {e}")
            return FactCheck(
                statement=statement,
                is_accurate=False,
                confidence_score=0,
                explanation=f"Erreur lors de la vérification: {str(e)}",
                supporting_sources=[],
                contradictions=[]
            )

    async def fact_check_meeting(
        self,
        transcription_segments: List[Dict[str, Any]]
    ) -> List[FactCheck]:
        """
        Perform comprehensive fact-checking on entire meeting.

        Args:
            transcription_segments: List of transcription segments

        Returns:
            List of fact-check results
        """
        try:
            log.info("Starting comprehensive fact-checking of meeting")

            # Combine transcription
            full_transcription = "\n".join([
                f"[{seg.get('start_time', 0):.1f}s] {seg.get('text', '')}"
                for seg in transcription_segments
            ])

            # Extract factual statements
            statements = await self.extract_factual_statements(full_transcription)

            if not statements:
                log.warning("No factual statements found to verify")
                return []

            # Verify each statement
            fact_checks = []
            for i, stmt_data in enumerate(statements):
                log.info(f"Verifying statement {i+1}/{len(statements)}")

                statement = stmt_data.get("text", "")
                context = stmt_data.get("context", "")

                fact_check = await self.verify_statement(statement, context)

                # Add timestamp if available
                fact_check.timestamp = self._find_timestamp_for_statement(
                    statement, transcription_segments
                )

                fact_checks.append(fact_check)

            # Log summary
            accurate_count = sum(1 for fc in fact_checks if fc.is_accurate)
            log.info(f"Fact-checking complete: {accurate_count}/{len(fact_checks)} statements verified as accurate")

            return fact_checks

        except Exception as e:
            log.error(f"Error fact-checking meeting: {e}")
            return []

    def _find_timestamp_for_statement(
        self,
        statement: str,
        transcription_segments: List[Dict[str, Any]]
    ) -> float:
        """
        Find the timestamp where a statement was made.

        Args:
            statement: The statement to find
            transcription_segments: List of segments

        Returns:
            Timestamp (or 0 if not found)
        """
        try:
            # Simple search - look for key words from statement
            statement_words = set(statement.lower().split())

            for segment in transcription_segments:
                segment_text = segment.get('text', '').lower()
                segment_words = set(segment_text.split())

                # If significant overlap, assume this is where the statement was made
                overlap = len(statement_words & segment_words)
                if overlap > len(statement_words) * 0.5:
                    return segment.get('start_time', 0)

            return 0

        except Exception:
            return 0

    def get_fact_check_summary(self, fact_checks: List[FactCheck]) -> Dict[str, Any]:
        """
        Generate a summary of fact-check results.

        Args:
            fact_checks: List of fact checks

        Returns:
            Summary statistics
        """
        if not fact_checks:
            return {
                "total_statements": 0,
                "accurate_statements": 0,
                "inaccurate_statements": 0,
                "average_confidence": 0,
                "accuracy_rate": 0
            }

        total = len(fact_checks)
        accurate = sum(1 for fc in fact_checks if fc.is_accurate)
        inaccurate = total - accurate
        avg_confidence = sum(fc.confidence_score for fc in fact_checks) / total

        return {
            "total_statements": total,
            "accurate_statements": accurate,
            "inaccurate_statements": inaccurate,
            "average_confidence": round(avg_confidence, 1),
            "accuracy_rate": round((accurate / total) * 100, 1) if total > 0 else 0
        }


# Global instance
_fact_checker_service = None


def get_fact_checker_service() -> FactCheckerService:
    """Get or create the global fact checker service instance."""
    global _fact_checker_service
    if _fact_checker_service is None:
        _fact_checker_service = FactCheckerService()
    return _fact_checker_service
