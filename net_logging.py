import logging
from dbo import Base, engine
from typing import Optional
from sqlalchemy.orm import Mapped, Session
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, DateTime
from datetime import datetime


# TODO: one option is to log to disk and periodically batch insert to DB: https://stackoverflow.com/a/290340/6288413
# TODO: log to database: https://stackoverflow.com/questions/2314307/python-logging-to-database


class DatabaseLog(Base):
    __tablename__ = "logging"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )  # [id] [bigint] IDENTITY(1,1) NOT NULL,
    log_level: Mapped[int] = mapped_column()  # [log_level] [int] NULL,
    log_levelname: Mapped[str] = mapped_column(
        String(32)
    )  # [log_levelname] [char](32) NULL,
    log: Mapped[str] = mapped_column(String)  # [log] [char](2048) NOT NULL,
    created_at: Mapped[datetime] = mapped_column(
        DateTime
    )  # [created_at] [datetime2](7) NOT NULL,
    created_by: Mapped[str] = mapped_column(
        String(1024)
    )  # [created_by] [char](32) NOT NULL,
    execution_info: Mapped[Optional[str]] = mapped_column(String)
    execution_text: Mapped[Optional[str]] = mapped_column(String)
    function_name: Mapped[str] = mapped_column(String(1024))
    file_name: Mapped[str] = mapped_column(String(4092))

    def __init__(self, **kw):
        # TODO: handle cases where keyword arguments are null

        # Set current time
        self.created_at = datetime.fromtimestamp(kw.get("created_at"))

        # Set log level
        self.log_level = kw.get("log_level_no")
        self.log_levelname = kw.get("log_level_name")
        # Set log message
        log_message = kw.get("log_message")
        self.log = log_message.strip()
        # Other columns
        self.created_by = kw.get("created_by")
        exc_info = kw.get("execution_info")
        if isinstance(exc_info, tuple):
            exc_info = "\n".join([str(x) for x in exc_info])
        self.execution_info = exc_info
        self.execution_text = kw.get("execution_text")
        self.function_name = kw.get("function_name")
        self.file_name = kw.get("file_name")


class LogDBHandler(logging.Handler):
    """
    Customized logging handler that puts logs to the database.
    """

    def __init__(self, sql_string: str):
        logging.Handler.__init__(self)
        self.sql_conn_string = sql_string

    def emit(self, record: logging.LogRecord):
        # TODO: create separate engine using sql_string
        with Session(engine) as session:
            try:
                db_log = DatabaseLog(
                    log_level_no=record.levelno,
                    log_level_name=record.levelname,
                    log_message=record.msg,
                    created_at=record.created,
                    created_by=record.name,
                    execution_info=record.exc_info,
                    execution_text=record.exc_text,
                    function_name=record.funcName,
                    file_name=record.filename,
                )
                session.add(db_log)
                session.commit()
            except Exception as e:
                print(str(e))
