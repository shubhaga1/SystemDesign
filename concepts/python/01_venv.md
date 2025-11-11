# Python Virtual Environment (venv)

## What is a venv?

An isolated Python sandbox — its own Python binary + its own packages.
Each venv is completely independent of system Python and other venvs.

```
System Python (/usr/bin/python3)
  └── system packages (never touch)

.venv/   ← isolated sandbox
  └── its own Python binary
  └── its own pip
  └── its own packages (only what YOU installed here)
```

---

## Folder Structure

```
.venv/
├── pyvenv.cfg              ← config: Python version, where it came from
│
├── bin/                    ← added to PATH when you activate
│   ├── python              → symlink to python3.x
│   ├── python3             → symlink to python3.x
│   ├── pip                 → pip for THIS venv only
│   ├── activate            ← run this to activate (bash/zsh)
│   ├── activate.fish       ← for fish shell
│   ├── activate.csh        ← for csh shell
│   ├── Activate.ps1        ← for Windows PowerShell
│   └── <cli tools>         ← installed with packages (uvicorn, huggingface-cli...)
│
├── lib/
│   └── python3.x/
│       └── site-packages/  ← ALL installed packages live here
│           ├── cryptography/
│           ├── fastapi/
│           └── ...
│
└── include/                ← C headers (for packages with C extensions)
```

---

## Create, Activate, Use

```bash
# 1. Create a venv
python3 -m venv .venv              # creates .venv/ folder
python3 -m venv .venv --python=3.14  # specific Python version

# 2. Activate (must do this every new terminal session)
source .venv/bin/activate          # Mac/Linux (bash/zsh)
source .venv/bin/activate.fish     # fish shell
.venv\Scripts\activate             # Windows

# 3. Your prompt changes to show active venv:
# (.venv) shubhamgarg@MacBook %
#   ↑ venv name prefix = confirmation it's active

# 4. Install packages (goes into .venv/lib/.../site-packages/)
pip install cryptography
pip install fastapi uvicorn

# 5. Use Python
python3 script.py

# 6. Deactivate (go back to system Python)
deactivate
```

---

## How Activation Works

`source .venv/bin/activate` does ONE thing — prepends venv/bin to PATH:

```bash
# Before activation:
PATH = /usr/bin:/usr/local/bin:...
which python3  →  /usr/bin/python3

# After activation:
PATH = /Code/.venv/bin:/usr/bin:/usr/local/bin:...
which python3  →  /Code/.venv/bin/python3   ← venv wins!
```

Shell finds `.venv/bin/python3` FIRST because it's at the front of PATH.
This is why you can run scripts from ANY folder — activation is shell-level, not directory-level.

---

## How Python Finds Packages

```python
import cryptography
# Python looks in: .venv/lib/python3.9/site-packages/
# Finds cryptography/ folder → imports it
# Not found → ModuleNotFoundError
```

```bash
# ModuleNotFoundError means ONE of:
# 1. Package not installed in active venv → pip install <package>
# 2. Wrong venv active → deactivate, activate correct one
# 3. No venv active at all → source .venv/bin/activate
```

---

## Multiple venvs

```bash
# You can have multiple venvs:
.venv        # Python 3.9, ML packages (transformers, vllm, torch...)
.venv-1      # Python 3.9, duplicate
.venv-2      # Python 3.14, fresh

# Active venv shown in prompt:
(.venv)   → .venv is active
(.venv-2) → .venv-2 is active

# Each is independent:
# pip install in .venv → ONLY .venv has it
# .venv-2 stays empty
```

---

## .gitignore

ALWAYS add venv to `.gitignore` — never commit it:

```gitignore
.venv/
venv/
__pycache__/
*.pyc
*.pyo
```

Why: venv is huge (100MB+), machine-specific, regeneratable with `pip install -r requirements.txt`.

---

## Best Practices

```bash
# Save installed packages to requirements.txt
pip freeze > requirements.txt

# Recreate venv on another machine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```
One venv per project (ideal):
  project-A/.venv   ← project A's dependencies
  project-B/.venv   ← project B's (different versions, no conflicts)

Shared venv at root (acceptable for learning):
  Code/.venv        ← used across all subprojects
```

---

## Fernet vs AES-256-GCM

| | Fernet | AES-256-GCM |
|---|---|---|
| Key size | AES-128 | AES-256 |
| IV/Nonce | automatic | you manage |
| Authentication | HMAC-SHA256 | GCM built-in |
| API complexity | simple (2 lines) | more code |
| Output | base64 string | raw bytes |
| Use case | learning, internal tools | production |

Both require: `pip install cryptography`
