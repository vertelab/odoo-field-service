#!/usr/bin/env bash
# sanity-check.sh — statisk grind för odoo-field-service.
#
# Tre kontroller, alla utan Odoo-runtime:
#   1. py_compile på varje .py (syntax)
#   2. XML-parse på varje fil som nämns i en __manifest__.py data/demo-nyckel
#   3. AST: varje compute="..." på ett fields.*-anrop måste ha en def med
#      exakt det namnet i samma modul
#   4. Cron: varje ir.cron vars code är model.<metod>() måste ha en def
#      <metod> på cronens målmodell
#   5. cron.task: model_name måste vara en modell repot definierar och
#      method_name en def på den modellen
#
# Avsiktligt utanför grinden (se design D9): .p.py synkas inte — Odoo laddar
# .py. Döda filer som inte nämns i manifestet kontrolleras därför inte heller.
#
# Användning:  bash scripts/sanity-check.sh [-v]
# Exit: 0 = allt grönt, 1 = minst ett fel.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
ROOT="$PWD"
VERBOSE=${1:-}
ERRORS=0
declare -a FAIL

fail() { FAIL+=("$1"); ERRORS=$((ERRORS + 1)); }

# ---------------------------------------------------------------- 1. syntax
PY_COUNT=0
while IFS= read -r f; do
    PY_COUNT=$((PY_COUNT + 1))
    if ! python3 -c "
import py_compile, sys, tempfile, os
try:
    fd, tmp = tempfile.mkstemp(suffix='.pyc')
    os.close(fd)
    py_compile.compile(sys.argv[1], doraise=True, cfile=tmp)
    os.unlink(tmp)
except py_compile.PyCompileError as e:
    print(str(e).strip().splitlines()[0])
    sys.exit(1)
" "$f" 2>/dev/null; then
        fail "SYNTAX  $f"
    fi
done < <(find . -name '*.py' -not -path './.git/*' | sort)

# ---------------------------------------------------------------- 2. XML
XML_COUNT=0
while IFS= read -r f; do
    XML_COUNT=$((XML_COUNT + 1))
    if ! python3 -c "
import sys, xml.dom.minidom as m
try:
    m.parse(sys.argv[1])
except Exception as e:
    print(str(e)[:120])
    sys.exit(1)
" "$f" 2>/dev/null; then
        fail "XML     $f"
    fi
done < <(python3 - <<'PYEOF'
import ast, glob, os
seen = []
for mf in sorted(glob.glob('*/__manifest__.py')):
    mod = os.path.dirname(mf)
    try:
        t = ast.literal_eval(open(mf).read())
    except Exception:
        continue
    for key in ('data', 'demo'):
        for rel in (t.get(key) or []):
            p = os.path.join(mod, rel)
            if os.path.isfile(p) and p.endswith('.xml'):
                seen.append(p)
print('\n'.join(sorted(set(seen))))
PYEOF
)

# ---------------------------------------------------------------- 3. compute
COMPUTE_COUNT=0
COMPUTE_OUT=$(python3 - <<'PYEOF'
import ast, glob, os, collections

def module_files(mod):
    return [f for f in glob.glob(os.path.join(mod, '**', '*.py'), recursive=True)
            if not f.endswith('.p.py')]

def collect_methods(mod):
    """model name -> set of method names, plus a global set (for unbound defs)."""
    per_model = collections.defaultdict(set)
    globals_ = set()
    for f in module_files(mod):
        try:
            tree = ast.parse(open(f).read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                model = None
                for stmt in node.body:
                    if (isinstance(stmt, ast.Assign)
                            and any(getattr(t, 'id', '') == '_name' for t in stmt.targets)
                            and isinstance(stmt.value, ast.Constant)):
                        model = stmt.value.value
                for stmt in node.body:
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        globals_.add(stmt.name)
                        if model:
                            per_model[model].add(stmt.name)
    return per_model, globals_

def field_computes(mod):
    """yield (file, lineno, field_name, compute_name)"""
    for f in module_files(mod):
        try:
            tree = ast.parse(open(f).read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, ast.Attribute) and getattr(fn.value, 'id', '') == 'fields'):
                continue
            field_name = None
            for kw in node.keywords:
                if kw.arg == 'compute' and isinstance(kw.value, ast.Constant):
                    field_name = kw.value.value
            if field_name is None:
                continue
            target = None
            for kw in node.keywords:
                if kw.arg == 'string' and isinstance(kw.value, ast.Constant):
                    target = kw.value.value
            yield f, node.lineno, target or fn.attr, field_name

bad = []
count = 0
for mod in sorted(d for d in os.listdir('.') if os.path.isdir(d) and os.path.exists(os.path.join(d, '__manifest__.py'))):
    per_model, globals_ = collect_methods(mod)
    all_methods = set(globals_)
    for m in per_model.values():
        all_methods |= m
    for f, lineno, field, compute in field_computes(mod):
        count += 1
        if compute not in all_methods:
            bad.append(f"{f}:{lineno}: field {field!r} -> compute={compute!r} (no such method)")
print(f"__COUNT__{count}")
for b in bad:
    print(b)
PYEOF
)
COMPUTE_COUNT=$(printf '%s\n' "$COMPUTE_OUT" | sed -n 's/^__COUNT__//p')
while IFS= read -r line; do
    [ -n "$line" ] && fail "COMPUTE $line"
done < <(printf '%s\n' "$COMPUTE_OUT" | grep -v '^__COUNT__' | grep -v '^$')

# ---------------------------------------------------------------- 4. cron
CRON_COUNT=0
CRON_OUT=$(python3 - <<'PYEOF'
import ast, glob, os, re, collections

def module_files(mod):
    return [f for f in glob.glob(os.path.join(mod, '**', '*.py'), recursive=True)
            if not f.endswith('.p.py')]

def collect_methods(mod):
    per_model = collections.defaultdict(set)
    for f in module_files(mod):
        try:
            tree = ast.parse(open(f).read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            model = None
            for stmt in node.body:
                if (isinstance(stmt, ast.Assign)
                        and any(getattr(t, 'id', '') == '_name' for t in stmt.targets)
                        and isinstance(stmt.value, ast.Constant)):
                    model = stmt.value.value
            if model is None:
                # _inherit-only extension of a model defined elsewhere.
                for stmt in node.body:
                    if (isinstance(stmt, ast.Assign)
                            and any(getattr(t, 'id', '') == '_inherit' for t in stmt.targets)):
                        if isinstance(stmt.value, ast.Constant):
                            model = stmt.value.value
                        elif isinstance(stmt.value, ast.List) and stmt.value.elts:
                            first = stmt.value.elts[0]
                            if isinstance(first, ast.Constant):
                                model = first.value
                if model is None:
                    continue
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    per_model[model].add(stmt.name)
    return per_model

# xmlid -> model for ir.model records declared in the repo
def model_xmlids(mod):
    out = {}
    for f in glob.glob(os.path.join(mod, '**', '*.xml'), recursive=True):
        try:
            src = open(f).read()
        except Exception:
            continue
        for m in re.finditer(r'<record[^>]*id="([^"]+)"[^>]*model="ir\.model"(.{0,400}?)</record>', src, re.S):
            rid, body = m.group(1), m.group(2)
            fm = re.search(r'<field name="model">([^<]+)</field>', body)
            if fm:
                out[rid] = fm.group(1)
    return out

# All models defined anywhere in the repo, so a cron may target a model that
# another module in the same repo defines.
repo_models = collections.defaultdict(set)
for mod in sorted(d for d in os.listdir('.') if os.path.isdir(d) and os.path.exists(os.path.join(d, '__manifest__.py'))):
    for model, methods in collect_methods(mod).items():
        repo_models[model] |= methods

bad = []
count = 0
for mod in sorted(d for d in os.listdir('.') if os.path.isdir(d) and os.path.exists(os.path.join(d, '__manifest__.py'))):
    per_model = collect_methods(mod)
    xm = model_xmlids(mod)
    for f in glob.glob(os.path.join(mod, '**', '*.xml'), recursive=True):
        try:
            src = open(f).read()
        except Exception:
            continue
        for m in re.finditer(r'<record[^>]*model="ir\.cron"[^>]*>(.*?)</record>', src, re.S):
            body = m.group(1)
            ref = re.search(r'<field name="model_id"[^>]*ref="([^"]+)"', body)
            code = re.search(r'<field name="code">(.*?)</field>', body, re.S)
            if not (ref and code):
                continue
            count += 1
            model = xm.get(ref.group(1))
            if model is None and ref.group(1).startswith('model_'):
                # Odoo's convention: ir.model xmlid model_<name with _ for .>
                candidate = ref.group(1)[len('model_'):]
                for name in repo_models:
                    if name.replace('.', '_') == candidate:
                        model = name
                        break
            calls = re.findall(r'\bmodel\.([A-Za-z_][A-Za-z0-9_]*)\(', code.group(1))
            if not calls:
                continue
            if model is None:
                # Model comes from a dependency outside this repo: only the
                # methods the repo itself adds to that model are verifiable.
                known = set()
                for name, methods in per_model.items():
                    if name.replace('.', '_') == ref.group(1)[len('model_'):]:
                        known = methods
                for call in calls:
                    if call not in known:
                        bad.append(f"{f}: cron on external model {ref.group(1)!r} calls model.{call}() -> not defined in this repo")
                continue
            known = repo_models.get(model, set())
            for call in calls:
                if call not in known:
                    bad.append(f"{f}: cron on {model} calls model.{call}() -> no such method")
print(f"__COUNT__{count}")
for b in bad:
    print(b)
PYEOF
)
CRON_COUNT=$(printf '%s\n' "$CRON_OUT" | sed -n 's/^__COUNT__//p')
while IFS= read -r line; do
    [ -n "$line" ] && fail "CRON    $line"
done < <(printf '%s\n' "$CRON_OUT" | grep -v '^__COUNT__' | grep -v '^$')

# ---------------------------------------------------------------- 5. cron.task
TASK_COUNT=0
TASK_OUT=$(python3 - <<'PYEOF'
import ast, glob, os, re, collections

def module_files(mod):
    return [f for f in glob.glob(os.path.join(mod, '**', '*.py'), recursive=True)
            if not f.endswith('.p.py')]

def collect_methods(mod):
    per_model = collections.defaultdict(set)
    for f in module_files(mod):
        try:
            tree = ast.parse(open(f).read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            model = None
            for stmt in node.body:
                if (isinstance(stmt, ast.Assign)
                        and any(getattr(t, 'id', '') == '_name' for t in stmt.targets)
                        and isinstance(stmt.value, ast.Constant)):
                    model = stmt.value.value
            if model is None:
                for stmt in node.body:
                    if (isinstance(stmt, ast.Assign)
                            and any(getattr(t, 'id', '') == '_inherit' for t in stmt.targets)):
                        if isinstance(stmt.value, ast.Constant):
                            model = stmt.value.value
                        elif isinstance(stmt.value, ast.List) and stmt.value.elts:
                            first = stmt.value.elts[0]
                            if isinstance(first, ast.Constant):
                                model = first.value
            if model is None:
                continue
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    per_model[model].add(stmt.name)
    return per_model

def manifest_depends(mod):
    mf = os.path.join(mod, '__manifest__.py')
    try:
        return set(ast.literal_eval(open(mf).read()).get('depends') or [])
    except Exception:
        return set()

repo_models = collections.defaultdict(set)
mod_models = {}
mod_methods = {}
for mod in sorted(d for d in os.listdir('.') if os.path.isdir(d) and os.path.exists(os.path.join(d, '__manifest__.py'))):
    methods = collect_methods(mod)
    mod_methods[mod] = methods
    mod_models[mod] = set(methods)
    for model, ms in methods.items():
        repo_models[model] |= ms

bad = []
count = 0
for mod in sorted(mod_models):
    deps = manifest_depends(mod)
    for f in glob.glob(os.path.join(mod, '**', '*.xml'), recursive=True):
        try:
            src = open(f).read()
        except Exception:
            continue
        for m in re.finditer(r'<record[^>]*model="cron\.task"[^>]*>(.*?)</record>', src, re.S):
            body = m.group(1)
            count += 1
            def field(name):
                fm = re.search(r'<field name="%s">([^<]*)</field>' % name, body)
                return fm.group(1).strip() if fm else None
            model_name = field('model_name')
            method_name = field('method_name')
            tech = field('technical_name') or '?'
            if not model_name or not method_name:
                bad.append("%s: cron.task %r is missing model_name or method_name" % (f, tech))
                continue
            known = repo_models.get(model_name)
            if known is None:
                if not deps:
                    bad.append("%s: cron.task %r targets %r which this repo does not define and the module declares no depends" % (f, tech, model_name))
                else:
                    bad.append("%s: cron.task %r targets %r from an external dependency - method %r not verifiable here" % (f, tech, model_name, method_name))
                continue
            if method_name not in known:
                bad.append("%s: cron.task %r calls %s.%s() -> no such method" % (f, tech, model_name, method_name))
print("__COUNT__%d" % count)
for b in bad:
    print(b)
PYEOF
)
TASK_COUNT=$(printf '%s\n' "$TASK_OUT" | sed -n 's/^__COUNT__//p')
while IFS= read -r line; do
    [ -n "$line" ] && fail "CRONTASK $line"
done < <(printf '%s\n' "$TASK_OUT" | grep -v '^__COUNT__' | grep -v '^$')

# ---------------------------------------------------------------- rapport
echo "sanity-check: $PY_COUNT py, $XML_COUNT xml, $COMPUTE_COUNT computes, $CRON_COUNT ir.cron, $TASK_COUNT cron.task"
if [ "$ERRORS" -eq 0 ]; then
    echo "OK — inga fel."
    exit 0
fi
echo ""
echo "$ERRORS fel:"
for f in "${FAIL[@]}"; do echo "  - $f"; done
exit 1
