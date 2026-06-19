#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the fail-loud exit-code core.

Covers the pure reducer (:func:`scitex_clew._cli._exit_codes.worst_code`
+ the severity table) and the Python-API entry point
``scitex_clew.verify_all_claims`` (which the ``clew verify`` CLI wraps).

Per PA-306 §3 (no mocks): the API tests touch a real isolated DB seeded
with real runs / file hashes. Per PA-307 §3: AAA marker comments + one
observable assertion per test.
"""

from __future__ import annotations

import os

import pytest

import scitex_clew as clew
import scitex_clew._db as _db_module
from scitex_clew._cli import _exit_codes as codes
from scitex_clew._db import set_db
from scitex_clew._hash import hash_file


# ---------------------------------------------------------------------------
# Pure severity reducer
# ---------------------------------------------------------------------------


class TestWorstCode:
    def test_empty_is_ok(self):
        # Arrange
        empty = []
        # Act
        worst = codes.worst_code(empty)
        # Assert
        assert worst == codes.OK

    def test_hash_mismatch_outranks_unverified(self):
        # Arrange — both a fabrication and a tamper present.
        mixed = [codes.UNVERIFIED, codes.HASH_MISMATCH]
        # Act
        worst = codes.worst_code(mixed)
        # Assert — the harder integrity failure must win.
        assert worst == codes.HASH_MISMATCH

    def test_unverified_outranks_no_lineage(self):
        # Arrange
        mixed = [codes.NO_LINEAGE, codes.UNVERIFIED]
        # Act
        worst = codes.worst_code(mixed)
        # Assert
        assert worst == codes.UNVERIFIED

    def test_any_failure_outranks_ok(self):
        # Arrange
        mixed = [codes.OK, codes.NO_LINEAGE, codes.OK]
        # Act
        worst = codes.worst_code(mixed)
        # Assert
        assert worst == codes.NO_LINEAGE

    def test_codes_are_distinct(self):
        # Arrange
        all_codes = [
            codes.OK,
            codes.UNVERIFIED,
            codes.SOURCE_MISSING,
            codes.HASH_MISMATCH,
            codes.NO_LINEAGE,
            codes.NO_CLAIMS,
        ]
        # Act — the contract relies on each outcome being unique.
        unique = set(all_codes)
        # Assert
        assert len(unique) == len(all_codes)


# ---------------------------------------------------------------------------
# verify_all_claims Python API
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    # Real env mutation with explicit undo (PA-306 forbids monkeypatch):
    # disable the read-only claims.json auto-export between temp DBs.
    prev = os.environ.get("SCITEX_CLEW_AUTO_EXPORT_CLAIMS")
    os.environ["SCITEX_CLEW_AUTO_EXPORT_CLAIMS"] = "0"
    set_db(tmp_path / "verify_all.db")
    yield _db_module.get_db()
    _db_module._DB_INSTANCE = None
    if prev is None:
        os.environ.pop("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", None)
    else:
        os.environ["SCITEX_CLEW_AUTO_EXPORT_CLAIMS"] = prev


def _seed_tracked_source(db, tmp_path):
    src = tmp_path / "results.json"
    src.write_text('{"acc": 0.94}\n')
    sid = "2026Y-06M-19D-00h00m00s_Seed-main"
    db.add_run(sid, str(tmp_path / "make_results.py"))
    db.add_file_hash(sid, str(src.resolve()), hash_file(src), "output")
    db.finish_run(sid, status="success")
    return src


class TestVerifyAllClaimsApi:
    def test_no_claims_returns_no_claims_code(self, isolated_db):
        # Arrange — empty DB.
        # Act
        summary = clew.verify_all_claims()
        # Assert
        assert summary.exit_code == codes.NO_CLAIMS

    def test_mixed_set_returns_worst_code(self, isolated_db, tmp_path):
        # Arrange — one OK claim + one fabrication claim in the same set.
        src = _seed_tracked_source(isolated_db, tmp_path)
        paper = tmp_path / "paper.tex"
        paper.write_text("acc=0.94\nfabricated p=0.003\n")
        clew.add_claim(
            file_path=str(paper),
            claim_type="value",
            line_number=1,
            claim_value="0.94",
            source_file=str(src),
        )
        clew.add_claim(
            file_path=str(paper),
            claim_type="statistic",
            line_number=2,
            claim_value="p=0.003",  # no source -> fabrication
        )
        # Act
        summary = clew.verify_all_claims()
        # Assert — the unverified fabrication drags the whole set to nonzero.
        assert summary.exit_code == codes.UNVERIFIED

    def test_ok_set_reports_full_verified_count(self, isolated_db, tmp_path):
        # Arrange
        src = _seed_tracked_source(isolated_db, tmp_path)
        paper = tmp_path / "paper.tex"
        paper.write_text("acc=0.94\n")
        clew.add_claim(
            file_path=str(paper),
            claim_type="value",
            line_number=1,
            claim_value="0.94",
            source_file=str(src),
        )
        # Act
        summary = clew.verify_all_claims()
        # Assert
        assert summary.exit_code == codes.OK and summary.verified == 1

    def test_strict_flag_is_echoed_in_summary(self, isolated_db, tmp_path):
        # Arrange
        src = _seed_tracked_source(isolated_db, tmp_path)
        paper = tmp_path / "paper.tex"
        paper.write_text("acc=0.94\n")
        clew.add_claim(
            file_path=str(paper),
            claim_type="value",
            line_number=1,
            claim_value="0.94",
            source_file=str(src),
        )
        # Act
        summary = clew.verify_all_claims(strict=True)
        # Assert
        assert summary.strict is True


# ---------------------------------------------------------------------------
# classify_exit — severity-aware reduction (pure, the linter-for-provenance core)
# ---------------------------------------------------------------------------


class TestClassifyExit:
    def test_warning_only_is_ok_and_listed(self):
        # Arrange — NO_CLAIMS downgraded to a tolerated warning.
        sev = dict(codes.DEFAULT_SEVERITY)
        sev[codes.NO_CLAIMS] = codes.Severity.WARNING
        # Act
        decision = codes.classify_exit([codes.NO_CLAIMS], sev)
        # Assert — exit OK, surfaced as a warning, no errors.
        assert decision == (codes.OK, [], ["NO_CLAIMS"])

    def test_error_pattern_sets_exit_code(self):
        # Arrange
        sev = dict(codes.DEFAULT_SEVERITY)
        # Act
        exit_code, errors, _ = codes.classify_exit([codes.UNVERIFIED], sev)
        # Assert
        assert (exit_code, errors) == (codes.UNVERIFIED, ["UNVERIFIED"])

    def test_worst_error_wins(self):
        # Arrange — both error-severity; the integrity failure must win.
        sev = dict(codes.DEFAULT_SEVERITY)
        # Act
        exit_code, _, _ = codes.classify_exit(
            [codes.UNVERIFIED, codes.HASH_MISMATCH], sev
        )
        # Assert
        assert exit_code == codes.HASH_MISMATCH

    def test_ignore_severity_is_dropped(self):
        # Arrange
        sev = dict(codes.DEFAULT_SEVERITY)
        sev[codes.UNVERIFIED] = codes.Severity.IGNORE
        # Act
        decision = codes.classify_exit([codes.UNVERIFIED], sev)
        # Assert
        assert decision == (codes.OK, [], [])


# ---------------------------------------------------------------------------
# resolve_severity — defaults, --strict promotion, fail-loud config
# ---------------------------------------------------------------------------


@pytest.fixture
def clean_scopes(tmp_path):
    # Pin user scope to an empty dir + provide a clean git-root project scope,
    # so resolved severities are deterministic (real env mutation, undone).
    prev = os.environ.get("SCITEX_DIR")
    os.environ["SCITEX_DIR"] = str(tmp_path / "empty_user")
    root = tmp_path / "proj"
    (root / ".git").mkdir(parents=True, exist_ok=True)
    yield root
    if prev is None:
        os.environ.pop("SCITEX_DIR", None)
    else:
        os.environ["SCITEX_DIR"] = prev


def _project_severity(root, body):
    d = root / ".scitex" / "clew"
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.yaml").write_text(body)


class TestResolveSeverity:
    def test_default_no_lineage_is_warning(self, clean_scopes):
        # Arrange — no config files present.
        # Act
        sev = codes.resolve_severity(start=clean_scopes)
        # Assert
        assert sev[codes.NO_LINEAGE] == codes.Severity.WARNING

    def test_strict_promotes_no_lineage_to_error(self, clean_scopes):
        # Arrange — no config files present.
        # Act
        sev = codes.resolve_severity(start=clean_scopes, strict=True)
        # Assert
        assert sev[codes.NO_LINEAGE] == codes.Severity.ERROR

    def test_project_config_downgrades_pattern(self, clean_scopes):
        # Arrange — downgrade the fabrication pattern via project config.
        _project_severity(
            clean_scopes, "verify:\n  severity:\n    unverified: warning\n"
        )
        # Act
        sev = codes.resolve_severity(start=clean_scopes)
        # Assert
        assert sev[codes.UNVERIFIED] == codes.Severity.WARNING

    def test_invalid_severity_value_raises(self, clean_scopes):
        # Arrange
        _project_severity(clean_scopes, "verify:\n  severity:\n    unverified: bogus\n")
        # Act — resolving with an invalid severity value is the action.
        # Assert — fail loud, no silent fallback.
        with pytest.raises(ValueError):
            codes.resolve_severity(start=clean_scopes)

    def test_unknown_pattern_key_raises(self, clean_scopes):
        # Arrange
        _project_severity(
            clean_scopes, "verify:\n  severity:\n    not_a_pattern: error\n"
        )
        # Act — resolving with an unknown pattern key is the action.
        # Assert
        with pytest.raises(ValueError):
            codes.resolve_severity(start=clean_scopes)


# ---------------------------------------------------------------------------
# VerificationResult dataclass
# ---------------------------------------------------------------------------


class TestVerificationResult:
    def test_to_dict_has_canonical_json_keys(self, isolated_db):
        # Arrange — empty DB yields a NO_CLAIMS result.
        result = clew.verify_all_claims()
        # Act
        payload = result.to_dict()
        # Assert
        assert set(payload) == {
            "exit_code",
            "exit_name",
            "reason",
            "strict",
            "total",
            "verified",
            "counts",
            "severities",
            "errors",
            "warnings",
            "claims",
        }

    def test_ok_property_tracks_verified_set(self, isolated_db, tmp_path):
        # Arrange — one fully-grounded, lineage-backed claim.
        src = _seed_tracked_source(isolated_db, tmp_path)
        paper = tmp_path / "paper.tex"
        paper.write_text("acc=0.94\n")
        clew.add_claim(
            file_path=str(paper),
            claim_type="value",
            line_number=1,
            claim_value="0.94",
            source_file=str(src),
        )
        # Act
        result = clew.verify_all_claims()
        # Assert
        assert result.ok is True and result.verified == 1


# EOF
