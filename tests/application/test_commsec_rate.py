import pytest

from application.rates.commsec import SettleToBank, SettleWithCDIA


class TestSettleWithCDIA:
    @pytest.mark.parametrize(
        "transaction_amount, expected_overhead",
        [
            (1000, 10),
            (10_000, 19.95),
            (25_000, 29.95),
            (30_000, round(30_000 * 0.0012, 2)),
        ],
    )
    def test_settle_with_cdia(self, transaction_amount, expected_overhead):
        assert SettleWithCDIA.total(transaction_amount) == expected_overhead


class TestSettleToBank:
    @pytest.mark.parametrize(
        "transaction_amount, expected_overhead",
        [(9999.99, 29.95), (15_000, round(15_000 * 0.0031, 2))],
    )
    def test_settle_to_bank(self, transaction_amount, expected_overhead):
        assert SettleToBank.total(transaction_amount) == expected_overhead
