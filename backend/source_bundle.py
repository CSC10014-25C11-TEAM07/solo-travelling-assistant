"""Export a minimal source review pack; does not import/reset any database."""

import json
from pathlib import Path

from data_handoff import audit, read
from place_catalog import PlaceCatalog


def export_source_bundle(directory: Path, output: Path):
    directory, output = directory.resolve(), output.resolve()
    if output.is_relative_to(directory) or directory.is_relative_to(output):
        raise ValueError("OUTPUT_OVERLAPS_SOURCE")
    if output.exists():
        raise ValueError("OUTPUT_EXISTS: choose a new output directory")
    catalog = PlaceCatalog.load(directory)
    manifest = read(directory / "handoff/manifest.json")
    routes = read(directory / manifest["source_routes"])
    checks = read(directory / manifest["source_adapt_checks"])
    ids = {pid for route in routes for day in route["days"] for pid in day["place_sequence"]}
    ids.update(pid for check in checks for pid in check["place_sequence"])
    places = [catalog.places[pid] for pid in sorted(ids)]
    legs = [leg for pair, leg in catalog.travel_times.items() if set(pair) <= ids]
    if any(p.data_status == "MOCK" for p in places) or any(leg.data_status == "MOCK" for leg in legs):
        raise ValueError("MOCK_IN_SOURCE_BUNDLE")
    report = audit(directory)
    if not report["checks_passed"]:
        raise ValueError("HANDOFF_CHECKS_FAILED")
    review = read(directory / "data_review.json")
    review["places"] = [p for p in review["places"] if p["place_id"] in ids]
    source_checks = read(directory / "handoff/source_checks.json")
    source_checks["observations"] = [p for p in source_checks["observations"] if p["place_id"] in ids]
    ready = all(route["ready_for_real_plan"] for route in report["source_routes"])
    summary = {"dataset_version": manifest["dataset_version"], "mode": "REVIEW_ONLY",
               "place_count": len(places), "directed_leg_count": len(legs),
               "ready_for_real_plan": ready, "source_adapt_ready": False,
               "note": "JSON review/import input only; không ghi SQLite, không đổi nhãn. Đọc readiness.json trước khi dùng."}
    contents = {
        "manifest.json": summary,
        "places.json": [p.model_dump() for p in places],
        "travel_times.json": [leg.model_dump() for leg in legs],
        "routes_source.json": routes, "source_adapt_checks.json": checks,
        "readiness.json": {key: report[key] for key in ("dataset_version", "source_routes", "source_adapt_checks")},
        "data_review.json": review, "source_checks.json": source_checks,
        "sources.json": read(directory / "sources.json"),
        "place_coordinates.json": [p for p in read(directory / "place_coordinates.json") if p["place_id"] in ids],
        "travel_time_evidence.json": [e for e in read(directory / "travel_time_evidence.json")
                                      if {e["from_place_id"], e["to_place_id"]} <= ids],
    }
    # Finish all validation/serialization before reserving a new directory. Never
    # reuse even an empty existing directory or an existing symlink destination.
    rendered = {name: json.dumps(value, ensure_ascii=False, indent=2) + "\n" for name, value in contents.items()}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(exist_ok=False)
    for name, value in rendered.items():
        (output / name).write_text(value, encoding="utf-8")
    return {**summary, "output_dir": str(output)}
