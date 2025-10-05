from app.db.base import Base  # noqa: F401  (re-export Base for Alembic's target_metadata)

# Ensure model modules are imported so that Alembic can discover them
# via Base.metadata
from app.models import user  # noqa: F401
from app.models import ticker  # noqa: F401
from app.models import headline  # noqa: F401
from app.models import mention  # noqa: F401
from app.models import risk_score  # noqa: F401

# Also export names for convenience
from app.models.user import User  # noqa: F401
from app.models.ticker import Ticker  # noqa: F401
from app.models.headline import Headline  # noqa: F401
from app.models.mention import Mention  # noqa: F401
from app.models.risk_score import RiskScore  # noqa: F401


