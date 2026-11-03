#!/usr/bin/env python
"""Static checks for a SightLab 2.x experiment script (design 6.1). No Vizard needed.

Standard library only; Python 3.8 syntax so it also runs under Vizard's interpreter.

  python check.py experiment.py [--api sightlab-api.json] [--sightlab-utils DIR]
                                [--resources resources-list.txt] [--json]

Exit 1 when any error is found, 0 otherwise. With --sightlab-utils the API map is built
from that installed package at run time (preferred on a customer machine); otherwise the
bundled --api JSON is used. Findings:

  E_SYNTAX                  the script does not parse
  E_UNKNOWN_METHOD          sightlab.<name>() is not a method of that class
  E_UNKNOWN_KWARG           a keyword argument the method or constructor does not take
  E_NO_RUN_EXPERIMENT       viztask.schedule(sightlab.runExperiment) is missing
  W_START_TRIAL_IMMEDIATE   the experiment generator calls startTrial before any viztask wait,
                            so it can run before SightLab has finished loading (shipped examples
                            wait on EXPERIMENT_START or on the space key first)
  W_NO_TRIAL_COUNT          gui=False, the script loops over getTrialCount(), and setTrialCount()
                            is never called: the loop runs once
  W_VIZ_GO                  viz.go() is called (SightLab already does this)
  W_NO_GAZE_OBJECT          gui=False and no addSceneObject(..., gaze=True): no gaze data on
                            objects is recorded (fine for a study that does not need it)
  W_UNKNOWN_ENVIRONMENT     a sightlab_resources/ path not present in the resources list
  W_UNPAIRED_TRIAL          startTrial and endTrial call counts differ
  W_NO_INSTANCE             sightlab_utils is imported but no SightLab instance was found, so
                            nothing above was checked (silence is not a pass)
  W_KEY_REPLACES_TRIGGER    textContinueKey= given on a call whose text tells the participant to
                            press the trigger; the key REPLACES the trigger wait, so a headset
                            participant cannot continue
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

SIGHTLAB_CLASSES = ("SightLab", "SightLabServer", "SightLabClient")
RESOURCE_PREFIX = "sightlab_resources/"


# ----------------------------------------------------------------------------- API map

def load_api(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _params_of(fn):
    """Parameter names of a FunctionDef, minus self, plus whether it takes **kwargs."""
    a = fn.args
    names = [x.arg for x in getattr(a, "posonlyargs", []) + a.args if x.arg != "self"]
    names += [x.arg for x in a.kwonlyargs]
    return names, a.kwarg is not None


def build_api_from_package(package_dir):
    """A reduced API map (classes, methods, params) read from an installed sightlab_utils.

    Mirrors tools/gen_api_map.py closely enough for the checks here; kept in this file so
    the harness ships without tools/.
    """
    path = os.path.join(package_dir, "sightlab.py")
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        tree = ast.parse(fh.read(), filename=path)
    classes = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {}
        init_params = []
        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            names, var_kw = _params_of(item)
            if item.name == "__init__":
                init_params = [{"name": n} for n in names]
            elif not item.name.startswith("_"):
                methods[item.name] = {"params": [{"name": n} for n in names], "signature": item.name + "(...)", "var_kwargs": var_kw}
        classes[node.name] = {"methods": methods, "init_params": init_params, "bases": [ast.unparse(b) if hasattr(ast, "unparse") else "" for b in node.bases]}
    version = "unknown"
    init = os.path.join(package_dir, "__init__.py")
    if os.path.isfile(init):
        with open(init, "r", encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                if line.strip().startswith("__version__"):
                    version = line.split("=", 1)[1].strip().strip("\"'")
    return {"sightlab_utils_version": version, "modules": {"sightlab": {"classes": classes, "functions": {}, "constants": []}}, "settings_constants": []}


def _class_table(api):
    """class name -> {'methods': {name: set(param names) | None for **kwargs}, 'init': set|None}.

    Inherited methods are folded in (SightLabServer and SightLabClient extend SightLab).
    """
    classes = api["modules"]["sightlab"]["classes"]
    table = {}

    def resolve(cname, seen=()):
        cls = classes.get(cname)
        if cls is None or cname in seen:
            return {"methods": {}, "init": None}
        out = {"methods": {}, "init": None}
        for base in cls.get("bases", []):
            inherited = resolve(base, seen + (cname,))
            out["methods"].update(inherited["methods"])
            out["init"] = inherited["init"]
        for mname, m in cls["methods"].items():
            names = {p["name"] for p in m["params"]}
            takes_any = m.get("var_kwargs") or any(p.get("kind") == "kwarg" for p in m["params"])
            out["methods"][mname] = None if takes_any else names
        if cls.get("init_params"):
            out["init"] = {p["name"] for p in cls["init_params"] if p.get("kind") != "kwarg"}
            if any(p.get("kind") == "kwarg" for p in cls["init_params"]):
                out["init"] = None
        return out

    for cname in classes:
        table[cname] = resolve(cname)
    return table


# ----------------------------------------------------------------------------- the check

def _finding(code, node, message):
    return {"code": code, "line": getattr(node, "lineno", 0), "message": message}


def _name_of(node):
    return node.id if isinstance(node, ast.Name) else None


def _dotted(node):
    """'a.b.c' for a Name/Attribute chain (so `self.sightlab` and `sightlab_utils.sightlab` resolve), else None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return base + "." + node.attr if base else None
    return None


def default_api_path():
    """Where a copied check.py looks for the API map when --api is not given."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "sightlab-api.json"),
        os.path.join(here, "..", "api", "sightlab-api.json"),
        os.path.join(os.getcwd(), "harness", "sightlab-api.json"),
    ]
    skills = os.path.join(os.getcwd(), ".claude", "skills")
    if os.path.isdir(skills):
        for name in sorted(os.listdir(skills)):
            candidates.append(os.path.join(skills, name, "api", "sightlab-api.json"))
    for c in candidates:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return None


def default_resources_path():
    """Where a copied check.py looks for resources.json (names under sightlab_resources/)."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "resources.json"),
        os.path.join(here, "..", "api", "resources.json"),
        os.path.join(os.getcwd(), "harness", "resources.json"),
    ]
    skills = os.path.join(os.getcwd(), ".claude", "skills")
    if os.path.isdir(skills):
        for name in sorted(os.listdir(skills)):
            candidates.append(os.path.join(skills, name, "api", "resources.json"))
    for c in candidates:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return None


def load_resources(path):
    """A set of relative paths under sightlab_resources/, from resources.json or a plain list file."""
    with open(path, "r", encoding="utf-8-sig") as fh:
        text = fh.read()
    if path.lower().endswith(".json"):
        data = json.loads(text)
        return {p.replace("\\", "/") for p in data.get("all", [])}
    return {line.strip().replace("\\", "/") for line in text.splitlines() if line.strip()}


TEXT_KWARGS = ("startTrialText", "startExperimentText", "endTrialText", "endExperimentText", "message")


def check_script(path, api, resources=None):
    """Check one script. Returns {'errors': [...], 'warnings': [...], 'frame': {...}, 'instances': {...}}."""
    errors, warnings = [], []
    frame = {"gui": None, "sets_trial_count": False, "schedules_run_experiment": False,
             "waits_experiment_start": False, "waits_before_start": None, "start_end_pairs": 0}
    report = {"script": str(path), "errors": errors, "warnings": warnings, "frame": frame, "instances": {}}

    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        source = fh.read()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        errors.append({"code": "E_SYNTAX", "line": e.lineno or 0, "message": str(e)})
        return report

    table = _class_table(api)

    # 1. Aliases of the sightlab module (dotted, so a bare `import sightlab_utils.sightlab` works).
    module_aliases = set()
    imports_sightlab_utils = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("sightlab_utils"):
                    imports_sightlab_utils = True
                if a.name == "sightlab_utils.sightlab":
                    module_aliases.add(a.asname or "sightlab_utils.sightlab")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("sightlab_utils"):
                imports_sightlab_utils = True
            if node.module == "sightlab_utils":
                for a in node.names:
                    if a.name == "sightlab":
                        module_aliases.add(a.asname or "sightlab")
            elif node.module == "sightlab_utils.sightlab":
                for a in node.names:
                    if a.name in SIGHTLAB_CLASSES:
                        module_aliases.add("<direct>:" + (a.asname or a.name))

    def ctor_class(call):
        fn = call.func
        if isinstance(fn, ast.Attribute) and _dotted(fn.value) in module_aliases and fn.attr in SIGHTLAB_CLASSES:
            return fn.attr
        if isinstance(fn, ast.Name) and ("<direct>:" + fn.id) in module_aliases:
            return fn.id
        return None

    # 2. Instances: name = alias.SightLab(...), including `self.sightlab = ...`
    instances = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            cname = ctor_class(node.value)
            if cname is None:
                continue
            for t in node.targets:
                name = _dotted(t)
                if name:
                    instances[name] = cname
            for kw in node.value.keywords:
                if kw.arg == "gui" and isinstance(kw.value, ast.Constant):
                    frame["gui"] = bool(kw.value.value)
            allowed = table.get(cname, {}).get("init")
            if allowed is not None:
                for kw in node.value.keywords:
                    if kw.arg is not None and kw.arg not in allowed:
                        errors.append(_finding("E_UNKNOWN_KWARG", kw, "%s() has no argument '%s'" % (cname, kw.arg)))
    report["instances"] = instances

    # 3. Method calls on instances, the frame, and the warnings' evidence.
    start_calls = end_calls = 0
    gaze_true = False
    loops_over_trial_count = False
    first_start_line = None
    first_wait_line = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Yield) and isinstance(node.value, ast.Call):
            yfn = node.value.func
            if isinstance(yfn, ast.Attribute) and _name_of(yfn.value) == "viztask" and yfn.attr.startswith("wait"):
                if first_wait_line is None or node.lineno < first_wait_line:
                    first_wait_line = node.lineno
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == "range" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "getTrialCount" and _dotted(arg.func.value) in instances:
                    loops_over_trial_count = True
            if isinstance(fn, ast.Attribute):
                owner = _dotted(fn.value)
                if owner in instances:
                    cname = instances[owner]
                    methods = table.get(cname, {}).get("methods", {})
                    if fn.attr not in methods:
                        errors.append(_finding("E_UNKNOWN_METHOD", node, "%s has no method '%s'" % (cname, fn.attr)))
                    else:
                        allowed = methods[fn.attr]
                        if allowed is not None:
                            for kw in node.keywords:
                                if kw.arg is not None and kw.arg not in allowed:
                                    errors.append(_finding("E_UNKNOWN_KWARG", kw, "%s.%s() has no argument '%s'" % (cname, fn.attr, kw.arg)))
                        if fn.attr in ("startTrial", "endTrial", "showInstructions"):
                            kwargs = {k.arg: k.value for k in node.keywords if k.arg}
                            if "textContinueKey" in kwargs:
                                texts = [kwargs[k] for k in TEXT_KWARGS if k in kwargs]
                                if fn.attr == "showInstructions" and node.args:
                                    texts.append(node.args[0])
                                for tnode in texts:
                                    if isinstance(tnode, ast.Constant) and isinstance(tnode.value, str) and "trigger" in tnode.value.lower():
                                        warnings.append(_finding("W_KEY_REPLACES_TRIGGER", node, "%s(): textContinueKey replaces the trigger wait, but the text says to press the trigger; a headset participant cannot continue" % fn.attr))
                                        break
                        if fn.attr == "setTrialCount":
                            frame["sets_trial_count"] = True
                        elif fn.attr == "startTrial":
                            start_calls += 1
                            if first_start_line is None or node.lineno < first_start_line:
                                first_start_line = node.lineno
                        elif fn.attr == "endTrial":
                            end_calls += 1
                        elif fn.attr == "addSceneObject":
                            for kw in node.keywords:
                                if kw.arg == "gaze" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                    gaze_true = True
                elif owner == "viz" and fn.attr == "go":
                    warnings.append(_finding("W_VIZ_GO", node, "viz.go() is not needed; SightLab starts Vizard itself"))
                elif owner == "viztask" and fn.attr == "schedule":
                    for arg in node.args:
                        # Both forms work in Vizard: schedule(sightlab.runExperiment) and
                        # schedule(sightlab.runExperiment()) (the shipped STIM example uses the latter).
                        target = arg.func if isinstance(arg, ast.Call) else arg
                        if isinstance(target, ast.Attribute) and _dotted(target.value) in instances and target.attr == "runExperiment":
                            frame["schedules_run_experiment"] = True
                elif owner == "viztask" and fn.attr == "waitEvent":
                    if node.args and _name_of(node.args[0]) == "EXPERIMENT_START":
                        frame["waits_experiment_start"] = True
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and RESOURCE_PREFIX in node.value.replace("\\", "/"):
            if resources is not None:
                rel = node.value.replace("\\", "/").split(RESOURCE_PREFIX, 1)[1]
                # A folder or a prefix the script completes at run time ('.../objects/' + name) is not a file.
                is_file = bool(rel) and not rel.endswith("/") and "." in rel.rsplit("/", 1)[-1]
                if is_file and rel not in resources:
                    same_case = [r for r in resources if r.lower() == rel.lower()]
                    if same_case:
                        warnings.append(_finding("W_UNKNOWN_ENVIRONMENT", node, "'%s' is spelled '%s' in the shipped resources; use that spelling so the GUI list and any case-sensitive file system agree" % (rel, same_case[0])))
                    else:
                        warnings.append(_finding("W_UNKNOWN_ENVIRONMENT", node, "'%s' is not in sightlab_resources" % rel))

    frame["start_end_pairs"] = min(start_calls, end_calls)
    if first_start_line is not None:
        frame["waits_before_start"] = first_wait_line is not None and first_wait_line < first_start_line
    if not instances and imports_sightlab_utils:
        warnings.append({"code": "W_NO_INSTANCE", "line": 0, "message": "sightlab_utils is imported but no SightLab instance was found; nothing was checked (a helper module, or a construction this checker cannot follow)"})
    if instances:
        if not frame["schedules_run_experiment"]:
            errors.append({"code": "E_NO_RUN_EXPERIMENT", "line": 0, "message": "viztask.schedule(sightlab.runExperiment) is missing"})
        if frame["waits_before_start"] is False:
            warnings.append({"code": "W_START_TRIAL_IMMEDIATE", "line": first_start_line, "message": "startTrial is called before any viztask wait; wait on EXPERIMENT_START or a key first"})
        if frame["gui"] is False and loops_over_trial_count and not frame["sets_trial_count"]:
            warnings.append({"code": "W_NO_TRIAL_COUNT", "line": 0, "message": "gui=False and a getTrialCount() loop without setTrialCount(): the loop runs once"})
        if frame["gui"] is False and not gaze_true:
            warnings.append({"code": "W_NO_GAZE_OBJECT", "line": 0, "message": "no addSceneObject(..., gaze=True): no gaze data on objects will be recorded"})
        if start_calls != end_calls:
            warnings.append({"code": "W_UNPAIRED_TRIAL", "line": 0, "message": "startTrial called %d times, endTrial %d times" % (start_calls, end_calls)})
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description="Static checks for a SightLab 2.x experiment script.")
    p.add_argument("script")
    p.add_argument("--api", default=None, help="sightlab-api.json (default: beside this file, ../api/, or the project's .claude/skills/*/api/)")
    p.add_argument("--sightlab-utils", default=None, help="installed package dir; builds the API map from it")
    p.add_argument("--resources", default=None, help="resources.json or a plain list of names under sightlab_resources/ (default: beside this file, ../api/, harness/, or .claude/skills/*/api/)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)

    if a.sightlab_utils:
        api = build_api_from_package(a.sightlab_utils)
        api_source = os.path.abspath(a.sightlab_utils)
    else:
        api_path = a.api or default_api_path()
        if not api_path or not os.path.isfile(api_path):
            print("no API map found: pass --api <sightlab-api.json> or --sightlab-utils <installed package dir>", file=sys.stderr)
            return 2
        api = load_api(api_path)
        api_source = os.path.abspath(api_path)
    resources = None
    res_path = a.resources or default_resources_path()
    if res_path and os.path.isfile(res_path):
        resources = load_resources(res_path)

    report = check_script(a.script, api, resources)
    report["api_source"] = api_source
    report["sightlab_utils_version"] = api.get("sightlab_utils_version")
    if a.json:
        print(json.dumps(report, indent=1))
    else:
        for f in report["errors"] + report["warnings"]:
            where = " line %d" % f["line"] if f["line"] else ""
            print("%s%s: %s" % (f["code"], where, f["message"]))
        inst = ", ".join("%s (%s)" % (k, v) for k, v in report["instances"].items()) or "none"
        print("instances: %s" % inst)
        print("%s: %d error(s), %d warning(s); frame %s" % (os.path.basename(a.script), len(report["errors"]), len(report["warnings"]), json.dumps(report["frame"])))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
