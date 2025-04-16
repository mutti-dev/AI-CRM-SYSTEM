from .email_views import *
from .whatsapp_views import *
from .task_views import *
from .dashboard_views import dashboard_data
from .customer_views import fetch_customers, create_customer
from .agent_views import (
    fetch_agents,
    fetch_teams,
    upload_fine_tuned_dataset
)

import logging
logger = logging.getLogger(__name__)
