import datetime
import time

from application import yfinance_adaptor
from application.yfinance_adaptor import adaptors
from data import models
from django.db import transaction
from django.db.models import Exists, OuterRef, QuerySet
from utils import asx, industrytime

from domain import queries


@transaction.atomic
def refresh_asx_industry_groups() -> None:
    groups = asx.get_industry_groups()
    new_groups = []
    for industry in groups - set(
        models.IndustryGroup.objects.values_list("name", flat=True)
    ):
        new_groups.append(models.IndustryGroup(name=industry))
    if new_groups:
        models.IndustryGroup.objects.bulk_create(new_groups)


def _handle_current_active_list() -> None:
    industries = {
        industry.name: industry for industry in models.IndustryGroup.objects.all()
    }
    current_company_list = {
        comp_info.code: comp_info for comp_info in asx.get_current_companies()
    }
    existing_list = {
        db_comp.trading_code: db_comp for db_comp in queries.get_listing_companies()
    }
    today = datetime.date.today()

    new_companies = []
    new_periods = []
    for trading_code, comp_info in current_company_list.items():
        if trading_code not in existing_list:
            # new listing
            company_info = current_company_list[trading_code]
            industry = industries[company_info.group]
            new_companies.append(
                models.Company(
                    name=company_info.name,
                    trading_code=comp_info.code,
                    industry=industry,
                )
            )
            new_periods.append(
                models.ActivePeriod(
                    company=new_companies[-1], start_date=datetime.date(1900, 1, 1)
                )
            )
        elif not existing_list[trading_code].active:
            company = existing_list[trading_code]
            new_periods.append(models.ActivePeriod(company=company, start_date=today))

    if new_companies:
        models.Company.objects.bulk_create(new_companies)

    if new_periods:
        models.ActivePeriod.objects.bulk_create(new_periods)


def _handle_deactivating_list() -> None:
    today = datetime.date.today()
    current_company_list = {
        comp_info.code: comp_info for comp_info in asx.get_current_companies()
    }

    ending_periods = []
    for company in queries.get_listing_companies():
        if not company.active:
            continue
        if company.trading_code not in current_company_list:
            active_period = company.active_periods.latest("start_date")
            active_period.end_date = today
            ending_periods.append(active_period)

    if ending_periods:
        models.ActivePeriod.objects.bulk_update(ending_periods, ["end_date"])


@transaction.atomic
def refresh_asx_company_list() -> None:
    refresh_asx_industry_groups()

    _handle_current_active_list()

    _handle_deactivating_list()


def update_prices(adaptor: adaptors.Adaptor, codes: list[str] | None = None) -> None:
    active_codes = queries.get_listing_companies(active_only=True).values_list(
        "trading_code", flat=True
    )
    if codes is not None:
        active_codes &= set(codes)

    latest = (
        models.PriceRecord.objects.filter(company__trading_code__in=active_codes)
        .order_by("timestamp")
        .last()
    )
    if latest is None:
        first_timestamp = industrytime.industry_midnight(datetime.datetime(1980, 1, 1))
    else:
        first_timestamp = industrytime.as_industry_time(
            latest.timestamp
        ) + datetime.timedelta(days=1)

    if first_timestamp.date() > datetime.date.today():
        return None

    # delete all later prices as we are going to update them with
    # potentially newer revaised adj_close etc.
    models.PriceRecord.objects.filter(
        company__trading_code__in=active_codes, timestamp__gte=first_timestamp
    ).delete()

    downloader = yfinance_adaptor.YFDownloader(
        tickers=[f"{code}.AX" for code in active_codes],
        start=first_timestamp,
        adaptor=adaptor,
    )
    downloader.export(table_name=models.PriceRecord._meta.db_table)


def organise_active_periods(company: models.Company) -> None:
    earliest_price = company.prices.order_by("timestamp").first()
    if not earliest_price:
        return None
    listing_date = industrytime.as_industry_time(earliest_price.timestamp).date()
    earliest_active_period = company.active_periods.order_by("start_date").first()
    if not earliest_active_period:
        models.ActivePeriod(
            company=company,
            start_date=listing_date,
        ).save()
    else:
        earliest_active_period.start_date = listing_date
        earliest_active_period.save()
