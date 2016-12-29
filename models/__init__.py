from models.base import Base
from models.user import User
from models.user_settings import UserSettings

create_order = (
    User.__table__,
    UserSettings.__table__
)

drop_order = (
    UserSettings.__table__,
    User.__table__
)
