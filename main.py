
import sqlite3
import pandas as pd
from radio_operator import RadioOperator
import asyncio
import aioconsole
from sqlalchemy.orm import Session
from radio_operator import Base
from urllib3.exceptions import MaxRetryError
from requests.exceptions import ReadTimeout
import argparse
import logging
from dbo import engine, sql_string
import logging
from net_logging import LogDBHandler


def log_call_sign_orm(repeater: str, call_sign: str) -> None:
    with Session(engine) as session:
        try:
            operator = RadioOperator(call_sign, repeater)
            session.add(operator)
            session.commit()
        except ValueError as e:
            print(str(e))


def log_call_sign_pd(repeater: str, call_sign: str) -> None:
    with sqlite3.connect("checkins.db") as db:
        try:
            operator = RadioOperator(call_sign, repeater)
            user_info = operator.operator_info()
            user_df = pd.DataFrame(user_info, index=[0])
            user_df.to_sql("checkins", db, if_exists="append", index=False)
        except ValueError as e:
            print(str(e))
        except MaxRetryError as e:
            print(f"Max Retries Error: {str(e)}")
        except ConnectionError as e:
            print(f"ConnectionError: {str(e)}")
        except TimeoutError as e:
            print(f"TimeoutError: {str(e)}")
        except ReadTimeout as e:
            print(f"ReadTimeout: {str(e)}")

    print("task complete")


async def main(default_repeater: str = "VE7RVF", accept_default: bool = False):
    loop = asyncio.get_running_loop()
    if accept_default == True:
        repeater = default_repeater
    else:
        repeater = await aioconsole.ainput(f"Repeater (default: {default_repeater}): ")
    if not repeater or not repeater.strip():
        repeater = default_repeater
    print(f"Using repeater: {repeater}")
    while True:
        call_sign = await aioconsole.ainput("Callsign: ")
        call_sign = call_sign.strip().upper()
        if not call_sign:
            continue
        loop.run_in_executor(None, log_call_sign_orm, repeater, call_sign)


if __name__ == '__main__':
    # Program Expenses
    parser = argparse.ArgumentParser(
        prog='Net Control - Check-ins',
        description='Program that logs the check-ins.',
        epilog='This program looks up Canadian and American call signs automatically'
    )
    parser.add_argument(
        '-d', '--accept-defaults',
        help="Accept default(s) (e.g. VA7RVF repeater)",
        action=argparse.BooleanOptionalAction
    )
    parser.add_argument(
        '--debug',
        help="Enable debug mode",
        action=argparse.BooleanOptionalAction
    )
    args = parser.parse_args()

    # ORM
    Base.metadata.create_all(engine)
    
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    db_handler = LogDBHandler(sql_string)
    root_logger = logging.getLogger()
    root_logger.addHandler(db_handler)
    root_logger.setLevel(logging.INFO)
    root_logger.info("Logging enabled")
    # Set debug mode
    if args.debug:
        root_logger.setLevel(logging.DEBUG)
        root_logger.debug("Debug mode enabled")
    
    # Asyncio loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main_task = loop.create_task(main(accept_default=args.accept_defaults))
    try:
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        print("cancelled")
    except EOFError:
        print("cancelled during input")
    finally:
        pending_tasks = asyncio.all_tasks(loop=loop)
        for task in pending_tasks:
            task.cancel()
        loop.close()
