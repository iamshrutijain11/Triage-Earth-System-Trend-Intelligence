"""Reporting modules: bilingual situation reports and radio summaries."""

from backend.triage.report.build_report import (
    format_template_context,
    generate_situation_reports,
)
from backend.triage.report.sms_summary import (
    ATTRIBUTION_SHORT,
    generate_sms_summary,
)

# Contract interface alias: report.build(...)
build = generate_situation_reports

__all__ = [
    "build",
    "format_template_context",
    "generate_situation_reports",
    "generate_sms_summary",
    "ATTRIBUTION_SHORT",
]
