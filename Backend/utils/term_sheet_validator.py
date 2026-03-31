import re
from typing import Any, Dict, List, Tuple


CORE_SECTION_RULES = [
    {
        "key": "title_term_sheet",
        "label": "Term sheet title",
        "weight": 1.0,
        "patterns": [r"\bterm\s*sheet\b"],
    },
    {
        "key": "parties",
        "label": "Parties (company/investor)",
        "weight": 1.0,
        "patterns": [r"\bissuer\b", r"\bcompany\b", r"\binvestor(s)?\b", r"\bparties\b"],
    },
    {
        "key": "security_type",
        "label": "Security type",
        "weight": 1.0,
        "patterns": [
            r"\bseries\s+[a-z]\b",
            r"\bpreferred\s+stock\b",
            r"\bconvertible\s+note\b",
            r"\bsafe\b",
            r"\bsecurities?\s+offered\b",
            r"\binstruments?\b",
            r"\bequity\s+shares?\b",
        ],
    },
    {
        "key": "investment_amount",
        "label": "Investment amount",
        "weight": 1.0,
        "patterns": [
            r"\binvestment\s+amount\b",
            r"\bpurchase\s+price\b",
            r"\$\s?\d[\d,]*(\.\d+)?",
            r"\b\d[\d,]*(\.\d+)?\s?(million|billion|m|k)\b",
        ],
    },
    {
        "key": "valuation_or_price",
        "label": "Valuation or per-share price",
        "weight": 1.0,
        "patterns": [
            r"\bpre[-\s]?money\b",
            r"\bpost[-\s]?money\b",
            r"\bvaluation\b",
            r"\bprice\s+per\s+share\b",
            r"\bcap\s+table\b",
            r"\bpre[-\s]?money\s+valuation\b",
            r"\bpost[-\s]?money\s+valuation\b",
        ],
    },
    {
        "key": "liquidation_preference",
        "label": "Liquidation preference",
        "weight": 1.0,
        "patterns": [r"\bliquidation\s+preference\b", r"\bparticipating\s+preferred\b"],
    },
    {
        "key": "governance",
        "label": "Board/governance",
        "weight": 1.0,
        "patterns": [
            r"\bboard\s+of\s+directors\b",
            r"\bboard\s+composition\b",
            r"\bprotective\s+provisions\b",
            r"\bvoting\s+rights?\b",
        ],
    },
    {
        "key": "investor_rights",
        "label": "Investor rights",
        "weight": 1.0,
        "patterns": [
            r"\binformation\s+rights?\b",
            r"\bpro\s*rata\s+rights?\b",
            r"\bright\s+of\s+first\s+refusal\b",
            r"\bregistration\s+rights?\b",
            r"\banti[-\s]?dilution\b",
            r"\bpre[-\s]?emptive\s+rights?\b",
            r"\binformation\s+rights?\b",
        ],
    },
    {
        "key": "closing_terms",
        "label": "Closing conditions/timeline",
        "weight": 1.0,
        "patterns": [
            r"\bclosing\b",
            r"\bconditions\s+precedent\b",
            r"\bclosing\s+date\b",
            r"\bdefinitive\s+documentation\b",
            r"\bshare\s+subscription\s+and\s+shareholders?\s+agreement\b",
            r"\bsssha\b",
        ],
    },
    {
        "key": "transfer_exit_rights",
        "label": "Transfer/exit rights",
        "weight": 0.8,
        "patterns": [
            r"\bright\s+of\s+first\s+offer\b",
            r"\brofo\b",
            r"\bright\s+of\s+first\s+refusal\b",
            r"\brofr\b",
            r"\btag[-\s]?along\b",
            r"\bdrag[-\s]?along\b",
            r"\bexit\s+rights?\b",
            r"\btransferability\b",
        ],
    },
    {
        "key": "promoter_lockin_vesting",
        "label": "Promoter lock-in/vesting",
        "weight": 0.7,
        "patterns": [
            r"\block[-\s]?in\b",
            r"\bvesting\b",
            r"\bunvested\s+shares?\b",
            r"\bpromoter(s)?\b",
        ],
    },
]


LEGAL_BOILERPLATE_RULES = [
    r"\bconfidential\b",
    r"\bnon[-\s]?binding\b",
    r"\bgoverning\s+law\b",
    r"\bjurisdiction\b",
    r"\bsignature(s)?\b",
]


SUSPICIOUS_PATTERNS = [
    r"\blorem\s+ipsum\b",
    r"\bthis\s+is\s+a\s+fake\b",
    r"\bdummy\s+document\b",
    r"\bsample\s+only\b",
    r"\bresume\b",
    r"\bcurriculum\s+vitae\b",
    r"\beducation\b",
    r"\bwork\s+experience\b",
    r"\bskills\b",
    r"\blinkedin\b",
    r"\bgithub\b",
    r"\bobjective\b",
]


def _find_heading_count(text: str) -> int:
    heading_pattern = re.compile(
        r"(?im)^\s{0,4}[A-Za-z][A-Za-z0-9/&(), \-]{2,80}:\s*.*$|^\s{0,4}[A-Za-z][A-Za-z0-9/&(), \-]{2,80}\s*$"
    )
    headings = heading_pattern.findall(text)
    return len(headings)


def _section_matches(text: str) -> Tuple[List[str], List[str], float]:
    matched_sections: List[str] = []
    missing_sections: List[str] = []
    total_weight = 0.0
    matched_weight = 0.0

    for rule in CORE_SECTION_RULES:
        total_weight += rule["weight"]
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in rule["patterns"]):
            matched_sections.append(rule["label"])
            matched_weight += rule["weight"]
        else:
            missing_sections.append(rule["label"])

    section_score = matched_weight / total_weight if total_weight else 0.0
    return matched_sections, missing_sections, section_score


def validate_term_sheet_structure(text: str) -> Dict[str, Any]:
    if not isinstance(text, str):
        text = ""

    raw_text = text
    normalized_text = " ".join(text.split())
    text_length = len(normalized_text)

    matched_sections, missing_sections, section_score = _section_matches(raw_text)
    heading_count = _find_heading_count(raw_text)
    boilerplate_hits = sum(
        1 for pattern in LEGAL_BOILERPLATE_RULES if re.search(pattern, raw_text, flags=re.IGNORECASE)
    )
    suspicious_hits = [p for p in SUSPICIOUS_PATTERNS if re.search(p, normalized_text, flags=re.IGNORECASE)]

    # Supporting structural signals.
    has_currency = bool(re.search(r"\$\s?\d[\d,]*(\.\d+)?", raw_text))
    has_date = bool(
        re.search(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
            raw_text,
            flags=re.IGNORECASE,
        )
        or re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", raw_text)
    )

    # Weighted composite score (0.0 - 1.0).
    structure_score = (
        0.65 * section_score
        + 0.10 * min(heading_count / 8.0, 1.0)
        + 0.10 * min(boilerplate_hits / 3.0, 1.0)
        + 0.10 * (1.0 if has_currency else 0.0)
        + 0.05 * (1.0 if has_date else 0.0)
    )

    warnings: List[str] = []
    if text_length < 400:
        warnings.append("Document text is very short for a full term sheet.")
    if heading_count < 3:
        warnings.append("Few section-like headings were detected.")
    if suspicious_hits:
        warnings.append("Suspicious placeholder/fake language detected.")
    if len(missing_sections) >= 5:
        warnings.append("Many core term sheet sections are missing.")

    likely_real_structure = structure_score >= 0.55 and not suspicious_hits and text_length >= 250

    return {
        "schema": "nvca_vc_equity_v1",
        "structure_score": round(structure_score, 3),
        "likely_real_structure": likely_real_structure,
        "matched_sections": matched_sections,
        "missing_sections": missing_sections,
        "signals": {
            "text_length": text_length,
            "heading_count": heading_count,
            "has_currency": has_currency,
            "has_date": has_date,
            "boilerplate_hits": boilerplate_hits,
        },
        "warnings": warnings,
    }


def combine_ml_and_structure(ml_prediction: str, validation: Dict[str, Any]) -> Dict[str, Any]:
    score = validation.get("structure_score", 0.0)
    likely_real_structure = bool(validation.get("likely_real_structure"))
    missing_sections = validation.get("missing_sections", [])
    matched_sections = validation.get("matched_sections", [])
    suspicious = any("Suspicious" in warning for warning in validation.get("warnings", []))

    # Hard safety gates first.
    if suspicious:
        final_label = "likely_fake"
        confidence_band = "high"
    elif score < 0.35 and len(matched_sections) < 3:
        final_label = "likely_fake"
        confidence_band = "high"
    elif len(missing_sections) >= 7 and score < 0.5:
        final_label = "likely_fake"
        confidence_band = "high"

    elif ml_prediction == "valid" and likely_real_structure:
        final_label = "likely_real"
        confidence_band = "high" if score >= 0.7 else "medium"
    elif ml_prediction == "invalid" and not likely_real_structure:
        final_label = "likely_fake"
        confidence_band = "high" if score <= 0.35 else "medium"
    elif score >= 0.85 and likely_real_structure:
        final_label = "likely_real"
        confidence_band = "medium"
    elif score <= 0.2 and not likely_real_structure:
        final_label = "likely_fake"
        confidence_band = "medium"
    else:
        final_label = "review_required"
        confidence_band = "low"

    return {
        "label": final_label,
        "confidence_band": confidence_band,
        "ml_prediction": ml_prediction,
        "structure_score": score,
        "notes": (
            "Combined decision from ML classifier and NVCA-style structure validation. "
            "Use 'review_required' cases for manual inspection."
        ),
    }
