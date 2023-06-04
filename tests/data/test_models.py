import pytest
import time_machine
from django.db.utils import IntegrityError
from tests import factories

from data import models


@pytest.mark.django_db
class TestData:
    @time_machine.travel("2022-02-01", tick=False)
    def test_company_is_active(self):
        test_company = factories.CompanyFactory(trading_code="AAC")
        factories.ActivePeriodFactory(
            company=test_company, start_date="2022-01-01", end_date="2023-01-01"
        )
        test_company.refresh_from_db()
        assert test_company.is_active_at()

    def test_active_period_raises_overlap_error(self):
        test_company = factories.CompanyFactory(trading_code="AAC")
        factories.ActivePeriodFactory(
            company=test_company, start_date="2022-01-01", end_date="2023-01-01"
        )
        with pytest.raises(IntegrityError):
            factories.ActivePeriodFactory(
                company=test_company, start_date="2022-06-01", end_date="2023-01-03"
            )

    def test_active_periods_overlaps_but_on_different_companies(self):
        test_company_1 = factories.CompanyFactory(trading_code="AAC")
        test_company_2 = factories.CompanyFactory(trading_code="ABC")

        factories.ActivePeriodFactory(
            company=test_company_1, start_date="2022-01-01", end_date="2023-01-01"
        )
        factories.ActivePeriodFactory(
            company=test_company_2, start_date="2022-01-01", end_date="2023-01-01"
        )

        assert models.ActivePeriod.objects.all().count() == 2
