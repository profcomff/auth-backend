from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
from settings import Settings

settings = Settings()


def connect():
    engine = create_engine(f"{settings.DB_DSN}", echo=True)
    meta = MetaData(engine)
    ## exec(open("users.py").read())
    users_table = Table("users", meta, autoload=True)
    tokens_table = Table("tokens", meta, autoload=True)
    try:
        engine.connect()
        print('Connection successful')
    except SQLAlchemyError as e:
        print(f"The error '{e}' occurred")
    ## return tablepython, engine
    return engine, users_table, tokens_table


engine, users_table, tokens_table = connect()

