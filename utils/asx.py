import csv
import dataclasses
import io
from functools import lru_cache

import requests

ListingCompanies = "https://www.asx.com.au/asx/research/ASXListedCompanies.csv"


@dataclasses.dataclass(frozen=True)
class CompanyInfo:
    name: str
    code: str
    group: str


@lru_cache
def get_current_companies() -> list[CompanyInfo]:
    mapping = {
        "Company name": "name",
        "ASX code": "code",
        "GICS industry group": "group",
    }
    response = requests.get(ListingCompanies)
    if response.status_code == 200:
        data = response.text.split("\n", 1)[1]
        _, header, data = data.split("\n", 2)
        fields = header.split(",")
        return [
            CompanyInfo(
                **{
                    mapping_to: row[mapping_from]
                    for mapping_from, mapping_to in mapping.items()
                }
            )
            for row in csv.DictReader(io.StringIO(data), fieldnames=fields)
        ]


def get_industry_groups() -> set[str]:
    return {company_info.group for company_info in get_current_companies()}
