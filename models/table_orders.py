from models.user import User
from models.user_property import UserProperty

create_order = (
    User.__table__,
    UserProperty.__table__
)

drop_order = (
    UserProperty.__table__,
    User.__table__
)
