#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
import subprocess
from typing import Any, Dict, List, Optional, Set, Union

JSON = Dict[str, Any]


def load_json_from_git(ref: str, path: str) -> JSON:
    out = subprocess.check_output(["git", "show", f"{ref}:{path}"])
    return json.loads(out.decode("utf-8"))


def load_json_from_file(path: str) -> JSON:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def to_type_set(t: Union[str, List[str], None]) -> Set[str]:
    if t is None:
        return set()
    if isinstance(t, str):
        return {t}
    return set(t)


def compare_types(old: Any, new: Any, path: str, violations: List[str]) -> None:
    old_set = to_type_set(old)
    new_set = to_type_set(new)
    if old_set and new_set and not old_set.issubset(new_set):
        violations.append(f"type narrowed at {path}: {sorted(old_set)} -> {sorted(new_set)}")


def compare_enum(old: Any, new: Any, path: str, violations: List[str]) -> None:
    if isinstance(old, list) and isinstance(new, list):
        old_set = set(old)
        new_set = set(new)
        if not old_set.issubset(new_set):
            violations.append(f"enum shrunk at {path}: missing {sorted(old_set - new_set)}")


def compare_constraints(old: JSON, new: JSON, path: str, violations: List[str]) -> None:
    # numeric
    if "minimum" in old and "minimum" in new and isinstance(old["minimum"], (int, float)) and isinstance(new["minimum"], (int, float)):
        if new["minimum"] > old["minimum"]:
            violations.append(f"minimum increased at {path}: {old['minimum']} -> {new['minimum']}")
    if "maximum" in old and "maximum" in new and isinstance(old["maximum"], (int, float)) and isinstance(new["maximum"], (int, float)):
        if new["maximum"] < old["maximum"]:
            violations.append(f"maximum decreased at {path}: {old['maximum']} -> {new['maximum']}")
    # string
    if "minLength" in old and "minLength" in new and isinstance(old["minLength"], int) and isinstance(new["minLength"], int):
        if new["minLength"] > old["minLength"]:
            violations.append(f"minLength increased at {path}: {old['minLength']} -> {new['minLength']}")
    if "maxLength" in old and "maxLength" in new and isinstance(old["maxLength"], int) and isinstance(new["maxLength"], int):
        if new["maxLength"] < old["maxLength"]:
            violations.append(f"maxLength decreased at {path}: {old['maxLength']} -> {new['maxLength']}")


def normalize_required(v: Any) -> Set[str]:
    if isinstance(v, list):
        return set(x for x in v if isinstance(x, str))
    return set()


def compare_required(old: JSON, new: JSON, path: str, violations: List[str]) -> None:
    old_req = normalize_required(old.get("required"))
    new_req = normalize_required(new.get("required"))
    added = new_req - old_req
    if added:
        violations.append(f"required added at {path}: {sorted(added)}")


def get_additional_props(v: JSON) -> Optional[bool]:
    ap = v.get("additionalProperties")
    if isinstance(ap, bool):
        return ap
    return None


def compare_additional_properties(old: JSON, new: JSON, path: str, violations: List[str]) -> None:
    old_ap = get_additional_props(old)
    new_ap = get_additional_props(new)
    old_eff = True if old_ap is None else old_ap
    new_eff = True if new_ap is None else new_ap
    if old_eff and not new_eff:
        violations.append(f"additionalProperties tightened at {path}: True -> False")


def compare_object(old: JSON, new: JSON, path: str, violations: List[str]) -> None:
    compare_required(old, new, path, violations)
    old_props = old.get("properties") or {}
    new_props = new.get("properties") or {}
    if isinstance(old_props, dict) and isinstance(new_props, dict):
        for k in old_props.keys():
            if k not in new_props:
                violations.append(f"property removed at {path}: {k}")
        for k, old_sub in old_props.items():
            new_sub = new_props.get(k)
            if isinstance(old_sub, dict) and isinstance(new_sub, dict):
                compare_schema(old_sub, new_sub, f"{path}.properties.{k}", violations)
    compare_additional_properties(old, new, path, violations)


def compare_array(old: JSON, new: JSON, path: str, violations: List[str]) -> None:
    old_items = old.get("items")
    new_items = new.get("items")
    if isinstance(old_items, dict) and isinstance(new_items, dict):
        compare_required(old_items, new_items, f"{path}.items", violations)
        compare_schema(old_items, new_items, f"{path}.items", violations)


def compare_schema(old: JSON, new: JSON, path: str, violations: List[str]) -> None:
    compare_types(old.get("type"), new.get("type"), path, violations)
    if "enum" in old or "enum" in new:
        compare_enum(old.get("enum"), new.get("enum"), path, violations)
    compare_constraints(old, new, path, violations)

    old_types = to_type_set(old.get("type"))
    new_types = to_type_set(new.get("type"))
    tset = new_types or old_types
    if not tset or "object" in tset:
        compare_object(old, new, path, violations)
    if "array" in tset:
        compare_array(old, new, path, violations)


def main() -> int:
    p = argparse.ArgumentParser(description="Schema compatibility checker")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--base", help="Git ref for base schema (e.g., main)")
    g.add_argument("--base-file", help="Path to base schema file")
    p.add_argument("--path", required=True, help="Schema path (file path or repo path with --base)")
    args = p.parse_args()

    try:
        if args.base:
            old = load_json_from_git(args.base, args.path)
        else:
            old = load_json_from_file(args.base_file)  # type: ignore[arg-type]
        new = load_json_from_file(args.path)
    except Exception as e:
        print(f"Failed to load schemas: {e}", file=sys.stderr)
        return 2

    violations: List[str] = []
    compare_schema(old, new, "#", violations)
    if violations:
        print("Schema compatibility violations detected:", file=sys.stderr)
        for v in violations:
            print(f"- {v}", file=sys.stderr)
        return 1
    print("Schema compatibility check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

