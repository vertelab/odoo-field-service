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
# fieldservice_order_lifecycle.py definierar action_assign,
# action_schedule, action_start, action_complete och action_cancel —
# de metoder som views/fieldservice_order_views.xml binder knappar
# till. Utan importen saknas metoderna och vyn faller med:
#   action_assign is not a valid action on fieldservice.order
# Fixad 2026-11-10 (lantteknik).
from . import fieldservice_order_lifecycle
# ir_ui_menu.py definierar _hide_location_workers_menu, som
# data/ir_ui_menu_data.xml anropar via <function>. Utan importen
# faller installationen med ParseError pa den raden.
# Fixad 2026-11-10 (lantteknik).
from . import ir_ui_menu
