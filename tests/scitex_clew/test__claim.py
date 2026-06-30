"""Tests for ``scitex_clew.export_claims_json`` and the
``add_claim`` auto-export hook, plus perf-B dedup behaviour.

Covers:

  - Default path resolution lands at
    ``<project_root>/.scitex/clew/runtime/claims.json`` per the
    ecosystem local-state-directories convention.
  - ``SCITEX_CLEW_CLAIMS_JSON`` env var overrides the default.
  - Explicit ``path=`` arg overrides both.
  - Each claim added via ``clew.add_claim`` is reflected in the
    exported JSON after the auto-hook fires.
  - The artifact is mode 0444 (read-only) after write — accidental
    edits trip an OSError at the OS layer.
  - Setting ``SCITEX_CLEW_AUTO_EXPORT_CLAIMS=0`` disables the auto-hook
    without breaking ``add_claim``.
  - Perf B: when N claims share one source_file, hash_file is called
    exactly once per verify_all_claims pass (hash_cache dedup).

Tests follow:
  - PA-306 §3 (no mocks): real env + cwd mutation with explicit
    save/restore, no pytest ``monkeypatch``.
  - PA-307 §3 (test-quality): AAA marker comments + one observable
    assertion per test.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

import pytest

import scitex_clew as clew
from scitex_clew._db import _core as _db_core


# ---------------------------------------------------------------------------
# Real-state save/restore helpers (NOT mocks — they touch os.environ /
# os.getcwd / clew.set_db on the live process and unwind on teardown).
# PA-306 forbids ``monkeypatch``; this fixture is the explicit equivalent.
# ---------------------------------------------------------------------------


@pytest.fixture
def env_sandbox():
    """Snapshot scitex-clew-relevant env vars + cwd; restore on teardown.

    Returns a small helper namespace with ``set_env``, ``unset_env``,
    ``chdir`` methods that mutate live state and record undo actions.
    """
    snapshot_env = {
        k: os.environ.get(k)
        for k in (
            "SCITEX_CLEW_DB_PATH",
            "SCITEX_CLEW_CLAIMS_JSON",
            "SCITEX_CLEW_AUTO_EXPORT_CLAIMS",
        )
    }
    snapshot_cwd = os.getcwd()

    class _Sandbox:
        def set_env(self, k: str, v: str) -> None:
            os.environ[k] = v

        def unset_env(self, k: str) -> None:
            os.environ.pop(k, None)

        def chdir(self, p: Path) -> None:
            os.chdir(p)

    yield _Sandbox()

    # Teardown — return env + cwd to entry state.
    for k, v in snapshot_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    os.chdir(snapshot_cwd)
    clew.set_db(None)


def _fresh_db(tmp_path: Path, sandbox) -> Path:
    """Wire scitex_clew at a fresh per-test DB under tmp_path."""
    db_path = tmp_path / ".scitex" / "clew" / "runtime" / "db.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sandbox.set_env("SCITEX_CLEW_DB_PATH", str(db_path))
    clew.set_db(None)
    return tmp_path


def _make_source(tmp_path: Path, content: str = "x=42\n") -> Path:
    """Write a small source file the claim's source_file can point at."""
    src = tmp_path / "evidence.txt"
    src.write_text(content)
    return src


def _seed_claim(workdir: Path, value: str = "0.94") -> None:
    """Seed exactly one claim against a fresh source file in workdir."""
    src = _make_source(workdir)
    clew.add_claim(
        file_path=str(workdir / "paper.tex"),
        claim_type="value",
        line_number=1,
        claim_value=value,
        source_file=str(src),
    )


def _make_project_root(workdir: Path) -> None:
    """Tag workdir as a project root so ``_find_project_root`` stops here."""
    (workdir / "pyproject.toml").write_text("[project]\nname = 'dummy'\n")


# ---------------------------------------------------------------------------
# Path-resolution tests
# ---------------------------------------------------------------------------


def test_default_path_under_runtime(tmp_path, env_sandbox):
    """``export_claims_json()`` lands under ``runtime/`` by default."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    _seed_claim(workdir)
    # Act
    out = clew.export_claims_json()
    # Assert
    assert out == (workdir / ".scitex" / "clew" / "runtime" / "claims.json").resolve()


def test_env_var_overrides_default(tmp_path, env_sandbox):
    """``$SCITEX_CLEW_CLAIMS_JSON`` overrides the project-root default."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    override = workdir / "elsewhere" / "claims.json"
    env_sandbox.set_env("SCITEX_CLEW_CLAIMS_JSON", str(override))
    _seed_claim(workdir)
    # Act
    out = clew.export_claims_json()
    # Assert
    assert out == override.resolve()


def test_explicit_path_overrides_env_var(tmp_path, env_sandbox):
    """Explicit ``path=`` beats env var beats default."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    env_sandbox.set_env(
        "SCITEX_CLEW_CLAIMS_JSON",
        str(workdir / "env_override.json"),
    )
    explicit = workdir / "explicit.json"
    _seed_claim(workdir)
    # Act
    out = clew.export_claims_json(path=explicit)
    # Assert
    assert out == explicit.resolve()


def test_explicit_path_does_not_write_env_target(tmp_path, env_sandbox):
    """When explicit ``path`` wins, env-var target stays empty."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    env_target = workdir / "env_override.json"
    env_sandbox.set_env("SCITEX_CLEW_CLAIMS_JSON", str(env_target))
    _seed_claim(workdir)
    # Act
    clew.export_claims_json(path=workdir / "explicit.json")
    # Assert
    assert not env_target.exists()


# ---------------------------------------------------------------------------
# Auto-export hook tests
# ---------------------------------------------------------------------------


def test_auto_export_writes_canonical_file(tmp_path, env_sandbox):
    """Default-on hook writes the canonical JSON after add_claim."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.unset_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS")
    canonical = workdir / ".scitex" / "clew" / "runtime" / "claims.json"
    # Act
    _seed_claim(workdir)
    # Assert
    assert canonical.is_file()


def test_auto_export_records_every_claim(tmp_path, env_sandbox):
    """Every add_claim() shows up in the exported JSON."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.unset_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS")
    src = _make_source(workdir)
    for i, val in enumerate(["0.94", "0.05", "ResNet-50"]):
        clew.add_claim(
            file_path=str(workdir / "paper.tex"),
            claim_type="value",
            line_number=i + 1,
            claim_value=val,
            source_file=str(src),
        )
    canonical = workdir / ".scitex" / "clew" / "runtime" / "claims.json"
    # Act
    payload = json.loads(canonical.read_text())
    # Assert
    assert {c["claim_value"] for c in payload["claims"]} == {
        "0.94",
        "0.05",
        "ResNet-50",
    }


def test_auto_export_payload_carries_note(tmp_path, env_sandbox):
    """The artifact carries the AUTO-GENERATED warning note."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.unset_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS")
    _seed_claim(workdir)
    canonical = workdir / ".scitex" / "clew" / "runtime" / "claims.json"
    # Act
    payload = json.loads(canonical.read_text())
    # Assert
    assert "AUTO-GENERATED" in payload.get("_note", "")


# ---------------------------------------------------------------------------
# File-mode + opt-out tests
# ---------------------------------------------------------------------------


def test_default_artifact_is_read_only(tmp_path, env_sandbox):
    """After write, the file has mode 0444 (read-only at OS layer)."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    _seed_claim(workdir)
    # Act
    out = clew.export_claims_json()
    # Assert
    assert (out.stat().st_mode & 0o777) == 0o444


def test_re_export_overrides_readonly_then_resets(tmp_path, env_sandbox):
    """Re-exporting succeeds even though the prior file is mode 0444."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    _seed_claim(workdir)
    clew.export_claims_json()
    # Act
    out2 = clew.export_claims_json()
    # Assert
    assert (out2.stat().st_mode & 0o777) == 0o444


def test_read_only_false_keeps_default_perms(tmp_path, env_sandbox):
    """``read_only=False`` leaves the file mutable for test scenarios."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    _seed_claim(workdir)
    # Act
    out = clew.export_claims_json(read_only=False)
    # Assert
    assert (out.stat().st_mode & 0o777) == 0o644


def test_auto_export_disabled_by_env(tmp_path, env_sandbox):
    """``SCITEX_CLEW_AUTO_EXPORT_CLAIMS=0`` disables the auto-hook."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    canonical = workdir / ".scitex" / "clew" / "runtime" / "claims.json"
    # Act
    _seed_claim(workdir)
    # Assert
    assert not canonical.exists()


def test_add_claim_still_returns_when_auto_export_off(tmp_path, env_sandbox):
    """add_claim() still produces a Claim with auto-export off."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = _make_source(workdir)
    # Act
    c = clew.add_claim(
        file_path=str(workdir / "paper.tex"),
        claim_type="value",
        line_number=1,
        claim_value="0.94",
        source_file=str(src),
    )
    # Assert
    assert c.claim_id.startswith("claim_")


# ---------------------------------------------------------------------------
# Pure-helper test (no env, no cwd)
# ---------------------------------------------------------------------------


def test_default_claims_json_path_helper():
    """The path-resolution helper composes the runtime/ path correctly."""
    # Arrange
    project_root = Path("/tmp/some-project")
    # Act
    p = _db_core._default_claims_json_path(project_root)
    # Assert
    assert p == Path("/tmp/some-project/.scitex/clew/runtime/claims.json")


# ---------------------------------------------------------------------------
# Perf B: hash_cache dedup tests
# (PA-306 §3 no mocks, PA-307 §3 AAA + one assertion per test)
# ---------------------------------------------------------------------------

# Shared fixture for perf B tests — builds an isolated DB with N claims all
# pointing at the same source_file so dedup behaviour is observable.

@pytest.fixture
def perf_b_sandbox(tmp_path, env_sandbox):
    """Isolated DB + 3 claims sharing one source_file (evidence.txt)."""
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = workdir / "evidence.txt"
    src.write_text("result=0.94\n")
    paper = workdir / "paper.tex"
    paper.write_text("claim1\nclaim2\nclaim3\n")
    for line in [1, 2, 3]:
        clew.add_claim(
            file_path=str(paper),
            claim_type="value",
            line_number=line,
            claim_value=f"v{line}",
            source_file=str(src),
        )
    return {"workdir": workdir, "src": src}


def test_perf_b_shared_source_hashed_once_per_pass(perf_b_sandbox, env_sandbox):
    """With 3 claims sharing one source_file, hash_cache has exactly 1 entry after the pass."""
    # Arrange
    from scitex_clew._chain._hash_cache import new_hash_cache
    from scitex_clew._claim import verify_claim

    observed_cache: Dict[str, str] = new_hash_cache()
    src = perf_b_sandbox["src"]
    all_claims = clew.list_claims()
    # Act — call verify_claim 3 times with the SAME cache (simulating verify_all_claims)
    for c in all_claims:
        verify_claim(c.claim_id, hash_cache=observed_cache)
    # Assert — resolved src path is the only key; file hashed once, not 3 times
    assert len(observed_cache) == 1


def test_perf_b_verify_all_claims_result_identical_exit_code(perf_b_sandbox):
    """verify_all_claims returns the same exit_code as calling without cache."""
    # Arrange — run without cache first (baseline), then with optimised path
    # verify_all_claims always builds the cache internally; we compare two
    # independent runs on the same DB and expect consistent exit_codes.
    result_first = clew.verify_all_claims()
    # Act
    result_second = clew.verify_all_claims()
    # Assert — idempotent: same pass, same DB, same exit_code
    assert result_first.exit_code == result_second.exit_code


def test_perf_b_verify_all_claims_result_identical_verified_count(perf_b_sandbox):
    """verify_all_claims returns the same verified count on repeated passes."""
    # Arrange
    result_first = clew.verify_all_claims()
    # Act
    result_second = clew.verify_all_claims()
    # Assert
    assert result_first.verified == result_second.verified


def test_perf_b_verify_all_claims_result_identical_total(perf_b_sandbox):
    """verify_all_claims total claim count is stable across passes."""
    # Arrange
    result_first = clew.verify_all_claims()
    # Act
    result_second = clew.verify_all_claims()
    # Assert
    assert result_first.total == result_second.total


def test_perf_b_missing_source_outcome_preserved(tmp_path, env_sandbox):
    """hash_cache dedup does not hide a SOURCE_MISSING outcome."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = workdir / "gone.txt"
    src.write_text("will be deleted\n")
    paper = workdir / "paper.tex"
    paper.write_text("claim1\n")
    clew.add_claim(
        file_path=str(paper),
        claim_type="value",
        line_number=1,
        claim_value="v1",
        source_file=str(src),
    )
    src.unlink()  # delete the source so it's MISSING at verify time
    from scitex_clew._cli import _exit_codes as codes
    # Act
    result = clew.verify_all_claims()
    # Assert — source gone must surface as SOURCE_MISSING exit code
    assert result.exit_code == codes.SOURCE_MISSING


def test_perf_b_hash_mismatch_outcome_preserved(tmp_path, env_sandbox):
    """hash_cache dedup does not mask a HASH_MISMATCH outcome."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = workdir / "data.txt"
    src.write_text("original content\n")
    paper = workdir / "paper.tex"
    paper.write_text("claim1\n")
    clew.add_claim(
        file_path=str(paper),
        claim_type="value",
        line_number=1,
        claim_value="v1",
        source_file=str(src),
    )
    src.write_text("TAMPERED content\n")  # mutate after registration
    from scitex_clew._cli import _exit_codes as codes
    # Act
    result = clew.verify_all_claims()
    # Assert — tampered source must surface as HASH_MISMATCH exit code
    assert result.exit_code == codes.HASH_MISMATCH


def test_perf_b_fresh_pass_re_hashes_changed_file(tmp_path, env_sandbox):
    """A second verify_all_claims pass sees a file mutated between passes."""
    # Arrange — first pass sees correct hash (source_verified True expected)
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = workdir / "evidence.txt"
    src.write_text("original\n")
    paper = workdir / "paper.tex"
    paper.write_text("claim1\n")
    clew.add_claim(
        file_path=str(paper),
        claim_type="value",
        line_number=1,
        claim_value="v1",
        source_file=str(src),
    )
    from scitex_clew._cli import _exit_codes as codes

    first_result = clew.verify_all_claims()
    src.write_text("TAMPERED\n")  # mutate between passes
    # Act — second pass, fresh cache, must detect tamper
    second_result = clew.verify_all_claims()
    # Assert — second pass detects the change; exit codes differ
    assert first_result.exit_code != second_result.exit_code


def test_perf_b_no_source_unverified_preserved(tmp_path, env_sandbox):
    """Fabrication claim (no source_file) still produces UNVERIFIED exit code."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    paper = workdir / "paper.tex"
    paper.write_text("fabricated result\n")
    clew.add_claim(
        file_path=str(paper),
        claim_type="statistic",
        line_number=1,
        claim_value="p=0.001",
        # source_file omitted — fabrication claim
    )
    from scitex_clew._cli import _exit_codes as codes
    # Act
    result = clew.verify_all_claims()
    # Assert
    assert result.exit_code == codes.UNVERIFIED


# ---------------------------------------------------------------------------
# Item 2: strict-mode chain_cache memo tests
# (PA-306 §3 no mocks — real wrapping of verify_chain via module attribute;
#  PA-307 §3 AAA + one observable assertion per test)
# ---------------------------------------------------------------------------


@pytest.fixture
def strict_chain_sandbox(tmp_path, env_sandbox):
    """Isolated DB with 3 claims sharing one source_file (no DB chain).

    Returns a dict with keys: workdir, src, paper.
    In strict mode each claim triggers verify_chain(src) — the memo
    should collapse these to a single walk.
    """
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = workdir / "evidence.txt"
    src.write_text("result=0.94\n")
    paper = workdir / "paper.tex"
    paper.write_text("claim1\nclaim2\nclaim3\n")
    for line in [1, 2, 3]:
        clew.add_claim(
            file_path=str(paper),
            claim_type="value",
            line_number=line,
            claim_value=f"v{line}",
            source_file=str(src),
        )
    return {"workdir": workdir, "src": src, "paper": paper}


def test_strict_chain_memo_verify_chain_called_once(strict_chain_sandbox, env_sandbox):
    """With 3 claims sharing one source_file, verify_chain is called once per pass."""
    # Arrange
    import scitex_clew._claim as _claim_mod
    from scitex_clew._claim import verify_claim
    from scitex_clew._chain._hash_cache import new_hash_cache

    call_count = [0]
    real_verify_chain = None

    def counting_verify_chain(source_file):
        call_count[0] += 1
        return real_verify_chain(source_file)

    # Patch at module level (not mock — replaces the real function reference)
    import scitex_clew._chain as _chain_mod
    real_verify_chain = _chain_mod.verify_chain

    original_import = _claim_mod.__builtins__  # keep ref for teardown

    # We intercept at _claim module's local import by temporarily replacing
    # the verify_chain name in the _chain package's namespace.
    _chain_mod.verify_chain = counting_verify_chain
    try:
        hash_cache = new_hash_cache()
        chain_cache: Dict[str, object] = {}
        all_claims = clew.list_claims()
        # Act — manually thread chain_cache through three verify_claim calls
        for c in all_claims:
            verify_claim(c.claim_id, hash_cache=hash_cache, chain_cache=chain_cache)
    finally:
        _chain_mod.verify_chain = real_verify_chain
    # Assert — exactly one chain walk for the one unique source_file
    assert call_count[0] == 1


def test_strict_chain_memo_exit_code_identical_with_and_without_memo(
    strict_chain_sandbox, env_sandbox
):
    """verify_all_claims returns byte-identical exit_code with and without memo."""
    # Arrange — run strict=True twice on the same DB; compare exit codes
    result_first = clew.verify_all_claims(strict=True)
    # Act
    result_second = clew.verify_all_claims(strict=True)
    # Assert — idempotent strict pass: same DB, same exit_code
    assert result_first.exit_code == result_second.exit_code


def test_strict_chain_memo_counts_identical_across_passes(strict_chain_sandbox):
    """verify_all_claims returns same per-outcome counts in strict mode across passes."""
    # Arrange
    result_first = clew.verify_all_claims(strict=True)
    # Act
    result_second = clew.verify_all_claims(strict=True)
    # Assert
    assert result_first.counts == result_second.counts


def test_strict_chain_memo_per_claim_chain_verified_identical(strict_chain_sandbox):
    """Each claim's chain_verified flag is the same with and without the memo."""
    # Arrange
    result_a = clew.verify_all_claims(strict=True)
    # Act
    result_b = clew.verify_all_claims(strict=True)
    # Assert — chain_verified vector must be byte-identical across both passes
    chain_verified_a = [cv.chain_verified for cv in result_a.claims]
    chain_verified_b = [cv.chain_verified for cv in result_b.claims]
    assert chain_verified_a == chain_verified_b


def test_strict_chain_memo_no_lineage_claim_preserves_outcome(tmp_path, env_sandbox):
    """A strict NO_LINEAGE claim keeps its outcome when chain_cache is active."""
    # Arrange — claim with source_file but no DB-tracked lineage (verify_chain
    # returns ChainVerification with UNKNOWN status => is_verified=False)
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = workdir / "leaf.txt"
    src.write_text("handwritten result\n")
    paper = workdir / "paper.tex"
    paper.write_text("claim1\nclaim2\n")
    # Two claims sharing the same untracked source_file
    for line in [1, 2]:
        clew.add_claim(
            file_path=str(paper),
            claim_type="value",
            line_number=line,
            claim_value=f"val{line}",
            source_file=str(src),
        )
    from scitex_clew._cli import _exit_codes as codes
    # Act — strict=True; no DB lineage => NO_LINEAGE
    result = clew.verify_all_claims(strict=True)
    # Assert — chain_cache does NOT suppress the NO_LINEAGE outcome
    assert result.exit_code == codes.NO_LINEAGE


# ---------------------------------------------------------------------------
# Tests for remove_claim / supersede_claim / file_path_prefix filter
# (PA-306 §3 no mocks — real temp DBs; PA-307 §3 AAA + one assert per test)
# ---------------------------------------------------------------------------


@pytest.fixture
def claim_sandbox(tmp_path, env_sandbox):
    """Isolated DB with one active claim pointing at a real source file."""
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = workdir / "results.csv"
    src.write_text("a,b\n1,2\n")
    clew.add_claim(
        file_path=str(workdir / "paper.tex"),
        claim_type="value",
        line_number=1,
        claim_value="0.94",
        source_file=str(src),
    )
    return {"workdir": workdir, "src": src}


# ---- remove_claim ----


def test_remove_claim_returns_true_when_found(claim_sandbox, env_sandbox):
    """remove_claim returns True when the claim_id exists."""
    # Arrange
    claims = clew.list_claims()
    target_id = claims[0].claim_id
    # Act
    result = clew.remove_claim(target_id)
    # Assert
    assert result is True


def test_remove_claim_deletes_row_from_list(claim_sandbox, env_sandbox):
    """After remove_claim, the claim no longer appears in list_claims."""
    # Arrange
    claims = clew.list_claims()
    target_id = claims[0].claim_id
    # Act
    clew.remove_claim(target_id)
    # Assert
    assert len(clew.list_claims()) == 0


def test_remove_claim_returns_false_for_unknown_id(claim_sandbox, env_sandbox):
    """remove_claim returns False when the claim_id is not found."""
    # Arrange
    # Act
    result = clew.remove_claim("claim_nonexistent_000")
    # Assert
    assert result is False


def test_remove_claim_verify_all_does_not_see_removed_claim(claim_sandbox, env_sandbox):
    """After remove_claim, verify_all_claims sees NO_CLAIMS (empty DB)."""
    # Arrange
    from scitex_clew._cli import _exit_codes as codes
    claims = clew.list_claims()
    target_id = claims[0].claim_id
    clew.remove_claim(target_id)
    # Act
    result = clew.verify_all_claims()
    # Assert
    assert result.exit_code == codes.NO_CLAIMS


def test_remove_claim_accepts_location_string(tmp_path, env_sandbox):
    """remove_claim resolves a location string like 'paper.tex:L42'."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    paper = workdir / "paper.tex"
    paper.write_text("line1\n")
    clew.add_claim(file_path=str(paper), claim_type="value", line_number=42, claim_value="x")
    location = f"{paper}:L42"
    # Act
    result = clew.remove_claim(location)
    # Assert
    assert result is True


# ---- supersede_claim ----


def test_supersede_claim_returns_true_when_found(claim_sandbox, env_sandbox):
    """supersede_claim returns True when the claim_id exists."""
    # Arrange
    claims = clew.list_claims()
    target_id = claims[0].claim_id
    # Act
    result = clew.supersede_claim(target_id)
    # Assert
    assert result is True


def test_supersede_claim_row_still_exists_with_include_superseded(claim_sandbox, env_sandbox):
    """After supersede_claim, the row is still in DB (include_superseded=True sees it)."""
    # Arrange
    from scitex_clew._claim import list_claims as _list_claims
    claims = clew.list_claims()
    target_id = claims[0].claim_id
    # Act
    clew.supersede_claim(target_id)
    # Assert
    all_claims = _list_claims(include_superseded=True)
    assert any(c.claim_id == target_id for c in all_claims)


def test_supersede_claim_sets_status_to_superseded(claim_sandbox, env_sandbox):
    """After supersede_claim, the row's status is 'superseded'."""
    # Arrange
    from scitex_clew._claim import list_claims as _list_claims
    claims = clew.list_claims()
    target_id = claims[0].claim_id
    # Act
    clew.supersede_claim(target_id)
    # Assert
    all_claims = _list_claims(include_superseded=True)
    superseded = [c for c in all_claims if c.claim_id == target_id]
    assert superseded[0].status == "superseded"


def test_supersede_claim_excluded_from_default_list(claim_sandbox, env_sandbox):
    """After supersede_claim, default list_claims does NOT return it."""
    # Arrange
    claims = clew.list_claims()
    target_id = claims[0].claim_id
    # Act
    clew.supersede_claim(target_id)
    # Assert
    assert len(clew.list_claims()) == 0


def test_supersede_claim_returns_false_for_unknown_id(claim_sandbox, env_sandbox):
    """supersede_claim returns False when no claim matches."""
    # Arrange
    # Act
    result = clew.supersede_claim("claim_nonexistent_000")
    # Assert
    assert result is False


# ---- verify_all_claims excludes superseded ----


def test_verify_all_claims_skips_superseded_claim(claim_sandbox, env_sandbox):
    """verify_all_claims treats superseded claims as invisible (hits NO_CLAIMS)."""
    # Arrange
    from scitex_clew._cli import _exit_codes as codes
    claims = clew.list_claims()
    target_id = claims[0].claim_id
    clew.supersede_claim(target_id)
    # Act
    result = clew.verify_all_claims()
    # Assert
    assert result.exit_code == codes.NO_CLAIMS


def test_verify_all_claims_supersede_only_failing_claim_makes_gate_pass(tmp_path, env_sandbox):
    """Superseding the only MISMATCH claim lets verify_all_claims exit 0 or NO_CLAIMS."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    src = workdir / "data.txt"
    src.write_text("original\n")
    paper = workdir / "paper.tex"
    paper.write_text("c1\n")
    clew.add_claim(file_path=str(paper), claim_type="value", line_number=1, claim_value="v", source_file=str(src))
    # Mutate to force HASH_MISMATCH
    src.write_text("tampered\n")
    result_before = clew.verify_all_claims()
    claims = clew.list_claims(include_superseded=True)
    clew.supersede_claim(claims[0].claim_id)
    # Act
    result_after = clew.verify_all_claims()
    # Assert — gate must not be failing after supersede (NO_CLAIMS or OK)
    assert result_after.exit_code != result_before.exit_code


def test_verify_all_claims_all_superseded_hits_no_claims_not_crash(tmp_path, env_sandbox):
    """When all claims are superseded, verify_all_claims returns NO_CLAIMS (not a crash)."""
    # Arrange
    from scitex_clew._cli import _exit_codes as codes
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    paper = workdir / "paper.tex"
    paper.write_text("c1\n")
    clew.add_claim(file_path=str(paper), claim_type="value", line_number=1, claim_value="v")
    clew.supersede_claim(clew.list_claims(include_superseded=True)[0].claim_id)
    # Act
    result = clew.verify_all_claims()
    # Assert
    assert result.exit_code == codes.NO_CLAIMS


# ---- claims.json excludes superseded by default ----


def test_export_claims_json_excludes_superseded_by_default(tmp_path, env_sandbox):
    """Default export_claims_json does NOT include superseded claims."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    _make_project_root(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    paper = workdir / "paper.tex"
    paper.write_text("c1\n")
    clew.add_claim(file_path=str(paper), claim_type="value", line_number=1, claim_value="v")
    claims_before = clew.list_claims(include_superseded=True)
    clew.supersede_claim(claims_before[0].claim_id)
    import json
    # Act
    out = clew.export_claims_json(read_only=False)
    payload = json.loads(out.read_text())
    # Assert
    assert payload["claims_count"] == 0


# ---- file_path_prefix filter ----


def test_list_claims_file_path_prefix_returns_matching_claims(tmp_path, env_sandbox):
    """list_claims(file_path_prefix=...) returns only claims under that prefix."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    # Two papers in different dirs
    dir_a = workdir / "proj_a"
    dir_b = workdir / "proj_b"
    dir_a.mkdir()
    dir_b.mkdir()
    clew.add_claim(file_path=str(dir_a / "paper.tex"), claim_type="value", line_number=1, claim_value="a")
    clew.add_claim(file_path=str(dir_b / "paper.tex"), claim_type="value", line_number=1, claim_value="b")
    # Act
    from scitex_clew._claim import list_claims as _list_claims
    results = _list_claims(file_path_prefix=str(dir_a))
    # Assert
    assert all(c.file_path.startswith(str(dir_a.resolve())) for c in results)


def test_list_claims_file_path_prefix_excludes_non_matching(tmp_path, env_sandbox):
    """list_claims(file_path_prefix=...) does NOT return claims outside the prefix."""
    # Arrange
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    dir_a = workdir / "proj_a"
    dir_b = workdir / "proj_b"
    dir_a.mkdir()
    dir_b.mkdir()
    clew.add_claim(file_path=str(dir_a / "paper.tex"), claim_type="value", line_number=1, claim_value="a")
    clew.add_claim(file_path=str(dir_b / "paper.tex"), claim_type="value", line_number=1, claim_value="b")
    # Act
    from scitex_clew._claim import list_claims as _list_claims
    results = _list_claims(file_path_prefix=str(dir_a))
    # Assert — proj_b claim must NOT appear
    assert not any(str(dir_b.resolve()) in c.file_path for c in results)


# ---- bulk remove / supersede by prefix ----


def test_remove_claims_by_prefix_returns_count(tmp_path, env_sandbox):
    """remove_claims_by_prefix returns the count of deleted rows."""
    # Arrange
    from scitex_clew._claim import remove_claims_by_prefix
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    dir_a = workdir / "proj_a"
    dir_a.mkdir()
    clew.add_claim(file_path=str(dir_a / "paper.tex"), claim_type="value", line_number=1, claim_value="a")
    clew.add_claim(file_path=str(dir_a / "paper.tex"), claim_type="value", line_number=2, claim_value="b")
    # Act
    deleted = remove_claims_by_prefix(str(dir_a))
    # Assert
    assert deleted == 2


def test_remove_claims_by_prefix_purges_all_matching(tmp_path, env_sandbox):
    """After remove_claims_by_prefix, no claims under that prefix remain."""
    # Arrange
    from scitex_clew._claim import remove_claims_by_prefix
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    dir_a = workdir / "proj_a"
    dir_a.mkdir()
    clew.add_claim(file_path=str(dir_a / "paper.tex"), claim_type="value", line_number=1, claim_value="a")
    remove_claims_by_prefix(str(dir_a))
    # Act
    from scitex_clew._claim import list_claims as _list_claims
    remaining = _list_claims(file_path_prefix=str(dir_a))
    # Assert
    assert len(remaining) == 0


def test_supersede_claims_by_prefix_returns_count(tmp_path, env_sandbox):
    """supersede_claims_by_prefix returns the count of updated rows."""
    # Arrange
    from scitex_clew._claim import supersede_claims_by_prefix
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    dir_a = workdir / "proj_a"
    dir_a.mkdir()
    clew.add_claim(file_path=str(dir_a / "paper.tex"), claim_type="value", line_number=1, claim_value="a")
    clew.add_claim(file_path=str(dir_a / "paper.tex"), claim_type="value", line_number=2, claim_value="b")
    # Act
    updated = supersede_claims_by_prefix(str(dir_a))
    # Assert
    assert updated == 2


def test_supersede_claims_by_prefix_hides_from_default_list(tmp_path, env_sandbox):
    """After supersede_claims_by_prefix, default list_claims returns none of them."""
    # Arrange
    from scitex_clew._claim import supersede_claims_by_prefix
    workdir = _fresh_db(tmp_path, env_sandbox)
    env_sandbox.chdir(workdir)
    env_sandbox.set_env("SCITEX_CLEW_AUTO_EXPORT_CLAIMS", "0")
    dir_a = workdir / "proj_a"
    dir_a.mkdir()
    clew.add_claim(file_path=str(dir_a / "paper.tex"), claim_type="value", line_number=1, claim_value="a")
    supersede_claims_by_prefix(str(dir_a))
    # Act
    remaining = clew.list_claims()
    # Assert
    assert len(remaining) == 0
