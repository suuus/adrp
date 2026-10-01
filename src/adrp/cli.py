#!/usr/bin/env python3
"""Read, write, validate, resolve, and explain Ape Decision Record Profile records."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "ape-decision-record/v1"
SOURCE_SCHEMA_VERSION = "ape-decision-source/v1"
QUALITY_SCHEMA_VERSION = "adrp-quality-assessment/v1"
VERSION = "0.1.0"
FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")
DECISION_ID = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
STATUSES = {
    "discovered",
    "draft",
    "under-review",
    "ratified",
    "effective",
    "rejected",
    "deprecated",
    "superseded",
    "expired",
    "revoked",
}
AUTHORITY_STATUSES = {
    "authoritative",
    "advisory",
    "conflicting",
    "unknown",
    "user-confirmed",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "decision_id",
    "record_id",
    "record_version",
    "status",
    "title",
    "decision_statement",
    "context",
    "drivers",
    "alternatives",
    "selected_alternative",
    "rationale",
    "tradeoffs",
    "authority",
    "provenance",
    "lifecycle",
    "consequences",
    "implementation",
    "relationships",
    "autonomy",
    "gaps",
    "ratification",
}
SOURCE_KEYS = {
    "schema_version",
    "decision_id",
    "record_id",
    "record_version",
    "source_uri",
    "snapshot_path",
    "retrieved_at",
    "last_checked_at",
    "record_fingerprint",
    "source_digest",
    "source_etag",
    "assessment",
    "local_disposition",
    "acceptance_basis",
    "accepted_by",
    "scope_confirmed",
    "authority_accepted",
}
QUALITY_DIMENSIONS = {
    "clarity",
    "actionability",
    "fidelity",
    "efficiency",
    "security",
}


class DecisionRecordError(RuntimeError):
    """Raised when a decision record violates the profile."""


def fail(condition: bool, message: str) -> None:
    if not condition:
        raise DecisionRecordError(message)


def read_record(path: Path) -> dict[str, Any]:
    value, _ = read_record_bytes(path)
    return value


def read_record_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except FileNotFoundError as exc:
        raise DecisionRecordError(f"file not found: {path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DecisionRecordError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    fail(isinstance(value, dict), "record must be a JSON object")
    return value, raw


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            os.chmod(temp_path, stat.S_IMODE(path.stat().st_mode))
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def atomic_create(path: Path, content: str) -> None:
    atomic_create_bytes(path, content.encode("utf-8"))


def atomic_create_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise DecisionRecordError(f"refusing to overwrite immutable artifact: {path}") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    fail(isinstance(value, dict), f"{label} must be an object")
    fail(set(value) == keys, f"{label} keys must be {sorted(keys)}")
    return value


def text(value: Any, label: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    fail(isinstance(value, str) and bool(value.strip()), f"{label} must be non-empty text")


def text_list(value: Any, label: str, *, unique: bool = False) -> None:
    fail(isinstance(value, list), f"{label} must be an array")
    fail(all(isinstance(item, str) and item.strip() for item in value), f"{label} must contain text")
    if unique:
        fail(len(value) == len(set(value)), f"{label} must not contain duplicates")


def timestamp(value: Any, label: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    text(value, label)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DecisionRecordError(f"{label} must be an ISO-8601 timestamp") from exc


def parse_moment(value: str, label: str) -> datetime:
    timestamp(value, label)
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    fail(moment.tzinfo is not None, f"{label} must include a timezone")
    return moment.astimezone(timezone.utc)


def validate_tradeoff(value: Any, label: str) -> None:
    item = exact_keys(value, {"impact", "summary", "evidence_refs", "accepted_risks"}, label)
    fail(item["impact"] in {"positive", "negative", "mixed", "neutral", "unknown"}, f"{label}.impact is invalid")
    fail(isinstance(item["summary"], str), f"{label}.summary must be text")
    text_list(item["evidence_refs"], f"{label}.evidence_refs", unique=True)
    text_list(item["accepted_risks"], f"{label}.accepted_risks")


def decision_payload(record: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(record)
    payload.pop("ratification", None)
    return payload


def canonical_bytes(record: dict[str, Any]) -> bytes:
    return json.dumps(
        decision_payload(record),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def fingerprint(record: dict[str, Any]) -> str:
    return f"sha256:{hashlib.sha256(canonical_bytes(record)).hexdigest()}"


def validate_record(record: dict[str, Any], *, require_ratified: bool = False) -> None:
    exact_keys(record, TOP_LEVEL_KEYS, "record")
    fail(record["schema_version"] == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    fail(isinstance(record["decision_id"], str) and DECISION_ID.fullmatch(record["decision_id"]) is not None, "decision_id is invalid")
    try:
        uuid.UUID(record["record_id"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise DecisionRecordError("record_id must be a UUID") from exc
    fail(isinstance(record["record_version"], int) and record["record_version"] >= 1, "record_version must be a positive integer")
    fail(record["status"] in STATUSES, "status is invalid")
    text(record["title"], "title")
    text(record["decision_statement"], "decision_statement")
    text(record["rationale"], "rationale")
    text_list(record["gaps"], "gaps")

    context = exact_keys(record["context"], {"problem", "scope", "stakeholders", "concerns"}, "context")
    text(context["problem"], "context.problem")
    for key in ("scope", "stakeholders", "concerns"):
        text_list(context[key], f"context.{key}", unique=True)

    fail(isinstance(record["drivers"], list), "drivers must be an array")
    for index, value in enumerate(record["drivers"]):
        item = exact_keys(value, {"name", "category", "criterion", "source_refs"}, f"drivers[{index}]")
        text(item["name"], f"drivers[{index}].name")
        fail(item["category"] in {"security", "cost", "compliance", "operations", "architecture", "product", "other"}, f"drivers[{index}].category is invalid")
        text(item["criterion"], f"drivers[{index}].criterion")
        text_list(item["source_refs"], f"drivers[{index}].source_refs", unique=True)

    fail(isinstance(record["alternatives"], list) and record["alternatives"], "alternatives must contain at least one option")
    alternative_ids: list[str] = []
    for index, value in enumerate(record["alternatives"]):
        item = exact_keys(value, {"id", "title", "description", "benefits", "drawbacks", "rejection_reason"}, f"alternatives[{index}]")
        text(item["id"], f"alternatives[{index}].id")
        text(item["title"], f"alternatives[{index}].title")
        fail(isinstance(item["description"], str), f"alternatives[{index}].description must be text")
        text_list(item["benefits"], f"alternatives[{index}].benefits")
        text_list(item["drawbacks"], f"alternatives[{index}].drawbacks")
        text(item["rejection_reason"], f"alternatives[{index}].rejection_reason", nullable=True)
        alternative_ids.append(item["id"])
    fail(len(alternative_ids) == len(set(alternative_ids)), "alternative ids must be unique")
    fail(record["selected_alternative"] in alternative_ids, "selected_alternative must reference an alternative id")

    tradeoffs = exact_keys(record["tradeoffs"], {"security", "cost", "compliance", "operations"}, "tradeoffs")
    for key in tradeoffs:
        validate_tradeoff(tradeoffs[key], f"tradeoffs.{key}")

    authority = exact_keys(record["authority"], {"authority_status", "decision_owner", "deciders", "approvers", "delegation_ref"}, "authority")
    fail(authority["authority_status"] in AUTHORITY_STATUSES, "authority_status is invalid")
    text(authority["decision_owner"], "authority.decision_owner", nullable=True)
    text_list(authority["deciders"], "authority.deciders", unique=True)
    text_list(authority["approvers"], "authority.approvers", unique=True)
    text(authority["delegation_ref"], "authority.delegation_ref", nullable=True)

    provenance = exact_keys(record["provenance"], {"sources", "activities", "agents"}, "provenance")
    fail(isinstance(provenance["sources"], list) and provenance["sources"], "provenance.sources must not be empty")
    source_ids: list[str] = []
    for index, value in enumerate(provenance["sources"]):
        item = exact_keys(value, {"id", "uri", "title", "authority_status", "digest"}, f"provenance.sources[{index}]")
        text(item["id"], f"provenance.sources[{index}].id")
        text(item["uri"], f"provenance.sources[{index}].uri")
        text(item["title"], f"provenance.sources[{index}].title", nullable=True)
        fail(item["authority_status"] in AUTHORITY_STATUSES, f"provenance.sources[{index}].authority_status is invalid")
        text(item["digest"], f"provenance.sources[{index}].digest", nullable=True)
        source_ids.append(item["id"])
    fail(len(source_ids) == len(set(source_ids)), "source ids must be unique")

    fail(isinstance(provenance["agents"], list), "provenance.agents must be an array")
    agent_ids: list[str] = []
    for index, value in enumerate(provenance["agents"]):
        item = exact_keys(value, {"id", "type", "name", "role", "acted_on_behalf_of"}, f"provenance.agents[{index}]")
        text(item["id"], f"provenance.agents[{index}].id")
        fail(item["type"] in {"person", "organisation", "software-agent", "model"}, f"provenance.agents[{index}].type is invalid")
        text(item["name"], f"provenance.agents[{index}].name")
        text(item["role"], f"provenance.agents[{index}].role")
        text(item["acted_on_behalf_of"], f"provenance.agents[{index}].acted_on_behalf_of", nullable=True)
        agent_ids.append(item["id"])
    fail(len(agent_ids) == len(set(agent_ids)), "agent ids must be unique")

    fail(isinstance(provenance["activities"], list), "provenance.activities must be an array")
    for index, value in enumerate(provenance["activities"]):
        item = exact_keys(value, {"id", "type", "timestamp", "used", "associated_agents"}, f"provenance.activities[{index}]")
        text(item["id"], f"provenance.activities[{index}].id")
        fail(item["type"] in {"discovery", "extraction", "generation", "review", "approval", "invalidation"}, f"provenance.activities[{index}].type is invalid")
        timestamp(item["timestamp"], f"provenance.activities[{index}].timestamp")
        text_list(item["used"], f"provenance.activities[{index}].used", unique=True)
        text_list(item["associated_agents"], f"provenance.activities[{index}].associated_agents", unique=True)
        fail(set(item["used"]).issubset(source_ids), f"provenance.activities[{index}].used references unknown sources")
        fail(set(item["associated_agents"]).issubset(agent_ids), f"provenance.activities[{index}].associated_agents references unknown agents")

    lifecycle = exact_keys(record["lifecycle"], {"created_at", "effective_at", "review_by", "expires_at", "review_triggers"}, "lifecycle")
    timestamp(lifecycle["created_at"], "lifecycle.created_at")
    for key in ("effective_at", "review_by", "expires_at"):
        timestamp(lifecycle[key], f"lifecycle.{key}", nullable=True)
    text_list(lifecycle["review_triggers"], "lifecycle.review_triggers", unique=True)

    consequences = exact_keys(record["consequences"], {"positive", "negative", "risks", "actions"}, "consequences")
    for key in consequences:
        text_list(consequences[key], f"consequences.{key}")

    implementation = exact_keys(record["implementation"], {"policy_refs", "artifact_refs", "evidence_refs"}, "implementation")
    for key in implementation:
        text_list(implementation[key], f"implementation.{key}", unique=True)

    relationships = exact_keys(record["relationships"], {"revises", "supersedes", "invalidates", "implements", "depends_on"}, "relationships")
    for key in ("revises", "supersedes", "invalidates"):
        text(relationships[key], f"relationships.{key}", nullable=True)
    for key in ("implements", "depends_on"):
        text_list(relationships[key], f"relationships.{key}", unique=True)

    autonomy = exact_keys(record["autonomy"], {"proceed", "always_ask", "never"}, "autonomy")
    for key in autonomy:
        text_list(autonomy[key], f"autonomy.{key}")

    ratification = record["ratification"]
    if record["status"] in {"ratified", "effective"} or require_ratified:
        item = exact_keys(
            ratification,
            {
                "status",
                "timestamp",
                "confirmed_by",
                "authority_role",
                "approval_meaning",
                "record_fingerprint",
                "context_fingerprint",
                "accepted_warnings",
                "signature_ref",
            },
            "ratification",
        )
        fail(item["status"] == "ratified", "ratification.status must be ratified")
        timestamp(item["timestamp"], "ratification.timestamp")
        text(item["confirmed_by"], "ratification.confirmed_by")
        text(item["authority_role"], "ratification.authority_role", nullable=True)
        text(item["approval_meaning"], "ratification.approval_meaning")
        fail(isinstance(item["record_fingerprint"], str) and FINGERPRINT.fullmatch(item["record_fingerprint"]) is not None, "ratification.record_fingerprint is invalid")
        fail(isinstance(item["context_fingerprint"], str) and FINGERPRINT.fullmatch(item["context_fingerprint"]) is not None, "ratification.context_fingerprint is invalid")
        text_list(item["accepted_warnings"], "ratification.accepted_warnings")
        text(item["signature_ref"], "ratification.signature_ref", nullable=True)
        fail(item["record_fingerprint"] == fingerprint(record), "ratification fingerprint does not match record")
    else:
        fail(ratification is None, "unratified records must have ratification=null")


def assess_record(record: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    validate_record(record)
    reasons: list[str] = []
    status = record["status"]
    lifecycle = record["lifecycle"]

    if status not in {"ratified", "effective"}:
        reasons.append(f"status {status} is not eligible for active context")
        eligibility = "inactive"
    elif lifecycle["effective_at"] and parse_moment(
        lifecycle["effective_at"], "lifecycle.effective_at"
    ) > as_of:
        reasons.append("effective_at is in the future")
        eligibility = "not_yet_effective"
    elif lifecycle["expires_at"] and parse_moment(
        lifecycle["expires_at"], "lifecycle.expires_at"
    ) <= as_of:
        reasons.append("expires_at has passed")
        eligibility = "expired"
    elif lifecycle["review_by"] and parse_moment(
        lifecycle["review_by"], "lifecycle.review_by"
    ) <= as_of:
        reasons.append("review_by has passed")
        eligibility = "review_required"
    elif record["authority"]["authority_status"] not in {
        "authoritative",
        "user-confirmed",
    }:
        reasons.append("record authority requires local review")
        eligibility = "authority_review_required"
    else:
        eligibility = "eligible"

    return {
        "as_of": as_of.isoformat().replace("+00:00", "Z"),
        "eligibility": eligibility,
        "reasons": reasons,
    }


def validate_source_metadata(metadata: dict[str, Any]) -> None:
    exact_keys(metadata, SOURCE_KEYS, "source metadata")
    fail(
        metadata["schema_version"] == SOURCE_SCHEMA_VERSION,
        f"schema_version must be {SOURCE_SCHEMA_VERSION}",
    )
    fail(
        isinstance(metadata["decision_id"], str)
        and DECISION_ID.fullmatch(metadata["decision_id"]) is not None,
        "decision_id is invalid",
    )
    try:
        uuid.UUID(metadata["record_id"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise DecisionRecordError("record_id must be a UUID") from exc
    fail(
        isinstance(metadata["record_version"], int)
        and metadata["record_version"] >= 1,
        "record_version must be a positive integer",
    )
    text(metadata["source_uri"], "source_uri")
    text(metadata["snapshot_path"], "snapshot_path")
    timestamp(metadata["retrieved_at"], "retrieved_at")
    timestamp(metadata["last_checked_at"], "last_checked_at")
    for key in ("record_fingerprint", "source_digest"):
        fail(
            isinstance(metadata[key], str)
            and FINGERPRINT.fullmatch(metadata[key]) is not None,
            f"{key} is invalid",
        )
    text(metadata["source_etag"], "source_etag", nullable=True)
    assessment = exact_keys(
        metadata["assessment"], {"as_of", "eligibility", "reasons"}, "assessment"
    )
    timestamp(assessment["as_of"], "assessment.as_of")
    fail(
        assessment["eligibility"]
        in {
            "eligible",
            "inactive",
            "not_yet_effective",
            "expired",
            "review_required",
            "authority_review_required",
        },
        "assessment.eligibility is invalid",
    )
    text_list(assessment["reasons"], "assessment.reasons")
    fail(
        metadata["local_disposition"] in {"accepted", "needs_review", "inactive"},
        "local_disposition is invalid",
    )
    text(metadata["acceptance_basis"], "acceptance_basis", nullable=True)
    text(metadata["accepted_by"], "accepted_by", nullable=True)
    fail(isinstance(metadata["scope_confirmed"], bool), "scope_confirmed must be boolean")
    fail(
        isinstance(metadata["authority_accepted"], bool),
        "authority_accepted must be boolean",
    )
    if metadata["local_disposition"] == "accepted":
        fail(assessment["eligibility"] == "eligible", "only eligible records may be accepted")
        fail(metadata["scope_confirmed"], "accepted records require confirmed scope")
        fail(metadata["authority_accepted"], "accepted records require accepted authority")
        text(metadata["acceptance_basis"], "acceptance_basis")
        text(metadata["accepted_by"], "accepted_by")
    else:
        fail(
            metadata["acceptance_basis"] is None and metadata["accepted_by"] is None,
            "unaccepted records must not claim acceptance",
        )


def validate_quality_assessment(assessment: dict[str, Any]) -> None:
    exact_keys(
        assessment,
        {
            "schema_version",
            "assessment_id",
            "target",
            "stage",
            "assessed_at",
            "assessor",
            "dimensions",
            "overall",
            "standing_effect",
            "notes",
        },
        "quality assessment",
    )
    fail(
        assessment["schema_version"] == QUALITY_SCHEMA_VERSION,
        f"schema_version must be {QUALITY_SCHEMA_VERSION}",
    )
    try:
        uuid.UUID(assessment["assessment_id"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise DecisionRecordError("assessment_id must be a UUID") from exc
    fail(
        assessment["stage"]
        in {
            "source-intake",
            "intent-fitness",
            "record-fitness",
            "projection-fitness",
        },
        "quality assessment stage is invalid",
    )
    timestamp(assessment["assessed_at"], "assessed_at")

    target = exact_keys(
        assessment["target"],
        {"type", "uri", "record_id", "fingerprint"},
        "quality assessment target",
    )
    fail(
        target["type"] in {"source", "intent", "record", "projection"},
        "quality assessment target.type is invalid",
    )
    text(target["uri"], "quality assessment target.uri")
    if target["record_id"] is not None:
        try:
            uuid.UUID(target["record_id"])
        except (ValueError, TypeError, AttributeError) as exc:
            raise DecisionRecordError(
                "quality assessment target.record_id must be a UUID or null"
            ) from exc
    if target["fingerprint"] is not None:
        fail(
            isinstance(target["fingerprint"], str)
            and FINGERPRINT.fullmatch(target["fingerprint"]) is not None,
            "quality assessment target.fingerprint is invalid",
        )
    if target["type"] in {"record", "projection"}:
        fail(
            target["fingerprint"] is not None,
            "record and projection quality assessments require a fingerprint",
        )

    assessor = exact_keys(
        assessment["assessor"],
        {"id", "type", "name"},
        "quality assessment assessor",
    )
    text(assessor["id"], "quality assessment assessor.id")
    fail(
        assessor["type"] in {"person", "organisation", "software-agent", "model"},
        "quality assessment assessor.type is invalid",
    )
    text(assessor["name"], "quality assessment assessor.name")

    dimensions = exact_keys(
        assessment["dimensions"],
        QUALITY_DIMENSIONS,
        "quality assessment dimensions",
    )
    statuses: list[str] = []
    for dimension_name in sorted(QUALITY_DIMENSIONS):
        dimension = exact_keys(
            dimensions[dimension_name],
            {"status", "summary", "evidence_refs", "findings"},
            f"quality assessment dimensions.{dimension_name}",
        )
        fail(
            dimension["status"] in {"pass", "warn", "block", "not_assessed"},
            f"quality assessment dimensions.{dimension_name}.status is invalid",
        )
        statuses.append(dimension["status"])
        text(
            dimension["summary"],
            f"quality assessment dimensions.{dimension_name}.summary",
        )
        text_list(
            dimension["evidence_refs"],
            f"quality assessment dimensions.{dimension_name}.evidence_refs",
            unique=True,
        )
        fail(
            isinstance(dimension["findings"], list),
            f"quality assessment dimensions.{dimension_name}.findings must be an array",
        )
        for index, finding_value in enumerate(dimension["findings"]):
            finding = exact_keys(
                finding_value,
                {"severity", "statement", "remediation"},
                f"quality assessment dimensions.{dimension_name}.findings[{index}]",
            )
            fail(
                finding["severity"] in {"info", "warning", "blocker"},
                f"quality assessment dimensions.{dimension_name}.findings[{index}].severity is invalid",
            )
            text(
                finding["statement"],
                f"quality assessment dimensions.{dimension_name}.findings[{index}].statement",
            )
            text(
                finding["remediation"],
                f"quality assessment dimensions.{dimension_name}.findings[{index}].remediation",
                nullable=True,
            )

    expected_overall = (
        "block"
        if "block" in statuses
        else "incomplete"
        if "not_assessed" in statuses
        else "pass_with_warnings"
        if "warn" in statuses
        else "pass"
    )
    fail(
        assessment["overall"] == expected_overall,
        f"quality assessment overall must be {expected_overall}",
    )
    fail(
        assessment["standing_effect"] == "none",
        "quality assessment standing_effect must be none",
    )
    text_list(assessment["notes"], "quality assessment notes")


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def action_matches(action: str, boundary: str) -> bool:
    normalized_action = normalize_text(action)
    normalized_boundary = normalize_text(boundary)
    return (
        normalized_action == normalized_boundary
        or normalized_action in normalized_boundary
        or normalized_boundary in normalized_action
    )


def discover_json_files(targets: list[str]) -> list[Path]:
    files: set[Path] = set()
    for target_value in targets:
        target = Path(target_value)
        fail(target.exists(), f"target does not exist: {target}")
        if target.is_file():
            files.add(target.resolve())
            continue
        for path in target.rglob("*.json"):
            if path.is_file():
                files.add(path.resolve())
    return sorted(files)


def adjacent_source_path(record_path: Path) -> Path:
    return record_path.with_name(f"{record_path.stem}.source.json")


def inspect_record(
    path: Path,
    *,
    as_of: datetime,
    include_content: bool = False,
) -> dict[str, Any]:
    record, raw = read_record_bytes(path)
    validate_record(record)
    assessment = assess_record(record, as_of)
    source_path = adjacent_source_path(path)
    source_metadata: dict[str, Any] | None = None
    local_disposition = "local"
    local_active = assessment["eligibility"] == "eligible"

    if source_path.exists():
        source_metadata = read_record(source_path)
        validate_source_metadata(source_metadata)
        fail(
            source_metadata["record_id"] == record["record_id"],
            f"source sidecar record_id does not match {path}",
        )
        fail(
            source_metadata["record_fingerprint"] == fingerprint(record),
            f"source sidecar fingerprint does not match {path}",
        )
        fail(
            source_metadata["source_digest"]
            == f"sha256:{hashlib.sha256(raw).hexdigest()}",
            f"source sidecar byte digest does not match {path}",
        )
        local_disposition = source_metadata["local_disposition"]
        local_active = (
            local_active
            and source_metadata["assessment"]["eligibility"] == "eligible"
            and source_metadata["local_disposition"] == "accepted"
            and source_metadata["scope_confirmed"]
            and source_metadata["authority_accepted"]
        )

    result: dict[str, Any] = {
        "path": str(path),
        "decision_id": record["decision_id"],
        "record_id": record["record_id"],
        "record_version": record["record_version"],
        "title": record["title"],
        "status": record["status"],
        "record_fingerprint": fingerprint(record),
        "authority_status": record["authority"]["authority_status"],
        "scope": record["context"]["scope"],
        "assessment": assessment,
        "local_disposition": local_disposition,
        "active": local_active,
        "review_by": record["lifecycle"]["review_by"],
        "expires_at": record["lifecycle"]["expires_at"],
        "relationships": record["relationships"],
        "autonomy": record["autonomy"],
        "gaps": record["gaps"],
        "source_metadata_path": str(source_path) if source_metadata else None,
    }
    if source_metadata:
        result["source_uri"] = source_metadata["source_uri"]
        result["source_assessment"] = source_metadata["assessment"]
        result["acceptance_basis"] = source_metadata["acceptance_basis"]
    if include_content:
        result["record"] = record
        result["source_metadata"] = source_metadata
    return result


def scope_matches(record_scope: list[str], requested_scopes: list[str]) -> bool:
    if not requested_scopes:
        return True
    normalized_record_scope = {normalize_text(value) for value in record_scope}
    normalized_requested = {normalize_text(value) for value in requested_scopes}
    return bool(normalized_record_scope & normalized_requested) or "*" in normalized_record_scope


def resolve_records(
    targets: list[str],
    *,
    as_of: datetime,
    scopes: list[str],
) -> dict[str, Any]:
    files = discover_json_files(targets)
    entries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in files:
        try:
            candidate = read_record(path)
        except DecisionRecordError as exc:
            errors.append({"path": str(path), "error": str(exc)})
            continue
        schema_version = candidate.get("schema_version")
        if schema_version == SOURCE_SCHEMA_VERSION:
            continue
        if schema_version != SCHEMA_VERSION:
            continue
        try:
            entries.append(inspect_record(path, as_of=as_of))
        except DecisionRecordError as exc:
            errors.append({"path": str(path), "error": str(exc)})

    excluded: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for entry in entries:
        reasons: list[str] = []
        if not entry["active"]:
            reasons.append(
                f"not active: {entry['assessment']['eligibility']}"
                if entry["local_disposition"] == "local"
                else f"not locally active: {entry['local_disposition']}"
            )
        if not scope_matches(entry["scope"], scopes):
            reasons.append("scope does not match")
        if reasons:
            excluded.append(
                {
                    "decision_id": entry["decision_id"],
                    "record_id": entry["record_id"],
                    "path": entry["path"],
                    "reasons": reasons,
                }
            )
        else:
            candidates.append(entry)

    by_decision: dict[str, list[dict[str, Any]]] = {}
    for entry in candidates:
        by_decision.setdefault(entry["decision_id"], []).append(entry)

    selected: dict[str, dict[str, Any]] = {}
    warnings: list[dict[str, Any]] = []
    for decision_id, versions in sorted(by_decision.items()):
        ordered = sorted(
            versions,
            key=lambda item: (item["record_version"], item["record_id"]),
            reverse=True,
        )
        selected[decision_id] = ordered[0]
        if len(ordered) > 1:
            warnings.append(
                {
                    "type": "multiple_active_versions",
                    "decision_id": decision_id,
                    "selected_record_id": ordered[0]["record_id"],
                    "other_record_ids": [item["record_id"] for item in ordered[1:]],
                }
            )

    removed: dict[str, list[str]] = {}
    for entry in list(selected.values()):
        supersedes = entry["relationships"]["supersedes"]
        invalidates = entry["relationships"]["invalidates"]
        if supersedes and supersedes in selected and supersedes != entry["decision_id"]:
            removed.setdefault(supersedes, []).append(
                f"superseded by {entry['decision_id']}"
            )
        if invalidates and invalidates in selected and invalidates != entry["decision_id"]:
            removed.setdefault(invalidates, []).append(
                f"invalidated by {entry['decision_id']}"
            )

    for decision_id, reasons in removed.items():
        removed_entry = selected.pop(decision_id)
        excluded.append(
            {
                "decision_id": decision_id,
                "record_id": removed_entry["record_id"],
                "path": removed_entry["path"],
                "reasons": reasons,
            }
        )

    active_ids = set(selected)
    dependency_failures: dict[str, list[str]] = {}
    for decision_id, entry in selected.items():
        missing = [
            dependency
            for dependency in entry["relationships"]["depends_on"]
            if dependency not in active_ids
        ]
        if missing:
            dependency_failures[decision_id] = missing

    for decision_id, missing in dependency_failures.items():
        entry = selected.pop(decision_id)
        excluded.append(
            {
                "decision_id": decision_id,
                "record_id": entry["record_id"],
                "path": entry["path"],
                "reasons": [f"missing active dependency: {value}" for value in missing],
            }
        )

    authority_conflicts = [
        entry["decision_id"]
        for entry in selected.values()
        if entry["authority_status"] == "conflicting"
    ]
    if authority_conflicts:
        warnings.append(
            {
                "type": "authority_conflict",
                "decision_ids": sorted(authority_conflicts),
            }
        )

    active = [selected[key] for key in sorted(selected)]
    return {
        "schema_version": "adrp-resolution/v1",
        "as_of": as_of.isoformat().replace("+00:00", "Z"),
        "requested_scopes": scopes,
        "active": active,
        "excluded": sorted(
            excluded,
            key=lambda item: (item["decision_id"], item["record_id"]),
        ),
        "warnings": warnings,
        "errors": errors,
        "summary": {
            "files_scanned": len(files),
            "records_found": len(entries),
            "active_records": len(active),
            "excluded_records": len(excluded),
            "errors": len(errors),
        },
    }


def render_list(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- None recorded"


def render_markdown(record: dict[str, Any]) -> str:
    validate_record(record)
    lines = [
        f"# {record['decision_id']}: {record['title']}",
        "",
        f"- **Status:** `{record['status']}`",
        f"- **Record version:** `{record['record_version']}`",
        f"- **Record ID:** `{record['record_id']}`",
        f"- **Authority:** `{record['authority']['authority_status']}`",
        "",
        "## Decision",
        "",
        record["decision_statement"],
        "",
        "## Context",
        "",
        record["context"]["problem"],
        "",
        "### Scope",
        render_list(record["context"]["scope"]),
        "",
        "### Drivers",
    ]
    for driver in record["drivers"]:
        lines.append(f"- **{driver['name']}** ({driver['category']}): {driver['criterion']}")
    lines.extend(["", "## Alternatives"])
    for alternative in record["alternatives"]:
        marker = " — **selected**" if alternative["id"] == record["selected_alternative"] else ""
        lines.extend(
            [
                "",
                f"### {alternative['id']}: {alternative['title']}{marker}",
                "",
                alternative["description"] or "No description recorded.",
                "",
                "**Benefits**",
                render_list(alternative["benefits"]),
                "",
                "**Drawbacks**",
                render_list(alternative["drawbacks"]),
            ]
        )
        if alternative["rejection_reason"]:
            lines.extend(["", f"**Rejection reason:** {alternative['rejection_reason']}"])
    lines.extend(["", "## Rationale", "", record["rationale"], "", "## Trade-offs"])
    for category in ("security", "cost", "compliance", "operations"):
        item = record["tradeoffs"][category]
        lines.extend(
            [
                "",
                f"### {category.title()} — `{item['impact']}`",
                "",
                item["summary"] or "No material impact recorded.",
                "",
                "**Accepted risks**",
                render_list(item["accepted_risks"]),
            ]
        )
    lines.extend(
        [
            "",
            "## Consequences",
            "",
            "### Positive",
            render_list(record["consequences"]["positive"]),
            "",
            "### Negative",
            render_list(record["consequences"]["negative"]),
            "",
            "### Risks",
            render_list(record["consequences"]["risks"]),
            "",
            "## Autonomy",
            "",
            "### PROCEED",
            render_list(record["autonomy"]["proceed"]),
            "",
            "### ALWAYS ASK",
            render_list(record["autonomy"]["always_ask"]),
            "",
            "### NEVER",
            render_list(record["autonomy"]["never"]),
            "",
            "## Provenance",
        ]
    )
    for source in record["provenance"]["sources"]:
        lines.append(f"- `{source['id']}` — {source['uri']} ({source['authority_status']})")
    lines.extend(["", "## Gaps", render_list(record["gaps"])])
    if record["ratification"]:
        ratification = record["ratification"]
        lines.extend(
            [
                "",
                "## Ratification",
                "",
                f"- **Confirmed by:** {ratification['confirmed_by']}",
                f"- **Authority role:** {ratification['authority_role'] or 'Not supplied'}",
                f"- **Timestamp:** {ratification['timestamp']}",
                f"- **Meaning:** {ratification['approval_meaning']}",
                f"- **Decision fingerprint:** `{ratification['record_fingerprint']}`",
                f"- **Context fingerprint:** `{ratification['context_fingerprint']}`",
                "",
                "### Accepted warnings",
                render_list(ratification["accepted_warnings"]),
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def validate_command(args: argparse.Namespace) -> int:
    record = read_record(Path(args.target))
    validate_record(record, require_ratified=args.require_ratified)
    print(json.dumps({"target": args.target, "status": record["status"], "valid": True}))
    return 0


def validate_source_command(args: argparse.Namespace) -> int:
    metadata = read_record(Path(args.target))
    validate_source_metadata(metadata)
    print(
        json.dumps(
            {
                "target": args.target,
                "local_disposition": metadata["local_disposition"],
                "valid": True,
            }
        )
    )
    return 0


def validate_quality_command(args: argparse.Namespace) -> int:
    assessment = read_record(Path(args.target))
    validate_quality_assessment(assessment)
    print(
        json.dumps(
            {
                "target": args.target,
                "stage": assessment["stage"],
                "overall": assessment["overall"],
                "standing_effect": assessment["standing_effect"],
                "valid": True,
            }
        )
    )
    return 0


def assessment_time(value: str | None) -> datetime:
    if value:
        return parse_moment(value, "as_of")
    return datetime.now(timezone.utc)


def assess_command(args: argparse.Namespace) -> int:
    record = read_record(Path(args.target))
    assessment = assess_record(record, assessment_time(args.as_of))
    print(
        json.dumps(
            {
                "decision_id": record["decision_id"],
                "record_id": record["record_id"],
                "record_version": record["record_version"],
                "status": record["status"],
                "record_fingerprint": fingerprint(record),
                "assessment": assessment,
            }
        )
    )
    return 0


def import_command(args: argparse.Namespace) -> int:
    source = Path(args.target)
    snapshot = Path(args.snapshot)
    metadata_path = Path(args.metadata_output)
    record, raw = read_record_bytes(source)
    assessment = assess_record(record, assessment_time(args.as_of))
    retrieved_at = args.retrieved_at or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    timestamp(retrieved_at, "retrieved_at")

    accepted = (
        assessment["eligibility"] == "eligible"
        and args.confirm_scope
        and args.accept_authority
    )
    if accepted:
        fail(bool(args.acceptance_basis), "accepted imports require --acceptance-basis")
        fail(bool(args.accepted_by), "accepted imports require --accepted-by")
        disposition = "accepted"
    elif assessment["eligibility"] == "eligible":
        disposition = "needs_review"
    else:
        disposition = "inactive"

    metadata = {
        "schema_version": SOURCE_SCHEMA_VERSION,
        "decision_id": record["decision_id"],
        "record_id": record["record_id"],
        "record_version": record["record_version"],
        "source_uri": args.source_uri,
        "snapshot_path": str(snapshot),
        "retrieved_at": retrieved_at,
        "last_checked_at": retrieved_at,
        "record_fingerprint": fingerprint(record),
        "source_digest": f"sha256:{hashlib.sha256(raw).hexdigest()}",
        "source_etag": args.source_etag,
        "assessment": assessment,
        "local_disposition": disposition,
        "acceptance_basis": args.acceptance_basis if accepted else None,
        "accepted_by": args.accepted_by if accepted else None,
        "scope_confirmed": bool(args.confirm_scope),
        "authority_accepted": bool(args.accept_authority),
    }
    validate_source_metadata(metadata)

    atomic_create_bytes(snapshot, raw)
    try:
        atomic_create(
            metadata_path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
        )
    except Exception:
        snapshot.unlink(missing_ok=True)
        raise
    print(
        json.dumps(
            {
                "snapshot": str(snapshot),
                "metadata": str(metadata_path),
                "record_fingerprint": metadata["record_fingerprint"],
                "source_digest": metadata["source_digest"],
                "local_disposition": disposition,
                "assessment": assessment,
            }
        )
    )
    return 0


def check_source_command(args: argparse.Namespace) -> int:
    metadata_path = Path(args.metadata)
    metadata = read_record(metadata_path)
    validate_source_metadata(metadata)
    record, raw = read_record_bytes(Path(args.target))
    validate_record(record)
    current_fingerprint = fingerprint(record)
    current_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"

    if (
        record["decision_id"] != metadata["decision_id"]
        or record["record_id"] != metadata["record_id"]
        or record["record_version"] != metadata["record_version"]
    ):
        comparison = "identity_changed"
    elif current_fingerprint != metadata["record_fingerprint"]:
        comparison = "record_changed"
    elif current_digest != metadata["source_digest"]:
        comparison = "source_bytes_changed"
    else:
        comparison = "unchanged"

    checked_at = args.checked_at or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    timestamp(checked_at, "checked_at")
    if args.update_metadata:
        fail(
            comparison == "unchanged",
            "changed sources require a new immutable import; metadata was not updated",
        )
        metadata["last_checked_at"] = checked_at
        if args.source_etag is not None:
            metadata["source_etag"] = args.source_etag
        validate_source_metadata(metadata)
        atomic_write(
            metadata_path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
        )

    print(
        json.dumps(
            {
                "comparison": comparison,
                "checked_at": checked_at,
                "source_uri": metadata["source_uri"],
                "expected_record_fingerprint": metadata["record_fingerprint"],
                "current_record_fingerprint": current_fingerprint,
                "expected_source_digest": metadata["source_digest"],
                "current_source_digest": current_digest,
                "metadata_updated": bool(args.update_metadata),
            }
        )
    )
    return 0


def fingerprint_command(args: argparse.Namespace) -> int:
    record = read_record(Path(args.target))
    validate_record(record)
    print(fingerprint(record))
    return 0


def render_command(args: argparse.Namespace) -> int:
    record = read_record(Path(args.target))
    rendered = render_markdown(record)
    if args.dry_run:
        sys.stdout.write(rendered)
    else:
        fail(bool(args.output), "--output is required unless --dry-run is used")
        output = Path(args.output)
        if args.allow_overwrite:
            atomic_write(output, rendered)
        else:
            atomic_create(output, rendered)
        print(json.dumps({"output": str(output)}))
    return 0


def ratify_command(args: argparse.Namespace) -> int:
    source = Path(args.target)
    output = Path(args.output)
    record = read_record(source)
    validate_record(record)
    fail(record["status"] in {"draft", "under-review"}, "only draft or under-review records may be ratified")
    fail(record["ratification"] is None, "record is already ratified")
    record["status"] = "ratified"
    record["ratification"] = None
    digest = fingerprint(record)
    record["ratification"] = {
        "status": "ratified",
        "timestamp": args.timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "confirmed_by": args.confirmed_by,
        "authority_role": args.authority_role,
        "approval_meaning": args.approval_meaning,
        "record_fingerprint": digest,
        "context_fingerprint": args.context_fingerprint,
        "accepted_warnings": args.accepted_warning,
        "signature_ref": args.signature_ref,
    }
    validate_record(record, require_ratified=True)
    atomic_create(output, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output), "fingerprint": digest}))
    return 0


def inspect_command(args: argparse.Namespace) -> int:
    result = inspect_record(
        Path(args.target),
        as_of=assessment_time(args.as_of),
        include_content=args.include_content,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def resolve_command(args: argparse.Namespace) -> int:
    result = resolve_records(
        args.target,
        as_of=assessment_time(args.as_of),
        scopes=args.scope,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


def autonomy_command(args: argparse.Namespace) -> int:
    resolution = resolve_records(
        args.target,
        as_of=assessment_time(args.as_of),
        scopes=args.scope,
    )
    matches: dict[str, list[dict[str, str]]] = {
        "never": [],
        "always_ask": [],
        "proceed": [],
    }
    for entry in resolution["active"]:
        for boundary in matches:
            for statement in entry["autonomy"][boundary]:
                if action_matches(args.action, statement):
                    matches[boundary].append(
                        {
                            "decision_id": entry["decision_id"],
                            "record_id": entry["record_id"],
                            "statement": statement,
                        }
                    )

    if matches["never"]:
        outcome = "NEVER"
    elif matches["always_ask"]:
        outcome = "ALWAYS_ASK"
    elif matches["proceed"]:
        outcome = "PROCEED"
    else:
        outcome = "UNRESOLVED"

    result = {
        "schema_version": "adrp-autonomy/v1",
        "action": args.action,
        "outcome": outcome,
        "matches": matches,
        "resolution_summary": resolution["summary"],
        "resolution_warnings": resolution["warnings"],
        "resolution_errors": resolution["errors"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if resolution["errors"] else 0


def graph_command(args: argparse.Namespace) -> int:
    files = discover_json_files(args.target)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    as_of = assessment_time(args.as_of)

    for path in files:
        try:
            value = read_record(path)
            if value.get("schema_version") != SCHEMA_VERSION:
                continue
            entry = inspect_record(path, as_of=as_of)
        except DecisionRecordError as exc:
            errors.append({"path": str(path), "error": str(exc)})
            continue
        nodes.append(
            {
                "decision_id": entry["decision_id"],
                "record_id": entry["record_id"],
                "record_version": entry["record_version"],
                "title": entry["title"],
                "status": entry["status"],
                "active": entry["active"],
                "path": entry["path"],
            }
        )
        relationships = entry["relationships"]
        for relationship in ("revises", "supersedes", "invalidates"):
            target = relationships[relationship]
            if target:
                edges.append(
                    {
                        "from": entry["decision_id"],
                        "to": target,
                        "type": relationship,
                    }
                )
        for relationship in ("implements", "depends_on"):
            for target in relationships[relationship]:
                edges.append(
                    {
                        "from": entry["decision_id"],
                        "to": target,
                        "type": relationship,
                    }
                )

    result = {
        "schema_version": "adrp-graph/v1",
        "nodes": sorted(
            nodes,
            key=lambda item: (
                item["decision_id"],
                item["record_version"],
                item["record_id"],
            ),
        ),
        "edges": sorted(
            edges,
            key=lambda item: (item["from"], item["type"], item["to"]),
        ),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def verify_set_command(args: argparse.Namespace) -> int:
    files = discover_json_files(args.target)
    records: list[dict[str, Any]] = []
    sidecars: list[dict[str, Any]] = []
    skipped: list[str] = []
    errors: list[dict[str, str]] = []
    records_by_id: dict[str, list[dict[str, Any]]] = {}

    for path in files:
        try:
            value, raw = read_record_bytes(path)
            schema_version = value.get("schema_version")
            if schema_version == SCHEMA_VERSION:
                validate_record(
                    value,
                    require_ratified=args.require_ratified,
                )
                item = {
                    "path": str(path),
                    "decision_id": value["decision_id"],
                    "record_id": value["record_id"],
                    "record_version": value["record_version"],
                    "status": value["status"],
                    "record_fingerprint": fingerprint(value),
                    "source_digest": f"sha256:{hashlib.sha256(raw).hexdigest()}",
                }
                records.append(item)
                records_by_id.setdefault(value["record_id"], []).append(item)
            elif schema_version == SOURCE_SCHEMA_VERSION:
                validate_source_metadata(value)
                sidecars.append(
                    {
                        "path": str(path),
                        "decision_id": value["decision_id"],
                        "record_id": value["record_id"],
                        "local_disposition": value["local_disposition"],
                    }
                )
            else:
                skipped.append(str(path))
        except DecisionRecordError as exc:
            errors.append({"path": str(path), "error": str(exc)})

    for record_id, matching_records in records_by_id.items():
        immutable_records = [
            item
            for item in matching_records
            if item["status"] in {"ratified", "effective"}
        ]
        if len(immutable_records) > 1:
            errors.append(
                {
                    "path": ", ".join(item["path"] for item in immutable_records),
                    "error": f"duplicate immutable record_id in verified set: {record_id}",
                }
            )

    for sidecar in sidecars:
        matching_records = records_by_id.get(sidecar["record_id"], [])
        if not matching_records:
            errors.append(
                {
                    "path": sidecar["path"],
                    "error": "source sidecar has no matching record in the verified set",
                }
            )
            continue
        metadata = read_record(Path(sidecar["path"]))
        fingerprint_matches = [
            item
            for item in matching_records
            if item["record_fingerprint"] == metadata["record_fingerprint"]
        ]
        if not fingerprint_matches:
            errors.append(
                {
                    "path": sidecar["path"],
                    "error": "source sidecar fingerprint does not match its record",
                }
            )
            continue
        if not any(
            item["source_digest"] == metadata["source_digest"]
            for item in fingerprint_matches
        ):
            errors.append(
                {
                    "path": sidecar["path"],
                    "error": "source sidecar byte digest does not match its record",
                }
            )

    result = {
        "schema_version": "adrp-verification/v1",
        "valid": not errors,
        "records": records,
        "sidecars": sidecars,
        "skipped": skipped,
        "errors": errors,
        "summary": {
            "files_scanned": len(files),
            "records": len(records),
            "sidecars": len(sidecars),
            "skipped": len(skipped),
            "errors": len(errors),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--version", action="version", version=f"adrp {VERSION}")
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate a canonical decision record")
    validate.add_argument("--target", required=True)
    validate.add_argument("--require-ratified", action="store_true")
    validate.set_defaults(handler=validate_command)

    validate_source = commands.add_parser(
        "validate-source", help="validate imported decision source metadata"
    )
    validate_source.add_argument("--target", required=True)
    validate_source.set_defaults(handler=validate_source_command)

    validate_quality = commands.add_parser(
        "validate-quality",
        help="validate a CAFE(S) source or intent quality assessment",
    )
    validate_quality.add_argument("--target", required=True)
    validate_quality.set_defaults(handler=validate_quality_command)

    assess = commands.add_parser(
        "assess", help="assess lifecycle and authority eligibility"
    )
    assess.add_argument("--target", required=True)
    assess.add_argument("--as-of")
    assess.set_defaults(handler=assess_command)

    import_record = commands.add_parser(
        "import", help="create a verbatim immutable snapshot and source sidecar"
    )
    import_record.add_argument("--target", required=True)
    import_record.add_argument("--snapshot", required=True)
    import_record.add_argument("--metadata-output", required=True)
    import_record.add_argument("--source-uri", required=True)
    import_record.add_argument("--source-etag")
    import_record.add_argument("--retrieved-at")
    import_record.add_argument("--as-of")
    import_record.add_argument("--confirm-scope", action="store_true")
    import_record.add_argument("--accept-authority", action="store_true")
    import_record.add_argument("--acceptance-basis")
    import_record.add_argument("--accepted-by")
    import_record.set_defaults(handler=import_command)

    check_source = commands.add_parser(
        "check-source", help="compare a refreshed source with an imported snapshot"
    )
    check_source.add_argument("--target", required=True)
    check_source.add_argument("--metadata", required=True)
    check_source.add_argument("--checked-at")
    check_source.add_argument("--source-etag")
    check_source.add_argument("--update-metadata", action="store_true")
    check_source.set_defaults(handler=check_source_command)

    digest = commands.add_parser("fingerprint", help="fingerprint the canonical decision payload")
    digest.add_argument("--target", required=True)
    digest.set_defaults(handler=fingerprint_command)

    render = commands.add_parser("render", help="render canonical JSON as Markdown")
    render.add_argument("--target", required=True)
    render.add_argument("--output")
    render.add_argument("--dry-run", action="store_true")
    render.add_argument("--allow-overwrite", action="store_true")
    render.set_defaults(handler=render_command)

    ratify = commands.add_parser("ratify", help="create an immutable ratified record version")
    ratify.add_argument("--target", required=True)
    ratify.add_argument("--output", required=True)
    ratify.add_argument("--confirmed-by", required=True)
    ratify.add_argument("--authority-role")
    ratify.add_argument("--approval-meaning", required=True)
    ratify.add_argument("--context-fingerprint", required=True)
    ratify.add_argument("--accepted-warning", action="append", default=[])
    ratify.add_argument("--signature-ref")
    ratify.add_argument("--timestamp")
    ratify.set_defaults(handler=ratify_command)

    inspect = commands.add_parser(
        "inspect",
        help="validate and explain one record, including local import standing",
    )
    inspect.add_argument("target")
    inspect.add_argument("--as-of")
    inspect.add_argument("--include-content", action="store_true")
    inspect.set_defaults(handler=inspect_command)

    resolve = commands.add_parser(
        "resolve",
        help="resolve the active applicable record set from files or directories",
    )
    resolve.add_argument("target", nargs="+")
    resolve.add_argument("--scope", action="append", default=[])
    resolve.add_argument("--as-of")
    resolve.set_defaults(handler=resolve_command)

    autonomy = commands.add_parser(
        "autonomy",
        help="evaluate a proposed action against resolved autonomy boundaries",
    )
    autonomy.add_argument("target", nargs="+")
    autonomy.add_argument("--action", required=True)
    autonomy.add_argument("--scope", action="append", default=[])
    autonomy.add_argument("--as-of")
    autonomy.set_defaults(handler=autonomy_command)

    graph = commands.add_parser(
        "graph",
        help="emit decision relationship nodes and edges",
    )
    graph.add_argument("target", nargs="+")
    graph.add_argument("--as-of")
    graph.set_defaults(handler=graph_command)

    verify_set = commands.add_parser(
        "verify-set",
        help="validate every ADRP record and source sidecar in a set",
    )
    verify_set.add_argument("target", nargs="+")
    verify_set.add_argument("--require-ratified", action="store_true")
    verify_set.set_defaults(handler=verify_set_command)

    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except DecisionRecordError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
