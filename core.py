# core.py
from dataclasses import dataclass
from math import sqrt
from typing import Optional


@dataclass
class Inputs:


    mu: float
    sigma_p: float
    sigma_tool: float
    sigma_operator: float
    lsl: float
    usl: float
    n: int
    cpk_threshold: float
    destructive: bool = False
    sigma_m_override: Optional[float] = None  # למדידה הרסנית/מיוחדת אם רוצים להזין ישירות
    bias: float = 0.0

@dataclass
class Results:
    sigma_m: float
    sigma_total: float
    cp_true: float
    cp_meas: float
    cpk_true: float
    cpk_meas: float
    pass_true: bool
    pass_meas: bool
    error_type: str  # "OK" / "α" / "β"


def _validate(inp: Inputs) -> None:
    if inp.usl <= inp.lsl:
        raise ValueError("USL must be greater than LSL.")
    if inp.sigma_p <= 0:
        raise ValueError("σp must be > 0.")
    if inp.sigma_tool < 0 or inp.sigma_operator < 0:
        raise ValueError("σtool and σoperator must be >= 0.")
    if inp.n < 2:
        raise ValueError("n must be at least 2.")
    if inp.cpk_threshold <= 0:
        raise ValueError("Cpk threshold must be > 0.")
    if inp.sigma_m_override is not None and inp.sigma_m_override < 0:
        raise ValueError("σm override must be >= 0.")


def _cp(usl: float, lsl: float, sigma: float) -> float:
    return (usl - lsl) / (6.0 * sigma)


def _cpk(usl: float, lsl: float, mu: float, sigma: float) -> float:
    cpu = (usl - mu) / (3.0 * sigma)
    cpl = (mu - lsl) / (3.0 * sigma)
    return min(cpu, cpl)


def compute(inp: Inputs) -> Results:
    _validate(inp)

    # σm (שונות מדידה)
    if inp.sigma_m_override is not None:
        sigma_m = inp.sigma_m_override
    else:
        sigma_m = sqrt(inp.sigma_tool**2 + inp.sigma_operator**2)

    # σtotal
    sigma_total = sqrt(inp.sigma_p**2 + sigma_m**2)
    mu_true = inp.mu
    mu_meas = inp.mu + inp.bias
    cp_true = _cp(inp.usl, inp.lsl, inp.sigma_p)
    cp_meas = _cp(inp.usl, inp.lsl, sigma_total)

    cpk_true = _cpk(inp.usl, inp.lsl, mu_true, inp.sigma_p)
    cpk_meas = _cpk(inp.usl, inp.lsl, mu_meas, sigma_total)

    pass_true = cpk_true >= inp.cpk_threshold
    pass_meas = cpk_meas >= inp.cpk_threshold

    if pass_true and not pass_meas:
        err = "α"  # דחייה שגויה
    elif (not pass_true) and pass_meas:
        err = "β"  # קבלה שגויה
    else:
        err = "OK"

    return Results(
        sigma_m=sigma_m,
        sigma_total=sigma_total,
        cp_true=cp_true,
        cp_meas=cp_meas,
        cpk_true=cpk_true,
        cpk_meas=cpk_meas,
        pass_true=pass_true,
        pass_meas=pass_meas,
        error_type=err
    )
