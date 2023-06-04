import concurrent
import time

from application.yfinance_adaptor import adaptors
from data.models import ActivePeriod, Company, IndustryGroup
from django.core.management.base import BaseCommand, CommandError
from domain import operations, queries


class Command(BaseCommand):
    help = "Refresh the currently ASX listing company"

    def add_arguments(self, parser):
        parser.add_argument(
            "-c",
            "--codes",
            type=str,
            help="Trading codes to be updated. Default to all codes",
        )

    def handle(self, *args, **options) -> None:
        codes = (
            options["codes"]
            if options["codes"] is None
            else options["codes"].split(",")
        )
        start = time.time()
        operations.refresh_asx_company_list()
        operations.update_prices(
            adaptors.PostGresAdaptor.from_django_settings(), codes=codes
        )
        for company in queries.get_listing_companies(active_only=True):
            operations.organise_active_periods(company)
        print(f"Updated in {time.time() - start}s")
