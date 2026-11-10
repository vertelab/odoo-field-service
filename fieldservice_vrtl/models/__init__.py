from . import fieldserviceorder
from . import fieldservice_order_line
from . import fieldservice_stage
from . import fieldservice_stakeholder
from . import fieldservice_order_type
from . import ir_config
from . import fieldservice_order_tag
from . import product_template
# fieldservice_team.py definierar fieldservice.team, som security/ir.model.access.csv
# refererar som model_fieldservice_team. Utan importen skapas aldrig xmlid:t,
# och installationen faller med:
#   null value in column "model_id" of relation "ir_model_access"
# Fixad 2026-11-10 (lantteknik).
from . import fieldservice_team
