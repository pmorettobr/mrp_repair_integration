from . import mrp_production    # ✅ PRIMEIRO: define repair_order_id
from . import repair_order      # ✅ DEPOIS: usa inverse_name='repair_order_id'
from . import mrp_workorder     # ✅ Independente
