import datetime
from unittest import mock

import pandas as pd
import pytest
import time_machine
from application import yfinance_adaptor
from application.yfinance_adaptor import adaptors
from data import models
from django.db import connection
from tests import factories
from utils import asx, industrytime

from domain import operations, queries


@pytest.mark.django_db
@mock.patch.object(asx, "get_current_companies")
class TestListing:
    def test_create_new_listing_company(self, mock_get_current_companies):
        mock_get_current_companies.return_value = [
            asx.CompanyInfo(name="TEST", code="TEST", group="TEST")
        ]
        operations.refresh_asx_company_list()
        queryset = models.Company.objects.filter(trading_code="TEST")
        assert queryset.exists()
        test_company = queryset.get()
        assert test_company.active_periods.latest(
            "start_date"
        ).start_date == datetime.date(1900, 1, 1)
        assert test_company.active_periods.latest("start_date").end_date is None
        assert test_company.name == "TEST"
        assert test_company.industry.name == "TEST"

    @time_machine.travel("2023-01-01", tick=False)
    def test_relist_previously_disabled_company(self, mock_get_current_companies):
        mock_get_current_companies.return_value = [
            asx.CompanyInfo(name="TEST", code="TEST", group="TEST")
        ]
        test_company = factories.CompanyFactory(trading_code="TEST")
        factories.ActivePeriodFactory(
            company=test_company, start_date="2022-01-01", end_date="2022-12-31"
        )
        assert test_company.active_periods.latest(
            "start_date"
        ).end_date == datetime.date(2022, 12, 31)
        operations.refresh_asx_company_list()
        assert test_company.active_periods.latest("start_date").end_date is None

    @time_machine.travel("2023-01-01", tick=False)
    def test_retiring_listing_company(self, mock_get_current_companies):
        mock_get_current_companies.return_value = []
        test_company = factories.CompanyFactory()
        factories.ActivePeriodFactory(company=test_company, start_date="2022-01-01")
        operations.refresh_asx_company_list()
        assert test_company.active_periods.latest(
            "start_date"
        ).end_date == datetime.date(2023, 1, 1)

    @time_machine.travel("2023-01-01", tick=False)
    def test_noop_currently_listed_company(self, mock_get_current_companies):
        mock_get_current_companies.return_value = [
            asx.CompanyInfo(name="TEST", code="TEST", group="TEST")
        ]
        test_company = factories.CompanyFactory(trading_code="TEST")
        factories.ActivePeriodFactory(company=test_company, start_date="2022-01-01")
        operations.refresh_asx_company_list()
        assert test_company.active_periods.latest(
            "start_date"
        ).start_date == datetime.date(2022, 1, 1)
        assert test_company.active_periods.latest("start_date").end_date is None


@pytest.mark.django_db
@time_machine.travel("2023-01-01", tick=False)
@mock.patch.object(
    yfinance_adaptor, "YFDownloader", wraps=yfinance_adaptor.YFDownloader
)
def test_fetch_prices(mock_yf_downloader, django_db_setup, django_db_blocker):
    test_trading_code = "ATM"
    postgre_adaptor = adaptors.PostGresAdaptor.from_django_settings()
    with connection.cursor() as cursor:
        test_company = factories.CompanyFactory(trading_code=test_trading_code)
        factories.ActivePeriodFactory(
            company=test_company, start_date=datetime.date(1980, 1, 1)
        )
        cursor.execute("COMMIT")

    operations.update_prices(postgre_adaptor)

    start_datetime = industrytime.industry_midnight(datetime.datetime(1980, 1, 1))
    mock_yf_downloader.assert_called_once_with(
        tickers=[f"{test_trading_code}.AX"],
        start=start_datetime,
        adaptor=postgre_adaptor,
    )
    price_count = test_company.prices.count()
    assert price_count != 0

    with connection.cursor() as cursor:
        test_company.prices.filter(
            timestamp__gt=industrytime.as_industry_time(datetime.datetime(2020, 1, 2))
        ).delete()
        cursor.execute("COMMIT")
    assert test_company.prices.count() < price_count

    operations.update_prices(postgre_adaptor)

    mock_yf_downloader.assert_called_with(
        tickers=[f"{test_trading_code}.AX"],
        start=industrytime.industry_midnight(datetime.datetime(2020, 1, 3)),
        adaptor=postgre_adaptor,
    )
    assert test_company.prices.count() == price_count


@pytest.mark.django_db
def test_organise_active_period():
    test_company = factories.CompanyFactory(trading_code="BLC")
    test_period = factories.ActivePeriodFactory(
        company=test_company, start_date=datetime.date(1980, 1, 1)
    )
    factories.PriceFactory(
        company=test_company,
        timestamp=industrytime.industry_midnight(datetime.datetime(2020, 1, 1)),
    )
    operations.organise_active_periods(test_company)
    assert test_period.start_date == datetime.date()
