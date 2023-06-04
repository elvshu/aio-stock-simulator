import datetime
import itertools
from unittest import mock

import numpy as np
import pandas

from application.yfinance_adaptor import downloader


class TestDownloader:
    fields = ["Open", "Close", "High", "Low", "Adj Close", "Volume"]

    def _generate_columns(self, codes):
        if isinstance(codes, str):
            return self.fields
        elif isinstance(codes, list):
            if len(codes) > 1:
                return list(itertools.product(self.fields, codes))
        return self.fields

    def _generate_dataframe(self, values, start="1990-01-01", codes=None):
        columns = self._generate_columns(codes)
        index = [datetime.datetime.fromisoformat(start)]
        for i, _ in enumerate(values[:-1], start=1):
            index.append(index[i - 1] + datetime.timedelta(days=1))
        return pandas.DataFrame(
            values, columns=columns, index=pandas.DatetimeIndex(index)
        )

    def test_download_single_code(self):
        fetcher = downloader.YFDownloader("ASX.AX")
        data_frame = fetcher.download()
        assert set(self.fields) == set(data_frame.columns)

    def test_download_multiple_codes(self):
        fetcher = downloader.YFDownloader(["ASX.AX", "CBA.AX"])
        data_frame = fetcher.download()

        expected_fields = set(
            list(itertools.product(self.fields, ["ASX.AX", "CBA.AX"]))
        )
        assert expected_fields == set(data_frame.columns)

    @mock.patch.object(downloader.YFDownloader, "download")
    def test_iter_result_handle_missing_value(self, mock_download):
        expected_df = self._generate_dataframe(
            [
                [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            ]
        )

        mock_download.return_value = expected_df
        fetcher = downloader.YFDownloader("ASX.AX")
        records = list(itertools.chain.from_iterable(fetcher.iterate_result()))
        assert fetcher.tickers == ["ASX.AX"]
        assert len(records) == 1
        assert records[0] == downloader.Record(
            code="ASX.AX",
            timestamp=datetime.datetime.fromisoformat("1990-01-01"),
            open_=None,
            high=None,
            low=None,
            close=None,
            adj_close=None,
            volume=None,
        )

    @mock.patch.object(downloader.YFDownloader, "download")
    def test_iter_result_handle_multi_code(self, mock_download):
        expected_df = self._generate_dataframe(
            [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]], codes=["ASX.AX", "CBA.AX"]
        )
        mock_download.return_value = expected_df

        fetcher = downloader.YFDownloader(["ASX.AX", "CBA.AX"])
        records = list(itertools.chain.from_iterable(fetcher.iterate_result()))
        assert len(records) == 2
        assert fetcher.tickers == ["ASX.AX", "CBA.AX"]
        assert (
            downloader.Record(
                code="ASX.AX",
                timestamp=datetime.datetime.fromisoformat("1990-01-01"),
                open_=1,
                high=1,
                low=1,
                close=1,
                adj_close=1,
                volume=1,
            )
            in records
        )
        assert (
            downloader.Record(
                code="CBA.AX",
                timestamp=datetime.datetime.fromisoformat("1990-01-01"),
                open_=1,
                high=1,
                low=1,
                close=1,
                adj_close=1,
                volume=1,
            )
            in records
        )
