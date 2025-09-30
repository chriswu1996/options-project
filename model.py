import math
import data
import pandas as pd
from scipy.stats import norm

'''
- Forward price instead of spot
- implied vol surface model
- we can back out r -> F = S e^(r-q)T
- sui, btc, solana / excel spread sheet of 
- deploy function in flask

Intraday options:
 - Use same day option IV from Deribit
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
    # TODO: Parse expiration_timestamp in instruments instead
    diff_days = (exp - pd.Timestamp.utcnow()) / pd.Timedelta(days=1)
    return diff_days

def get_options_table(option_date, exp, mode, ticker):
    options_data = data.get_options_data(ticker, option_date)
    fut_px = options_data.iloc[0].underlying_price

    options_data['option_type'] = options_data['instrument_name'].str.split('-').str[-1]
    options_data['strike'] = options_data['instrument_name'].str.split('-').str[2].astype(int)
    exp_days = get_days_to_exp(exp)  # TODO: use milliseconds instead

    if mode == 'Intraday':
        step = 100 if ticker == 'BTC' else 5
        strikes = set(options_data.query(f'strike < {fut_px}').drop_duplicates('strike').nlargest(2, 'strike')['strike']) | set(options_data.query(f'strike > {fut_px}').drop_duplicates('strike').nsmallest(2, 'strike')['strike'])
        n_steps = int((max(strikes) - min(strikes)) // step)
        strikes = [round(min(strikes) + k * step) for k in range(n_steps + 1)]
        options_data = options_data.set_index(['strike', 'option_type'], drop=True).reindex(pd.MultiIndex.from_product([strikes, ['C', 'P']], names=['strike', 'option_type']))
        options_data['mark_iv'] = options_data.groupby(level='option_type', group_keys=False)['mark_iv'].apply(lambda s: s.interpolate(method='linear'))
        options_data['underlying_price'] = fut_px  # TODO: Change this to spot price instead of futures
        options_data = options_data.reset_index()

    options_data['mark'] = options_data.apply(lambda x: black_scholes(x.underlying_price, x.strike, exp_days / 365, 0, x.mark_iv / 100, x.option_type) / x.underlying_price, axis=1)

    df = options_data.pivot_table(index='strike', columns='option_type', values=['mark', 'mark_iv', 'underlying_price'], aggfunc='first').reset_index()
    df = pd.DataFrame({
        ("Calls", "Mark"): df[('mark', 'C')],
        ("Calls", "Mark_IV"): df[('mark_iv', 'C')],
        ("Calls", "Underlying_Price"): df[('underlying_price', 'C')],
        ("Strike", ""): df[('strike', '')],
        ("Puts", "Mark"): df[('mark', 'P')],
        ("Puts", "Mark_IV"): df[('mark_iv', 'P')],
        ("Puts", "Underlying_Price"): df[('underlying_price', 'P')],
    })
    return df, fut_px