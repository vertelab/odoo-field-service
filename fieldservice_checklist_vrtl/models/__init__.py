# Filen heter fieldservice_checklist.py, inte fieldservice_checklist_vrtl.py.
# Fel namn -> ModuleNotFoundError -> 'Couldn't load module
# fieldservice_checklist_vrtl' -> Failed to initialize database.
# Fixad 2026-11-10 (lantteknik).
from . import fieldservice_checklist
from . import fieldservice_order
