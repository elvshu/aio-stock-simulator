from application.rates.commsec.data_models import CostSchema, RateType, StepCharge

# TradeExecution
# Reference doc: https://www2.commsec.com.au/media/57221/fsg.pdf

# Trade online and settle your trade to a CDIA or CommSec Margin Loan
# Typically Buy/Purchase stock
SettleWithCDIA = CostSchema(
    name="CDIA",
    steps=[
        StepCharge(lower=0, upper=1000, rate=10, rate_type=RateType.Fixed),
        StepCharge(lower=1000, upper=10_000, rate=19.95, rate_type=RateType.Fixed),
        StepCharge(lower=10_000, upper=25_000, rate=29.95, rate_type=RateType.Fixed),
        StepCharge(lower=25_000, upper=None, rate=0.0012, rate_type=RateType.Relative),
    ],
)

# Trade online and settle into a bank account of your choice
# Typically sell stock
SettleToBank = CostSchema(
    name="Bank",
    steps=[
        StepCharge(lower=0, upper=9999.99, rate=29.95, rate_type=RateType.Fixed),
        StepCharge(lower=9999.99, upper=None, rate=0.0031, rate_type=RateType.Relative),
    ],
)

# Trande over phone and deceased estates
PhoneAndDeceased = CostSchema(
    name="PhoneAndDeceased",
    steps=[
        StepCharge(lower=0, upper=10_000, rate=59.95, rate_type=RateType.Fixed),
        StepCharge(
            lower=10_000, upper=25_000, rate=0.0052, rate_type=RateType.Relative
        ),
        StepCharge(
            lower=25_000, upper=1_000_000, rate=0.0049, rate_type=RateType.Relative
        ),
        StepCharge(
            lower=1_000_000, upper=None, rate=0.0011, rate_type=RateType.Relative
        ),
    ],
)

# Trades requiring settlement through a third party
SettlementThroughThirdParty = CostSchema(
    name="SettlementThroughThirdParty",
    steps=[
        StepCharge(lower=0, upper=15_000, rate=99.95, rate_type=RateType.Fixed),
        StepCharge(lower=15_000, upper=None, rate=0.0066, rate_type=RateType.Relative),
    ],
)

# Exchange traded options traded online
ExchangeTradedOptionsOnline = CostSchema(
    name="ExchangeTradedOptionsOnline",
    steps=[
        StepCharge(lower=0, upper=10_000, rate=34.95, rate_type=RateType.Fixed),
        StepCharge(lower=10_000, upper=None, rate=0.0035, rate_type=RateType.Relative),
    ],
)

# Exchange traded options traded over the phone
ExchangeTradedOptionsPhone = CostSchema(
    name="ExchangeTradedOptionsPhone",
    steps=[
        StepCharge(lower=0, upper=10_000, rate=54.60, rate_type=RateType.Fixed),
        StepCharge(lower=10_000, upper=None, rate=0.0054, rate_type=RateType.Relative),
    ],
)
