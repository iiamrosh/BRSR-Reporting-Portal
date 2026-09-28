from __future__ import annotations

from typing import Any


def n(key: str, label: str, unit: str = "", required: bool = True, **extra: Any) -> dict[str, Any]:
    return {"key": key, "label": label, "type": "number", "unit": unit, "required": required, "min": 0, **extra}


def t(key: str, label: str, required: bool = True, long: bool = False, **extra: Any) -> dict[str, Any]:
    return {"key": key, "label": label, "type": "textarea" if long else "text", "required": required, **extra}


def yn(key: str, label: str, required: bool = True) -> dict[str, Any]:
    return {"key": key, "label": label, "type": "yes_no_na", "required": required, "options": ["Yes", "No", "Not applicable"]}


def table(key: str, label: str, columns: list[dict[str, Any]], rows: list[dict[str, str]] | None = None, required: bool = True, help_text: str = "") -> dict[str, Any]:
    return {"key": key, "label": label, "type": "table", "required": required, "columns": columns, "rows": rows or [], "helpText": help_text}


def col(key: str, label: str, kind: str = "text", unit: str = "", required: bool = True, options: list[str] | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"key": key, "label": label, "type": kind, "required": required}
    if unit: item["unit"] = unit
    if options: item["options"] = options
    return item


def metric_columns(unit: str, three_years: bool = False) -> list[dict[str, Any]]:
    cols = [col("metric", "Parameter"), col("unit", "Unit", "text", required=False), col("current_year", "FY 2025–26", "number", unit)]
    cols.append(col("previous_year", "FY 2024–25", "number", unit, False))
    if three_years: cols.append(col("prior_previous_year", "FY 2023–24", "number", unit, False))
    return cols


FORM_SCHEMAS: dict[str, list[dict[str, Any]]] = {
    "A-14": [table("business_activities", "Business activities accounting for 90% of turnover", [col("activity", "Main activity"), col("description", "Description of business activity", "textarea"), col("turnover_percent", "% of turnover", "number", "%")], help_text="Add one row for each material business activity; percentages should reconcile to the represented turnover."), t("boundary_note", "Reporting boundary and basis", True, True)],
    "A-15": [table("products_services", "Products and services accounting for 90% of turnover", [col("product", "Product / service"), col("nic_code", "NIC Group / Class / Sub-class"), col("turnover_percent", "% of turnover", "number", "%")]), t("classification_note", "NIC classification note", False, True)],
    "A-18": [table("workforce", "Employees and workers by contract and gender", [col("category", "Category", "select", options=["Permanent employees", "Other than permanent employees", "Permanent workers", "Other than permanent workers"]), col("male", "Male (A)", "number", "count"), col("female", "Female (B)", "number", "count"), col("other", "Other (C)", "number", "count", False), col("total", "Total (A+B+C)", "number", "count"), col("female_percent", "Female %", "number", "%", False)]), t("workforce_scope", "Scope, methodology and exclusions", True, True)],
    "A-20": [table("turnover", "Turnover rate of permanent employees and workers", [col("category", "Category", "select", options=["Permanent employees", "Permanent workers"]), col("gender", "Gender", "select", options=["Male", "Female", "Total"]), col("current_year", "FY 2025–26", "number", "%"), col("previous_year", "FY 2024–25", "number", "%", False), col("prior_previous_year", "FY 2023–24", "number", "%", False)]), t("turnover_methodology", "Calculation basis and significant movement", True, True)],
    "A-23": [table("grievances", "Stakeholder grievance mechanisms and complaints", [col("stakeholder", "Stakeholder group"), col("mechanism", "Mechanism / channel", "textarea"), col("current_filed", "FY26 filed", "number", "count"), col("current_pending", "FY26 pending", "number", "count"), col("previous_filed", "FY25 filed", "number", "count", False), col("previous_pending", "FY25 pending", "number", "count", False), col("remarks", "Remarks", "textarea", required=False)]), t("escalation_process", "Escalation, oversight and remediation process", True, True)],
    "A-24": [table("material_topics", "Material risks and opportunities", [col("topic", "Material issue"), col("type", "Risk / opportunity", "select", options=["Risk", "Opportunity"]), col("rationale", "Rationale and expected impact", "textarea"), col("approach", "Mitigation / adaptation approach", "textarea"), col("financial_implications", "Financial implications", "textarea")]), t("materiality_method", "Materiality assessment methodology", True, True)],
    "B-05": [table("principle_matrix", "Policy and management process matrix", [col("question", "Management process question"), *[col(f"p{i}", f"P{i}", "yes_no_na") for i in range(1, 10)]], rows=[{"question": q} for q in ["Policy coverage", "Board approval", "Policy translated into procedures", "Extended to value-chain partners", "National / international certification"]]), t("policy_links", "Policy links and key procedures", False, True), table("targets", "Commitments, goals and performance", [col("principle", "Principle"), col("commitment", "Commitment / goal"), col("target", "Target and target year"), col("performance", "Performance achieved"), col("variance", "Variance and corrective action", "textarea")])],
    "B-08": [t("leadership_statement", "Director responsible for the BRSR — statement", True, True), t("responsible_authority", "Highest authority responsible for implementation", True), yn("sustainability_committee", "Does the entity have a Board / Director-level sustainability committee?"), t("committee_details", "Committee composition, mandate and review cadence", True, True), table("review_matrix", "Review of NGRBC policies and performance", [col("review_area", "Review area"), *[col(f"p{i}", f"P{i}", "select", options=["Quarterly", "Half-yearly", "Annually", "Need-based", "Not applicable"]) for i in range(1, 10)]]), yn("independent_evaluation", "Were policies independently evaluated?"), t("na_reasons", "Reasons for any not-applicable principle", False, True)],
    "P1-E2": [table("penalties", "Monetary and non-monetary proceedings", [col("type", "Monetary / non-monetary"), col("regulator", "Regulatory / enforcement agency"), col("amount", "Amount", "number", "INR"), col("brief", "Brief of the case", "textarea"), col("appeal", "Appeal preferred?", "yes_no_na")]), t("corrective_action", "Corrective action and control improvement", False, True)],
    "P2-E2": [table("sourcing", "Sustainable sourcing coverage", [col("input_category", "Input category"), col("current_year", "FY 2025–26", "number", "%"), col("previous_year", "FY 2024–25", "number", "%", False), col("standard", "Standard / certification"), col("scope", "Coverage and exclusions", "textarea")]), t("methodology", "Sustainable-sourcing methodology", True, True)],
    "P3-E5": [table("parental_leave", "Return-to-work and retention after parental leave", [col("gender", "Gender", "select", options=["Male", "Female", "Other", "Total"]), col("entitled", "Entitled", "number", "count"), col("availed", "Availed", "number", "count"), col("returned", "Returned", "number", "count"), col("retained", "Retained 12 months", "number", "count"), col("return_rate", "Return rate", "number", "%"), col("retention_rate", "Retention rate", "number", "%")]), t("leave_note", "Policy scope and calculation note", False, True)],
    "P3-E11": [table("safety_metrics", "Safety incidents", [col("metric", "Safety metric", "select", options=["LTIFR", "Total recordable injuries", "Fatalities", "High-consequence injuries"]), col("population", "Employee / worker", "select", options=["Employees", "Workers"]), col("current_year", "FY 2025–26", "number"), col("previous_year", "FY 2024–25", "number", required=False), col("unit", "Unit")]), n("hours_worked", "Total hours worked", "hours"), t("safety_methodology", "Definitions, boundary and corrective actions", True, True)],
    "P4-E2": [table("stakeholders", "Stakeholder identification and engagement", [col("group", "Stakeholder group"), col("identified_vulnerable", "Vulnerable / marginalised?", "yes_no_na"), col("channels", "Engagement channels", "textarea"), col("frequency", "Frequency"), col("topics", "Key topics and concerns", "textarea"), col("response", "Management response", "textarea")])],
    "P5-E1": [table("training", "Human-rights training coverage", [col("category", "Category", "select", options=["Permanent employees", "Other employees", "Permanent workers", "Other workers"]), col("total", "Total (A)", "number", "count"), col("covered", "Covered (B)", "number", "count"), col("coverage", "% (B/A)", "number", "%"), col("previous_coverage", "Prior-year %", "number", "%", False)]), t("training_topics", "Training topics and delivery approach", True, True)],
    "P5-E6": [table("complaints", "Human-rights complaints", [col("category", "Complaint category"), col("current_filed", "FY26 filed", "number", "count"), col("current_pending", "FY26 pending", "number", "count"), col("previous_filed", "FY25 filed", "number", "count", False), col("previous_pending", "FY25 pending", "number", "count", False), col("remarks", "Remarks", "textarea", required=False)]), t("remediation", "Remediation and prevention measures", True, True)],
    "P6-E1": [table("energy", "Energy consumption", metric_columns("GJ"), rows=[{"metric": x, "unit": "GJ"} for x in ["Renewable electricity", "Renewable fuel", "Other renewable sources", "Non-renewable electricity", "Non-renewable fuel", "Other non-renewable sources", "Total energy (A+B+C)"]]), n("turnover", "Turnover", "INR crore", False), n("ppp_revenue", "Revenue adjusted for PPP", "INR crore", False), n("intensity_turnover", "Energy intensity per turnover", "GJ / INR crore", False), n("intensity_ppp", "Energy intensity per PPP revenue", "GJ / INR crore", False), t("energy_methodology", "Boundary, methodology, variance and restatement note", True, True)],
    "P6-E3": [table("water_withdrawal", "Water withdrawal by source", metric_columns("kL"), rows=[{"metric": x, "unit": "kL"} for x in ["Surface water", "Groundwater", "Third-party water", "Seawater / desalinated water", "Other sources", "Total withdrawal", "Total consumption"]]), n("water_intensity_turnover", "Water intensity per turnover", "kL / INR crore", False), table("water_discharge", "Water discharge", [col("destination", "Destination"), col("treatment", "Treatment level"), col("current_year", "FY 2025–26", "number", "kL"), col("previous_year", "FY 2024–25", "number", "kL", False)]), t("water_methodology", "Boundary, methodology and variance note", True, True)],
    "P6-E6": [table("ghg", "Scope 1 and Scope 2 GHG emissions", metric_columns("tCO2e"), rows=[{"metric": "Scope 1 emissions", "unit": "tCO2e"}, {"metric": "Scope 2 emissions", "unit": "tCO2e"}, {"metric": "Total Scope 1 + Scope 2", "unit": "tCO2e"}]), n("ghg_intensity_turnover", "GHG intensity per turnover", "tCO2e / INR crore", False), n("ghg_intensity_ppp", "GHG intensity per PPP revenue", "tCO2e / INR crore", False), t("methodology", "Methodology, emission factors, boundary and restatements", True, True)],
    "P6-E8": [table("waste_generation", "Waste generated by category", metric_columns("tonnes"), rows=[{"metric": x, "unit": "tonnes"} for x in ["Plastic waste", "E-waste", "Bio-medical waste", "Construction and demolition waste", "Battery waste", "Radioactive waste", "Other hazardous waste", "Other non-hazardous waste", "Total waste generated"]]), table("waste_treatment", "Waste recovered and disposed", [col("route", "Recovery / disposal route"), col("current_year", "FY 2025–26", "number", "tonnes"), col("previous_year", "FY 2024–25", "number", "tonnes", False)]), t("waste_methodology", "Measurement basis, boundary and variance note", True, True)],
    "P7-L1": [table("policy_positions", "Public-policy positions", [col("issue", "Public policy advocated"), col("method", "Method of advocacy"), col("association", "Industry association"), col("board_review", "Board review frequency"), col("alignment", "Web link / responsible-business alignment", "textarea")]), t("governance_alignment", "Governance and alignment statement", True, True)],
    "P8-E4": [table("procurement", "Input sourcing", [col("category", "Sourcing category", "select", options=["MSMEs / small producers", "Within India"]), col("current_year", "FY 2025–26", "number", "%"), col("previous_year", "FY 2024–25", "number", "%", False), col("basis", "Calculation basis", "textarea")])],
    "P8-L6": [table("csr_projects", "CSR beneficiaries", [col("project", "CSR project"), col("beneficiaries", "Total beneficiaries", "number", "count"), col("vulnerable_percent", "% vulnerable / marginalised", "number", "%"), col("location", "Location"), col("outcome", "Outcome / impact", "textarea")]), t("assessment_method", "Beneficiary identification and impact assessment method", True, True)],
    "P9-E4": [table("recalls", "Product recalls", [col("recall_type", "Recall type", "select", options=["Voluntary", "Forced"]), col("count", "Number", "number", "count"), col("reason", "Reason for recall", "textarea"), col("corrective_action", "Corrective action", "textarea")]), table("consumer_complaints", "Consumer complaints", [col("category", "Category"), col("current_received", "FY26 received", "number", "count"), col("current_pending", "FY26 pending", "number", "count"), col("previous_received", "FY25 received", "number", "count", False), col("previous_pending", "FY25 pending", "number", "count", False)]), t("product_safety_note", "Product safety governance and trend explanation", True, True)],
}


def form_schema(disclosure: Any) -> list[dict[str, Any]]:
    return FORM_SCHEMAS.get(disclosure.id, [t("response", "Disclosure response", True, True), t("methodology", "Methodology, scope and variance note", False, True)])


def _number(value: Any) -> float | None:
    try: return float(value) if value not in (None, "") else None
    except (TypeError, ValueError): return None


def validate_response(disclosure: Any, value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in form_schema(disclosure):
        raw = value.get(field["key"])
        if field.get("required") and raw in (None, "", []): errors.append(f'{field["label"]} is required')
        if field["type"] == "number" and raw not in (None, ""):
            number = _number(raw)
            if number is None: errors.append(f'{field["label"]} must be numeric')
            elif field.get("min") is not None and number < field["min"]: errors.append(f'{field["label"]} must be at least {field["min"]}')
        if field["type"] == "table" and isinstance(raw, list):
            for index, row in enumerate(raw, 1):
                for column in field.get("columns", []):
                    cell = row.get(column["key"])
                    if column.get("required") and cell in (None, ""): errors.append(f'{field["label"]}, row {index}: {column["label"]} is required')
                    if column.get("type") == "number" and cell not in (None, "") and _number(cell) is None: errors.append(f'{field["label"]}, row {index}: {column["label"]} must be numeric')
    return errors


def quality_score(errors: list[str], has_evidence: bool, evidence_required: bool) -> int:
    return max(0, 100 - min(60, len(errors) * 15) - (20 if evidence_required and not has_evidence else 0))
