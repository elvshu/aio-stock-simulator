from __future__ import annotations

import datetime
import urllib.parse as urlparse

import pandas
import pydantic as p
import yfinance as yf

from django.db.models import Model

from . import adaptors, enums


def get_database_ready_df(df: pandas.DataFrame, ticker: str) -> pandas.DataFrame:
    company_id = ticker.replace(".AX", "")
    mapper = {
        "Adj Close": "adj_close",
        "High": "high",
        "Low": "low",
        "Open": "open",
        "Close": "close",
        "Volume": "volume",
    }
    replacement_columns = ["timestamp"] + [
        mapper[column] for column in df.columns.get_level_values(0)
    ]
    if isinstance(df.index, pandas.Index):
        df.index = pandas.DatetimeIndex(df.index)
    df.index = df.index.tz_localize("Australia/Melbourne")
    df.reset_index(inplace=True)
    df.columns = replacement_columns
    company_id_column = [company_id for _ in range(len(df))]
    df["company_id"] = company_id_column
    # if any of the open/close/high/low/volume is nan
    # then the data is useless
    df = df[df.open.notnull()]
    df = df[df.close.notnull()]
    df = df[df.high.notnull()]
    df = df[df.low.notnull()]
    df = df[df.volume.notnull()]
    # fix adj_close
    adj_close = df["adj_close"]
    adj_close = adj_close.where(
        adj_close.notnull(), df["close"]  # replace nan adj_close with close
    )
    # replace ridiculous values (extreme small or extreme large)
    # with close
    adj_close = adj_close.where(
        adj_close >= 0.001,
        df["close"],
    )
    adj_close = adj_close.where(
        adj_close < df["close"] * 20,
        df["close"],
    )
    df["adj_close"] = adj_close
    return df


def handle_yf_dataframes(
    df: pandas.DataFrame, tickers: list[str]
) -> list[pandas.DataFrame]:
    if not isinstance(df.columns, pandas.MultiIndex) and len(tickers) == 1:
        return [get_database_ready_df(df, tickers[0])]

    columns_by_tickers = {}
    for name, ticker in df.columns:
        columns_by_tickers.setdefault(ticker, []).append((name, ticker))

    dfs = []
    for ticker, column_names in columns_by_tickers.items():
        dfs.append(get_database_ready_df(df.filter(column_names, axis=1), ticker))
    return dfs


class YahooFinanceDownloadSpec(p.BaseModel):
    tickers: str | list[str]
    start: str | datetime.datetime = "1900-01-01"
    end: str | datetime.datetime = datetime.datetime.now()
    actions: bool = False
    threads: bool = True
    ignore_tz: bool = True
    group_by: enums.GroupBy = enums.GroupBy.COLUMN
    auto_adjust: bool = False
    back_adjust: bool = False
    repair: bool = False
    keepna: bool = False
    progress: bool = True
    period: enums.Period = enums.Period.MAX
    show_errors: bool = True
    interval: enums.Interval = enums.Interval.ONE_DAY
    prepost: bool = False
    proxy: str | None = None
    rounding: bool = False
    timeout: float | None = None

    @p.field_validator("start", "end")
    @classmethod
    def validate_datetime(cls, value) -> str | None:
        if value:
            if isinstance(value, str):
                _ = datetime.datetime.fromisoformat(value)
            elif isinstance(value, datetime.datetime):
                pass
            else:
                raise ValueError(
                    f"Invalid type for field start/end {value}, "
                    "expect iso format str or datetime obj"
                )
        return value

    @p.field_validator("proxy")
    @classmethod
    def validate_proxy(cls, value) -> str | None:
        """Optional. Proxy server URL scheme. Default is None"""
        if value:
            if bool(urlparse.urlparse(value).scheme):
                return value
            raise ValueError(f"Invalid url scheme: {value}")
        return value

    def serialize(self) -> dict:
        data = super().model_dump()
        data["group_by"] = data["group_by"].value
        data["period"] = data["period"].value
        data["interval"] = data["interval"].value
        return data


class YFDownloader(object):
    def __init__(
        self,
        tickers: str | list[str],
        adaptor: adaptors.Adaptor | None = None,
        **kwargs,
    ) -> None:
        self.adaptor = adaptor
        self.spec = YahooFinanceDownloadSpec(tickers=tickers, **kwargs)
        self._downloaded: list[pandas.DataFrame] | None = None

    @property
    def tickers(self) -> list[str]:
        return (
            self.spec.tickers
            if isinstance(self.spec.tickers, list)
            else [self.spec.tickers]
        )

    def download(self) -> pandas.DataFrame:
        return yf.download(**self.spec.serialize())

    def get_dfs(self) -> list[pandas.DataFrame]:
        if self._downloaded is None:
            self._downloaded = self.download()
        return handle_yf_dataframes(self._downloaded, self.tickers)

    def export(self, django_model: Model) -> None:
        # table_has_inited = django_model.objects.exists()
        objects = []
        for df in self.get_dfs():
            company_ids = df["company_id"].unique().tolist()
            if not len(company_ids):
                continue
            # print(company_ids)
            pending_records = []
            for record in df.to_dict(orient="records"):
                pending_records.append(django_model(**record))
            if pending_records:
                django_model.objects.bulk_create(pending_records, batch_size=10000)
