"""Q-SHIELD — Security Evaluation Package (Milestone M17).

Provides deterministic security evaluation, controlled scenario definitions,
confusion-matrix metrics, and automated runner utilities for the Q-SHIELD
detection and decision pipeline.
"""

from __future__ import annotations

from src.evaluation.security_evaluation import (
    CategorySummary,
    ConfusionMatrixMetrics,
    EvaluationCategory,
    EvaluationResult,
    EvaluationScenario,
    EvaluationSummary,
    build_baseline_evaluation_suite,
    evaluate_scenario,
    make_anomalous_channel_evidence,
    make_anomalous_threshold_report,
    make_clean_authorization_evidence,
    make_clean_channel_evidence,
    make_clean_impersonation_evidence,
    make_clean_threshold_report,
    make_conflicting_authorization_evidence,
    make_conflicting_channel_evidence,
    make_conflicting_impersonation_evidence,
    make_unauthorized_authorization_evidence,
    make_violating_channel_evidence,
    make_violating_impersonation_evidence,
    run_security_evaluation,
)

__all__ = [
    "CategorySummary",
    "ConfusionMatrixMetrics",
    "EvaluationCategory",
    "EvaluationResult",
    "EvaluationScenario",
    "EvaluationSummary",
    "build_baseline_evaluation_suite",
    "evaluate_scenario",
    "make_anomalous_channel_evidence",
    "make_anomalous_threshold_report",
    "make_clean_authorization_evidence",
    "make_clean_channel_evidence",
    "make_clean_impersonation_evidence",
    "make_clean_threshold_report",
    "make_conflicting_authorization_evidence",
    "make_conflicting_channel_evidence",
    "make_conflicting_impersonation_evidence",
    "make_unauthorized_authorization_evidence",
    "make_violating_channel_evidence",
    "make_violating_impersonation_evidence",
    "run_security_evaluation",
]

