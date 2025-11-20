"""
Report generator service for creating comprehensive meeting reports.
Aggregates all analyses and generates structured reports.
"""
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from backend.config import settings
from backend.utils.logger import log
from backend.models.schemas import (
    ReportResponse, FactCheck, BlindSpotsAnalysis,
    Recommendation, TranscriptionSegment
)
from backend.services.fact_checker import get_fact_checker_service
from backend.services.blind_spots_detector import get_blind_spots_detector_service
from anthropic import Anthropic
import json
import re
import markdown2


class ReportGeneratorService:
    """Service for generating comprehensive meeting reports."""

    def __init__(self):
        """Initialize the report generator service."""
        self.claude_client = Anthropic(api_key=settings.anthropic_api_key)
        self.fact_checker = get_fact_checker_service()
        self.blind_spots_detector = get_blind_spots_detector_service()
        self.reports_dir = Path(settings.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def generate_report(
        self,
        meeting_id: str,
        meeting_data: Dict[str, Any],
        transcription_segments: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive meeting report.

        Args:
            meeting_id: Meeting identifier
            meeting_data: Meeting metadata
            transcription_segments: List of transcription segments
            alerts: List of real-time alerts

        Returns:
            Complete report data
        """
        try:
            log.info(f"Generating report for meeting {meeting_id}")

            # Combine full transcription
            full_transcription = "\n".join([
                f"[{seg.get('start_time', 0):.1f}s] {seg.get('text', '')}"
                for seg in transcription_segments
            ])

            # Generate executive summary
            log.info("Generating executive summary...")
            executive_summary = await self._generate_executive_summary(
                full_transcription, meeting_data
            )

            # Perform fact-checking
            log.info("Performing comprehensive fact-checking...")
            fact_checks = await self.fact_checker.fact_check_meeting(transcription_segments)

            # Detect blind spots
            log.info("Analyzing blind spots...")
            blind_spots = await self.blind_spots_detector.analyze_blind_spots(
                full_transcription, meeting_data
            )

            # Generate recommendations
            log.info("Generating recommendations...")
            recommendations = await self._generate_recommendations(
                full_transcription,
                fact_checks,
                blind_spots,
                alerts
            )

            # Create report object
            report_data = {
                "id": f"report_{meeting_id}_{int(datetime.now().timestamp())}",
                "meeting_id": meeting_id,
                "generated_at": datetime.now(),
                "executive_summary": executive_summary,
                "full_transcription": transcription_segments,
                "fact_checks": [fc.dict() for fc in fact_checks],
                "blind_spots": blind_spots.dict(),
                "recommendations": [rec.dict() for rec in recommendations],
                "language": meeting_data.get("language", "fr"),
                "metadata": {
                    "meeting_title": meeting_data.get("title", ""),
                    "meeting_date": str(meeting_data.get("date", "")),
                    "participants": meeting_data.get("participants", []),
                    "duration": meeting_data.get("duration", 0),
                    "alert_count": len(alerts),
                    "fact_check_summary": self.fact_checker.get_fact_check_summary(fact_checks)
                }
            }

            # Save report to file
            await self._save_report(report_data)

            log.info(f"Report generation complete for meeting {meeting_id}")
            return report_data

        except Exception as e:
            log.error(f"Error generating report: {e}")
            raise

    async def _generate_executive_summary(
        self,
        transcription: str,
        meeting_data: Dict[str, Any]
    ) -> str:
        """
        Generate an executive summary of the meeting.

        Args:
            transcription: Full meeting transcription
            meeting_data: Meeting metadata

        Returns:
            Executive summary text
        """
        try:
            prompt = f"""Tu es un assistant exécutif expert en synthèse de réunions de direction.

INFORMATIONS DE LA RÉUNION:
Titre: {meeting_data.get('title', 'N/A')}
Date: {meeting_data.get('date', 'N/A')}
Participants: {', '.join(meeting_data.get('participants', []))}
Durée: {meeting_data.get('duration', 0)} secondes

TRANSCRIPTION COMPLÈTE:
{transcription[:20000]}

TÂCHE: Génère un résumé exécutif professionnel en français qui couvre:

1. **Contexte et Objectif** (2-3 phrases)
   - Pourquoi cette réunion a eu lieu
   - Objectifs principaux

2. **Points Clés Discutés** (liste à puces)
   - 5-7 points principaux
   - Chiffres et faits importants mentionnés

3. **Décisions Prises** (liste à puces)
   - Décisions majeures
   - Responsables si mentionnés

4. **Actions à Suivre** (liste à puces)
   - Actions identifiées
   - Échéances si mentionnées

5. **Conclusion** (2-3 phrases)
   - Ton général de la réunion
   - Prochaines étapes

Format: Markdown professionnel et concis (max 600 mots)."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=2048,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text
            log.info("Executive summary generated")
            return summary

        except Exception as e:
            log.error(f"Error generating executive summary: {e}")
            return "Erreur lors de la génération du résumé exécutif."

    async def _generate_recommendations(
        self,
        transcription: str,
        fact_checks: List[FactCheck],
        blind_spots: BlindSpotsAnalysis,
        alerts: List[Dict[str, Any]]
    ) -> List[Recommendation]:
        """
        Generate actionable recommendations based on all analyses.

        Args:
            transcription: Full transcription
            fact_checks: Fact-checking results
            blind_spots: Blind spots analysis
            alerts: Real-time alerts

        Returns:
            List of recommendations
        """
        try:
            # Prepare context
            inaccurate_facts = [
                fc for fc in fact_checks if not fc.is_accurate
            ]

            context = f"""ANALYSES:

Faits Incorrects Détectés: {len(inaccurate_facts)}
{chr(10).join([f"- {fc.statement}: {fc.explanation}" for fc in inaccurate_facts[:5]])}

Risques Non Mentionnés: {len(blind_spots.unmentioned_risks)}
{chr(10).join([f"- {r.get('description', '')}" for r in blind_spots.unmentioned_risks[:3]])}

Opportunités Manquées: {len(blind_spots.missed_opportunities)}
{chr(10).join([f"- {o.get('description', '')}" for o in blind_spots.missed_opportunities[:3]])}

Contraintes Oubliées: {len(blind_spots.forgotten_constraints)}

Alertes Temps Réel: {len(alerts)}"""

            prompt = f"""Tu es un consultant stratégique donnant des recommandations actionnables.

CONTEXTE:
{context}

TRANSCRIPTION (extraits):
{transcription[:5000]}

TÂCHE: Génère 5-10 RECOMMANDATIONS ACTIONNABLES prioritaires.

Chaque recommandation doit avoir:
- priority: "high", "medium", ou "low"
- category: "strategy", "operations", "risk_management", "quality", "communication", "resources"
- title: Titre court et clair
- description: Description détaillée (2-4 phrases)
- rationale: Pourquoi c'est important
- expected_impact: Impact attendu si mise en œuvre

Réponds avec JSON:
{{
    "recommendations": [
        {{
            "priority": "high",
            "category": "category",
            "title": "titre",
            "description": "description",
            "rationale": "justification",
            "expected_impact": "impact"
        }}
    ]
}}

Concentre-toi sur les recommandations les plus impactantes."""

            response = self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=3072,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                recommendations_data = result.get("recommendations", [])

                recommendations = [
                    Recommendation(**rec) for rec in recommendations_data
                ]

                log.info(f"Generated {len(recommendations)} recommendations")
                return recommendations
            else:
                log.warning("Could not parse recommendations response")
                return []

        except Exception as e:
            log.error(f"Error generating recommendations: {e}")
            return []

    async def _save_report(self, report_data: Dict[str, Any]) -> Path:
        """
        Save report to disk.

        Args:
            report_data: Complete report data

        Returns:
            Path to saved report
        """
        try:
            report_id = report_data["id"]
            report_path = self.reports_dir / f"{report_id}.json"

            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)

            log.info(f"Report saved to {report_path}")
            return report_path

        except Exception as e:
            log.error(f"Error saving report: {e}")
            raise

    def load_report(self, report_id: str) -> Dict[str, Any]:
        """
        Load a report from disk.

        Args:
            report_id: Report identifier

        Returns:
            Report data
        """
        try:
            report_path = self.reports_dir / f"{report_id}.json"

            if not report_path.exists():
                raise FileNotFoundError(f"Report {report_id} not found")

            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)

            return report_data

        except Exception as e:
            log.error(f"Error loading report: {e}")
            raise

    async def export_report_to_markdown(self, report_data: Dict[str, Any]) -> str:
        """
        Export report to markdown format.

        Args:
            report_data: Report data

        Returns:
            Markdown text
        """
        try:
            md = []

            # Header
            metadata = report_data.get("metadata", {})
            md.append(f"# Rapport de Réunion")
            md.append(f"\n**{metadata.get('meeting_title', 'Sans titre')}**\n")
            md.append(f"Date: {metadata.get('meeting_date', 'N/A')}")
            md.append(f"Durée: {metadata.get('duration', 0) // 60} minutes")
            md.append(f"Participants: {', '.join(metadata.get('participants', []))}")
            md.append(f"Généré le: {report_data.get('generated_at', '')}\n")

            md.append("---\n")

            # Executive Summary
            md.append("## Résumé Exécutif\n")
            md.append(report_data.get("executive_summary", ""))
            md.append("\n---\n")

            # Fact Checks
            md.append("## Vérification des Faits\n")
            fact_checks = report_data.get("fact_checks", [])
            if fact_checks:
                summary = metadata.get("fact_check_summary", {})
                md.append(f"**Statistiques:** {summary.get('accurate_statements', 0)}/{summary.get('total_statements', 0)} affirmations vérifiées comme exactes ({summary.get('accuracy_rate', 0)}%)\n")

                # Show inaccurate facts
                inaccurate = [fc for fc in fact_checks if not fc.get("is_accurate")]
                if inaccurate:
                    md.append("\n### ⚠️ Affirmations Nécessitant une Attention\n")
                    for fc in inaccurate:
                        md.append(f"\n**Affirmation:** {fc.get('statement')}")
                        md.append(f"\n- **Confiance:** {fc.get('confidence_score')}%")
                        md.append(f"\n- **Explication:** {fc.get('explanation')}")
                        if fc.get('contradictions'):
                            md.append(f"\n- **Contradictions:** {', '.join(fc.get('contradictions'))}")
                        md.append("\n")
            else:
                md.append("Aucune affirmation factuelle n'a été identifiée.\n")

            md.append("\n---\n")

            # Blind Spots
            md.append("## Analyse des Angles Morts\n")
            blind_spots = report_data.get("blind_spots", {})

            if blind_spots.get("unmentioned_risks"):
                md.append("\n### 🚨 Risques Non Mentionnés\n")
                for risk in blind_spots["unmentioned_risks"]:
                    md.append(f"\n**{risk.get('type', 'N/A')}** ({risk.get('probability', 'N/A')})")
                    md.append(f"\n- {risk.get('description', '')}")
                    md.append(f"\n- Impact: {risk.get('impact', '')}\n")

            if blind_spots.get("missed_opportunities"):
                md.append("\n### 💡 Opportunités Manquées\n")
                for opp in blind_spots["missed_opportunities"]:
                    md.append(f"\n**{opp.get('type', 'N/A')}** (Valeur: {opp.get('potential_value', 'N/A')})")
                    md.append(f"\n- {opp.get('description', '')}\n")

            if blind_spots.get("forgotten_constraints"):
                md.append("\n### 🔒 Contraintes Oubliées\n")
                constraints = blind_spots["forgotten_constraints"]
                for category, items in constraints.items():
                    if items:
                        md.append(f"\n**{category.replace('_', ' ').title()}:**")
                        for item in items:
                            md.append(f"\n- {item}")
                        md.append("\n")

            md.append("\n---\n")

            # Recommendations
            md.append("## Recommandations\n")
            recommendations = report_data.get("recommendations", [])
            if recommendations:
                # Group by priority
                high_priority = [r for r in recommendations if r.get("priority") == "high"]
                medium_priority = [r for r in recommendations if r.get("priority") == "medium"]
                low_priority = [r for r in recommendations if r.get("priority") == "low"]

                if high_priority:
                    md.append("\n### 🔴 Priorité Haute\n")
                    for rec in high_priority:
                        md.append(f"\n**{rec.get('title')}** ({rec.get('category')})")
                        md.append(f"\n{rec.get('description')}")
                        md.append(f"\n\n*Justification:* {rec.get('rationale')}")
                        md.append(f"\n\n*Impact attendu:* {rec.get('expected_impact')}\n")

                if medium_priority:
                    md.append("\n### 🟡 Priorité Moyenne\n")
                    for rec in medium_priority:
                        md.append(f"\n**{rec.get('title')}** ({rec.get('category')})")
                        md.append(f"\n{rec.get('description')}\n")

                if low_priority:
                    md.append("\n### 🟢 Priorité Basse\n")
                    for rec in low_priority:
                        md.append(f"\n**{rec.get('title')}** - {rec.get('description')}\n")

            md.append("\n---\n")

            # Transcription
            md.append("## Transcription Complète\n")
            transcription = report_data.get("full_transcription", [])
            for segment in transcription:
                timestamp = segment.get("start_time", 0)
                text = segment.get("text", "")
                md.append(f"\n**[{timestamp:.1f}s]** {text}")

            return "\n".join(md)

        except Exception as e:
            log.error(f"Error exporting report to markdown: {e}")
            raise


# Global instance
_report_generator_service = None


def get_report_generator_service() -> ReportGeneratorService:
    """Get or create the global report generator service instance."""
    global _report_generator_service
    if _report_generator_service is None:
        _report_generator_service = ReportGeneratorService()
    return _report_generator_service
