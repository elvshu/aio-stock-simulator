# Generated by Django 4.2.1 on 2023-05-10 00:16

import data.models
import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        BtreeGistExtension(),
        migrations.CreateModel(
            name="Company",
            fields=[
                ("name", models.CharField(max_length=128)),
                (
                    "trading_code",
                    models.CharField(
                        max_length=10, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="IndustryGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="PriceRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("timestamp", models.DateTimeField()),
                ("low", models.DecimalField(decimal_places=3, max_digits=10)),
                ("high", models.DecimalField(decimal_places=3, max_digits=10)),
                ("open", models.DecimalField(decimal_places=3, max_digits=10)),
                ("close", models.DecimalField(decimal_places=3, max_digits=10)),
                ("adj_close", models.DecimalField(decimal_places=3, max_digits=10)),
                ("volume", models.IntegerField()),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prices",
                        to="data.company",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="company",
            name="industry",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="data.industrygroup",
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="others",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="data.company",
            ),
        ),
        migrations.CreateModel(
            name="ActivePeriod",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(null=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="active_periods",
                        to="data.company",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="activeperiod",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=(
                    (
                        data.models.DateRangeFunc(
                            "start_date",
                            "end_date",
                            django.contrib.postgres.fields.ranges.RangeBoundary(),
                        ),
                        "&&",
                    ),
                    ("company", "="),
                ),
                name="exclude_overlapping_period",
            ),
        ),
    ]