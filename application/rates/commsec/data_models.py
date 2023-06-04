import dataclasses
import enum
import functools
import sys

import pydantic

BigInt = sys.maxsize


class RateType(enum.Enum):
    Fixed = "Fixed"
    Relative = "Relative"


@functools.total_ordering
@dataclasses.dataclass(frozen=True)
class StepCharge:
    lower: float
    rate: float
    rate_type: RateType
    upper: float | None = None

    def __gt__(self, other: "StepCharge") -> bool:
        return self.lower > other.lower

    def __eq__(self, other: "StepCharge") -> bool:
        return self.lower == other.lower

    @property
    def true_upper(self) -> float:
        return self.upper if self.upper else BigInt

    def contains(self, value: float) -> bool:
        return self.lower < value <= self.true_upper

    def cost(self, value: float) -> float:
        if not self.contains(value):
            return 0

        match self.rate_type:
            case RateType.Fixed:
                return self.rate
            case RateType.Relative:
                return round(value * self.rate, 2)


class CostSchema(pydantic.BaseModel):
    name: str
    steps: list[StepCharge]

    @pydantic.validator("steps")
    def steps_must_be_unique(cls, v, values, **kwargs):
        steps = [(step.lower, step.upper) for step in sorted(v)]
        for i, (step_lower, _step_upper) in enumerate(steps[1:], start=1):
            _prev_step_lower, prev_step_upper = steps[i - 1]
            if step_lower != prev_step_upper:
                raise ValueError(
                    f"No over lap between: {prev_step_upper} and {step_lower}"
                )
        return v

    def total(self, value: float) -> float:
        for step in self.steps:
            if step.contains(value):
                return step.cost(value)
