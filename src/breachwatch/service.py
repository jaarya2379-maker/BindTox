from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .data_loader import load_breach_dataset
from .repository import AlertRepository, InMemoryAlertRepository
from .security import sha256_hex
from .schemas import (
    AlertRecord,
    BreachCheckRequest,
    BreachCheckResponse,
    BreachRecord,
    DashboardSummary,
    MitigationSuggestion,
    PasswordExposureSummary,
    RiskScoreBreakdown,
)


def _rating_from_score(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 55:
        return "elevated"
    if score >= 30:
        return "guarded"
    return "low"


def _calculate_risk(breaches: list[BreachRecord], password_exposed: bool) -> RiskScoreBreakdown:
    score = 0
    reasons: list[str] = []
    severity_weights = {"low": 8, "medium": 15, "high": 22, "critical": 30}

    if breaches:
        score += min(45, len(breaches) * 12)
        reasons.append(f"{len(breaches)} breach record(s) matched this email.")

    for breach in breaches:
        score += severity_weights[breach.severity]

    if password_exposed:
        score += 25
        reasons.append("A password exposure match was detected in the simulated dataset.")

    unique_data_types = {item for breach in breaches for item in breach.data_types}
    if "password" in unique_data_types or "password_hash" in unique_data_types:
        score += 15
        reasons.append("Credential-related data appeared in at least one breach.")

    final_score = min(score, 100)
    return RiskScoreBreakdown(score=final_score, rating=_rating_from_score(final_score), reasons=reasons)


def _build_mitigation_suggestions(
    breaches: list[BreachRecord],
    password_exposed: bool,
    risk: RiskScoreBreakdown,
) -> list[MitigationSuggestion]:
    suggestions: list[MitigationSuggestion] = []
    if password_exposed:
        suggestions.append(
            MitigationSuggestion(
                title="Rotate exposed passwords",
                action="Force a password reset and replace reused credentials with unique passphrases.",
                priority="high",
            )
        )
    if breaches:
        suggestions.append(
            MitigationSuggestion(
                title="Enable phishing watch",
                action="Monitor for targeted phishing because the email appeared in leaked datasets.",
                priority="medium" if risk.score < 80 else "high",
            )
        )
    if risk.score >= 55:
        suggestions.append(
            MitigationSuggestion(
                title="Turn on MFA",
                action="Require MFA for sensitive accounts and review recent sign-ins for suspicious activity.",
                priority="high",
            )
        )
    if any("phone" in breach.data_types for breach in breaches):
        suggestions.append(
            MitigationSuggestion(
                title="Watch for SIM-swap indicators",
                action="Add carrier PIN protections and monitor telecom changes if phone data was exposed.",
                priority="medium",
            )
        )
    if not suggestions:
        suggestions.append(
            MitigationSuggestion(
                title="Keep monitoring",
                action="No active exposure was detected in the sample feed, but continue scheduled checks.",
                priority="low",
            )
        )
    return suggestions


class BreachWatchService:
    def __init__(
        self,
        dataset: list[BreachRecord] | None = None,
        repository: AlertRepository | None = None,
    ) -> None:
        self.dataset = dataset or load_breach_dataset()
        self.repository = repository or InMemoryAlertRepository()

    def check_email(self, request: BreachCheckRequest) -> BreachCheckResponse:
        matched_breaches = [item for item in self.dataset if item.email.lower() == request.email.lower()]
        password_hash = sha256_hex(request.password) if request.password else None
        password_matches = [
            item for item in matched_breaches if item.password_sha256 and item.password_sha256 == password_hash
        ]
        password_exposed = any(item.password_exposed for item in password_matches)

        password_summary = PasswordExposureSummary(
            exposed=password_exposed,
            reused_password_risk=bool(password_matches),
            matched_breach_names=[item.breach_name for item in password_matches],
        )
        risk = _calculate_risk(matched_breaches, password_exposed=password_exposed)
        mitigation_suggestions = _build_mitigation_suggestions(
            matched_breaches,
            password_exposed=password_exposed,
            risk=risk,
        )
        response = BreachCheckResponse(
            email=request.email,
            breaches=matched_breaches,
            password_summary=password_summary,
            risk=risk,
            mitigation_suggestions=mitigation_suggestions,
            checked_at=datetime.now(timezone.utc),
        )
        if matched_breaches:
            self.repository.save_alert(
                AlertRecord(
                    email=request.email,
                    risk_score=risk.score,
                    breach_count=len(matched_breaches),
                    created_at=response.checked_at,
                    status="new",
                )
            )
        return response

    def dashboard_summary(self) -> DashboardSummary:
        email_counter = Counter(item.email for item in self.dataset)
        compromised_accounts = len(email_counter)
        alerts = self.repository.list_alerts(limit=5)
        average_risk = 0.0
        if alerts:
            average_risk = round(sum(item.risk_score for item in alerts) / len(alerts), 2)
        critical_alerts = sum(1 for item in alerts if item.risk_score >= 80)
        monitored_accounts = compromised_accounts + 12
        return DashboardSummary(
            monitored_accounts=monitored_accounts,
            compromised_accounts=compromised_accounts,
            critical_alerts=critical_alerts,
            average_risk_score=average_risk,
            latest_alerts=alerts,
        )
