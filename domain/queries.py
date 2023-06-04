import datetime

from data import models
from django.db.models import Exists, OuterRef, Q, QuerySet


def get_listing_companies(active_only: bool = False) -> QuerySet:
    today = datetime.date.today()

    is_active = models.ActivePeriod.objects.filter(
        Q(end_date__isnull=True) or Q(end_date__gte=today), company__pk=OuterRef("pk")
    )

    queryset = models.Company.objects.annotate(active=Exists(is_active))
    if active_only:
        queryset = queryset.filter(active=active_only)
    return queryset
