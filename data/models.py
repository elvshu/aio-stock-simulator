import datetime

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeBoundary, RangeOperators
from django.db import models
from utils import industrytime


class DateRangeFunc(models.Func):
    function = "daterange"
    output_field = DateRangeField()


class IndustryGroup(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"

    def __repr__(self) -> str:
        return f"<{self}>"


class Company(models.Model):
    name = models.CharField(max_length=128)
    trading_code = models.CharField(max_length=10, unique=True, primary_key=True)
    industry = models.ForeignKey(
        IndustryGroup, null=True, blank=True, on_delete=models.DO_NOTHING
    )
    description = models.TextField(null=True, blank=True)
    others = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.DO_NOTHING
    )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.trading_code}"

    def __repr__(self) -> str:
        return f"{self}"

    # queries
    def is_active_at(self, at: datetime.datetime | None = None) -> bool:
        if at is None:
            at = industrytime.industry_midnight(datetime.datetime.now())
        return self.active_periods.filter(
            (models.Q(end_date__isnull=True) | models.Q(end_date__gte=at)),
            start_date__lte=at,
        ).exists()


class ActivePeriod(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="active_periods"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True)

    class Meta:
        constraints = [
            ExclusionConstraint(
                name="exclude_overlapping_period",
                expressions=(
                    (
                        DateRangeFunc("start_date", "end_date", RangeBoundary()),
                        RangeOperators.OVERLAPS,
                    ),
                    ("company", RangeOperators.EQUAL),
                ),
            )
        ]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.company.trading_code} {self.start_date} -> {self.end_date}"

    def __repr__(self) -> str:
        return f"{self}"


class PriceRecord(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="prices"
    )
    timestamp = models.DateTimeField()
    low = models.DecimalField(decimal_places=3, max_digits=10)
    high = models.DecimalField(decimal_places=3, max_digits=10)
    open = models.DecimalField(decimal_places=3, max_digits=10)
    close = models.DecimalField(decimal_places=3, max_digits=10)
    adj_close = models.DecimalField(decimal_places=3, max_digits=10, null=True)
    volume = models.IntegerField()

    class Meta:
        unique_together = ("company", "timestamp")


class Portfolio(models.Model):
    name = models.CharField(max_length=128, unique=True)


class Holdings(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="holdings"
    )
    purchased_price = models.DecimalField(decimal_places=3, max_digits=10)
    purchased_at = models.DateTimeField()
