import math
import pandas as pd
from scipy.stats import norm

'''
- Forward price instead of spot
- implied vol surface model
- we can back out r -> F = S e^(r-q)T
- sui, btc, solana / excel spread sheet of 
- deploy function in flask
'''

def black_scholes(F, K, T, r, sigma, option_type):
    """
    Black-Scholes option pricing model.

    Parameters:
        F : float - futures price of the asset
        K : float - strike price
        T : float - time to maturity in years
        r : float - risk-free interest rate (annual, continuously compounded)
        sigma : float - volatility (annualized standard deviation)
        option_type : str - "call" or "put"

    Returns:
        float - fair value of the option
    """
    d1 = (math.log(F / K) + 0.5 * sigma**2 * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    match option_type.upper():
        case "C":
            return math.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))
        case "P":
            return math.exp(-r * T) * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
        case _:
            raise ValueError("option_type must be 'C' or 'P'")

def get_days_to_exp(exp):
    # Daily options expire every day at 08:00 UTC
    # TODO: Parse expiration_timestamp in instruments instead
    exp_8am = pd.Timestamp(exp.date(), tz='UTC') + pd.Timedelta(hours=8)
    now = pd.Timestamp.utcnow()
    diff_days = (exp_8am - now) / pd.Timedelta(days=1)
    return diff_days