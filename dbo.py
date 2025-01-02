from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine


sql_string = "sqlite:///checkins.db"
engine = create_engine(sql_string)


class Base(DeclarativeBase):
    pass

