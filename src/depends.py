from fastapi import Depends
from auth.users import fastapi_users

current_user = fastapi_users.current_user()

optional_current_user = fastapi_users.current_user(optional=True)

current_active_user = fastapi_users.current_user(active=True)
