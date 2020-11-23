from pony.orm import Database, Required, Json
from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """State user into scenario"""
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class RegistrationDB(db.Entity):
    """Request to registration"""
    name = Required(str)
    email = Required(str)


db.generate_mapping(create_tables=True)
