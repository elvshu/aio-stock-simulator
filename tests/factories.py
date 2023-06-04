import factory

from data import models


class IndustryGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.IndustryGroup
        django_get_or_create = ("name",)

    name = "test"


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Company

    name = "Test Company"
    industry = factory.SubFactory(IndustryGroupFactory)
    trading_code = "AAC"


class ActivePeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ActivePeriod


class PriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PriceRecord

    high = 1
    low = 1
    close = 1
    adj_close = 1
    open = 1
    volume = 100
