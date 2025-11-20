"""
Real-time analysis service for detecting issues during meetings.
Analyzes transcription segments and generates alerts.
"""
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.utils.logger import log
from backend.services.vector_store import get_vector_store
from backend.models.schemas import AlertSeverity
from anthropic import Anthropic
import json
import re


class RealTimeAnalysisService:
    """Service for real-time analysis of meeting transcriptions."""

    def __init__(self):
        """Initialize the real-time analysis service."""
        self.vector_store = get_vector_store()
        self.claude_client = Anthropic(api_key=settings.anthropic_api_key)
        self.analysis_buffer = []  # Buffer recent statements for context
        self.buffer_max_size = 10

    async def analyze_statement(
        self,
        statement: str,
        timestamp: float,
        meeting_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single statement in real-time.

        Args:
            statement: The transcribed statement
            timestamp: Timestamp in the meeting
            meeting_context: Optional context about the meeting

        Returns:
            List of alerts (if any issues detected)
        """
        try:
            log.info(f"Analyzing statement at {timestamp}s: {statement[:50]}...")

            # Add to buffer for context
            self.analysis_buffer.append({
                "timestamp": timestamp,
                "text": statement
            })

            # Keep buffer size limited
            if len(self.analysis_buffer) > self.buffer_max_size:
                self.analysis_buffer.pop(0)

            alerts = []

            # 1. Check for factual claims that can be verified
            factual_alerts = await self._check_factual_claims(statement, timestamp)
            alerts.extend(factual_alerts)

            # 2. Check for logical inconsistencies
            consistency_alerts = await self._check_consistency(statement, timestamp)
            alerts.extend(consistency_alerts)

            # 3. Check for missing context
            context_alerts = await self._check_missing_context(statement, timestamp)
            alerts.extend(context_alerts)

            return alerts

        except Exception as e:
            log.error(f"Error analyzing statement: {e}")
            return []

    async def _check_factual_claims(
        self,
        statement: str,
        timestamp: float
    ) -> List[Dict[str, Any]]:
        """
        Check if the statement contains factual claims that contradict company data.

        Args:
            statement: The statement to check
            timestamp: Timestamp in the meeting

        Returns:
            List of alerts for factual issues
        """
        alerts = []

        try:
            # Extract potential facts (numbers, specific claims)
            has_numbers = bool(re.search(r'\d+', statement))
            has_specific_claim = len(statement.split()) > 5

            if not (has_numbers or has_specific_claim):
                return []  # No specific claims to verify

            # Search for relevant context in vector store
            search_results = self.vector_store.search(statement, n_results=5)

            if not search_results:
                return []  # No relevant data to compare against

            # Use Claude to check for contradictions
            context_docs = "\n\n".join([
                f"Document: {r['metadata'].get('filename', 'Unknown')}\n{r['text']}"
                for r in search_results[:3]
            ])

            prompt = f"""Tu es un vérificateur de faits pour une réunion d'entreprise.

AFFIRMATION FAITE EN RÉUNION:
"{statement}"

DONNÉES DE L'ENTREPRISE:
{context_docs}

ANALYSE:
Cette affirmation contient-elle des informations qui contredisent les données de l'entreprise?

Si OUI, réponds avec un JSON:
{{
    "has_contradiction": true,
    "severity": "warning" ou "critical",
    "issue": "description courte du problème",
    "evidence": "citation des données qui contredisent"
}}

Si NON, réponds avec:
{{
    "has_contradiction": false
}}

JSON uniquement, pas d'explication."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=512,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())

                if analysis.get("has_contradiction"):
                    alerts.append({
                        "timestamp": timestamp,
                        "severity": AlertSeverity(analysis.get("severity", "warning")),
                        "statement": statement,
                        "issue": analysis.get("issue", "Contradiction détectée"),
                        "source_docs": [r['metadata'].get('filename', 'Unknown') for r in search_results[:2]]
                    })

        except Exception as e:
            log.error(f"Error checking factual claims: {e}")

        return alerts

    async def _check_consistency(
        self,
        statement: str,
        timestamp: float
    ) -> List[Dict[str, Any]]:
        """
        Check for logical inconsistencies with previous statements in the meeting.

        Args:
            statement: Current statement
            timestamp: Timestamp in the meeting

        Returns:
            List of alerts for consistency issues
        """
        alerts = []

        try:
            if len(self.analysis_buffer) < 3:
                return []  # Need some history for consistency check

            # Get recent context
            recent_statements = [item["text"] for item in self.analysis_buffer[-5:]]
            context = "\n".join(recent_statements[:-1])  # Exclude current statement

            prompt = f"""Analyse la cohérence logique entre ces affirmations d'une même réunion.

AFFIRMATIONS PRÉCÉDENTES:
{context}

NOUVELLE AFFIRMATION:
"{statement}"

Cette nouvelle affirmation est-elle logiquement cohérente avec ce qui a été dit précédemment?

Si INCOHÉRENT, réponds avec JSON:
{{
    "is_inconsistent": true,
    "issue": "description de l'incohérence"
}}

Si COHÉRENT, réponds avec:
{{
    "is_inconsistent": false
}}

JSON uniquement."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=256,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())

                if analysis.get("is_inconsistent"):
                    alerts.append({
                        "timestamp": timestamp,
                        "severity": AlertSeverity.INFO,
                        "statement": statement,
                        "issue": f"Incohérence détectée: {analysis.get('issue', 'Contradiction avec déclarations précédentes')}",
                        "source_docs": []
                    })

        except Exception as e:
            log.error(f"Error checking consistency: {e}")

        return alerts

    async def _check_missing_context(
        self,
        statement: str,
        timestamp: float
    ) -> List[Dict[str, Any]]:
        """
        Check if important context is missing from the statement.

        Args:
            statement: The statement to check
            timestamp: Timestamp

        Returns:
            List of alerts for missing context
        """
        alerts = []

        try:
            # Look for decision-making language without supporting data
            decision_keywords = [
                "nous devons", "il faut", "je propose", "on va",
                "we should", "we must", "let's", "I propose"
            ]

            has_decision = any(keyword in statement.lower() for keyword in decision_keywords)

            if not has_decision:
                return []  # Not a decision statement

            # Search for relevant context
            search_results = self.vector_store.search(statement, n_results=3)

            if len(search_results) < 2:
                # Not enough context found in knowledge base
                alerts.append({
                    "timestamp": timestamp,
                    "severity": AlertSeverity.INFO,
                    "statement": statement,
                    "issue": "Décision proposée sans référence aux données disponibles",
                    "source_docs": []
                })

        except Exception as e:
            log.error(f"Error checking missing context: {e}")

        return alerts

    def reset_buffer(self):
        """Reset the analysis buffer (e.g., at the start of a new meeting)."""
        self.analysis_buffer = []
        log.info("Analysis buffer reset")


# Global instance
_real_time_analysis_service = None


def get_real_time_analysis_service() -> RealTimeAnalysisService:
    """Get or create the global real-time analysis service instance."""
    global _real_time_analysis_service
    if _real_time_analysis_service is None:
        _real_time_analysis_service = RealTimeAnalysisService()
    return _real_time_analysis_service
