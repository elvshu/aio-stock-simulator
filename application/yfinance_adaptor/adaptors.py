import abc

import pandas as pd
from django.conf import settings
from sqlalchemy import create_engine


class Adaptor(abc.ABC):
    @abc.abstractmethod
    def export(self, table_name: str, df: pd.DataFrame) -> None:
        ...


class PostGresDjangoAdaptor(Adaptor):
    @classmethod
    def from_django_settings(cls) -> "PostGresDjangoAdaptor":
        return cls(
            user_name=settings.DATABASES["default"]["USER"],
            password=settings.DATABASES["default"]["PASSWORD"],
            db_name=settings.DATABASES["default"]["NAME"],
            host=settings.DATABASES["default"]["HOST"],
            port=settings.DATABASES["default"]["PORT"],
        )

    def __init__(
        self,
        user_name: str,
        password: str,
        db_name: str,
        host: str = "localhost",
        port: str = "5432",
    ) -> None:
        self.engine = create_engine(
            f"postgresql+psycopg2://{user_name}:{password}@{host}:{port}/{db_name}"
        )

    def read_table_schema(self, table_name: str) -> pd.DataFrame:
        query = (
            "select table_name, column_name, data_type from "
            f" information_schema.columns where table_name='{table_name}'"
        )
        return pd.read_sql(query, self.engine)

    def export(self, table_name: str, df: pd.DataFrame) -> None:
        df.to_sql(table_name, self.engine, if_exists="append", index=False)
