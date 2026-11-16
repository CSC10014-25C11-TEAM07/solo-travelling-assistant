# Bảo 04 data readiness implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan in the current session. Track checks below.

**Goal:** Deliver the 15/11 MOCK freeze, a reviewed minimum source pack and precise source blockers for the assignment due 18/11.

**Architecture:** Continue the merged PR #19 catalog and fixtures on current main. Extend the offline audit rather than the PLAN/ADAPT business engine; export a separate review bundle without writing SQLite. Replay the full fixtures through the existing F05 consumer in explicit rules/MOCK mode.

**Tech Stack:** Existing Python, Pydantic, unittest and JSON; no new dependencies.

**Spec:** `/Users/trangiabao/Downloads/Phân công xong app 14_11.md`, sections 3.5, 4.3 and 5. The user requested implementation of this assignment; its scope and technology are already decided.

## Global constraints

- Preserve VERIFIED/UNVERIFIED/MOCK; a successful request or URL never verifies a venue.
- Do not edit teammates' backend integration, auth, SQLite, AI or mobile modules.
- Use the approved API/data contracts; no new public fields or endpoints.
- Four independent MOCK cases T06/T08/T13/T15, full 3/4-day fixtures, no actual Gemini calls.
- Source dates/weekday, directed travel, visit duration, rest access and deadline all matter.
- No merge; branch/PR handoff only. Keep local package-lock.json unchanged.

## Review focus

- A route labelled VERIFIED that still finishes late after VISIT/waiting must be blocked.
- Waiting, a closed rest venue, or a rest stop outside the route cannot satisfy daily REST.
- Rain coverage includes previous→replacement→next→end; reverse legs cannot fill gaps.
- Export must preserve labels and never overwrite source or existing output directories.
- Consumer replay success proves domain behavior only, not API/SQLite/AI/device acceptance.

### Task 1: Source route and replacement readiness

**Files:** `backend/source_readiness.py`, `backend/data_handoff.py`, `backend/tests/test_source_readiness.py`.

**Interfaces:** Keep `source_route(route, catalog) -> dict`; add `source_replacements(paths, catalog) -> list[dict]`. Add `source_adapt_checks` to the manifest and offline report only.

- [x] Write failing tests: VISIT makes a route late, wait for next opening, closed REST, rest/visit outside sequence, unknown/missing directed final leg and invalid date range.
- [x] Run `python -m unittest discover -s backend/tests -p test_source_readiness.py -v` and observe failures.
- [x] Audit structural dates and endpoints, accumulate travel+REST+VISIT lower bounds, compute earliest schedules with opening windows; report exact gaps and never infer missing data.
- [x] Test rain with missing incoming/outgoing/final directed legs and non-INDOOR candidate.
- [x] Run the new tests and full backend suite; commit this independently verifiable change.

### Task 2: Reviewed source pack and reproducible export

**Files:** `backend/data/{places,data_review,place_coordinates,travel_times,travel_time_evidence}.json`, `backend/data/handoff/{manifest,source_checks,source_adapt_checks}.json`, `backend/scripts/prepare_source_bundle.py`, `backend/tests/test_source_bundle.py`.

**Interfaces:** Export source `places.json`, `travel_times.json`, route/ADAPT configs, provenance and readiness report into a NEW `--output-dir`; no database mutation or status promotion. Missing/blocked real-world data stays visible.

- [x] Read current primary sources for selected venues; update only supported facts and actual read timestamps.
- [x] Add only the directed edges needed by declared rain/drop checks, retaining raw estimates and endpoint review.
- [x] Write export tests for complete selection, no MOCK, unchanged labels, blocked readiness, existing output and source-directory protection; observe RED.
- [x] Implement the standalone export CLI and verify JSON loads with `PlaceCatalog`.
- [x] Run catalog validators, offline audit, exporter and full suite; commit.

### Task 3: Freeze MOCK and handoff evidence

**Files:** `backend/scripts/replay_handoff_f05.py`, `backend/tests/test_handoff_replay.py`, `docs/DATASET-HANDOFF-BAO04.md`, `backend/data/README.md`, `docs/testing/*` handoff reports.

**Interfaces:** `replay(directory) -> dict` reports T06/T08/T13/T15 × 3/4 days via the real merged F05 consumer. Check counts 2/0/1/0, end16:15, preserved DONE/other days, serialized stored-option validation and independently audited snapshots.

- [x] Behavior tests cover consumer replay and a missing rain leg; current suite reverified at9679151. Historical RED execution is documented in the handoff report, not re-established by this review.
- [x] Implement reproducible rules-only replay without persistence or AI claims.
- [x] Re-run all validators, backend suite, replay and authenticated F01 preference tests with temporary SQLite; record commit/version and precise scope.
- [x] Update handoff/status docs: four MOCK cases ready, source blockers with next actions, device/AI/SQLite not inferred. Update S01 prerequisite because PR #18 is now merged.
- [x] Fresh whole-branch read-only review of0b446b1..9679151; no critical/important findings. Re-ran103 backend tests,three validators,audit,replay and source export; fixed two minor documentation inconsistencies. Updated persistent project context in the original workspace.
- PR handoff references #8 and explicitly leaves real-source readiness and device/live integration acceptance outstanding; see `docs/DATASET-HANDOFF-PR.md`.
