import numpy as np
import pandas as pd

def calculate_position_size(asset: str, balance: float, risk_pct: float, entry_price: float, stop_price: float, rrr: float, win_rate_pct: float):
    """Calculates position sizing, dollar risk, expected value (EV), and target prices."""
    max_risk_dollars = balance * (risk_pct / 100.0)
    stop_distance = abs(entry_price - stop_price)
    
    if stop_distance == 0:
        raise ValueError("Stop loss price cannot equal entry price.")
        
    if asset == "XAU/USD":
        # 1 Standard Lot = 100 oz ($1 move = $100 per lot)
        position_size = max_risk_dollars / (stop_distance * 100.0)
        unit_label = "Lots"
    else: # BTC/USD
        # Direct BTC Units ($1 move = $1 per BTC)
        position_size = max_risk_dollars / stop_distance
        unit_label = "BTC"
        
    reward_dollars = max_risk_dollars * rrr
    win_prob = win_rate_pct / 100.0
    loss_prob = 1.0 - win_prob
    ev_dollars = (win_prob * reward_dollars) - (loss_prob * max_risk_dollars)
    
    return {
        "max_risk_dollars": max_risk_dollars,
        "position_size": round(position_size, 4),
        "unit_label": unit_label,
        "ev_dollars": round(ev_dollars, 2),
        "target_dollars": round(reward_dollars, 2)
    }

def simulate_trade_compounding(balance: float, risk_pct: float, win_rate_pct: float, rrr: float, num_trades: int = 40):
    """Generates trade-by-trade compounding equity curve based on geometric expectation."""
    win_prob = win_rate_pct / 100.0
    r = risk_pct / 100.0
    
    # Growth multiplier per trade pair
    trade_growth_factor = ((1 + rrr * r) ** win_prob) * ((1 - r) ** (1 - win_prob))
    
    equity = [balance]
    for i in range(1, num_trades + 1):
        current_eq = balance * (trade_growth_factor ** i)
        equity.append(current_eq)
        
    return pd.DataFrame({"Trade": list(range(num_trades + 1)), "Equity": equity})

def simulate_monte_carlo(initial_deposit: float, max_risk_pct: float, target_profit_pct: float, volatility_pct: float, days: int = 60, num_paths: int = 8):
    """Simulates multi-path Geometric Brownian Motion bounded by Stop-Loss Floor and Take-Profit Cap."""
    stop_floor = initial_deposit * (1.0 - max_risk_pct / 100.0)
    profit_cap = initial_deposit * (1.0 + target_profit_pct / 100.0)
    
    dt = 1.0 / 252.0 # Daily time step
    sigma = volatility_pct / 100.0
    
    paths = []
    for _ in range(num_paths):
        path = [initial_deposit]
        current_val = initial_deposit
        
        for _ in range(days):
            if current_val <= stop_floor or current_val >= profit_cap:
                path.append(current_val) # Hold at boundary upon trigger
                continue
                
            shock = np.random.normal(0, 1) * sigma * np.sqrt(dt)
            current_val = current_val * np.exp(-0.5 * (sigma ** 2) * dt + shock)
            path.append(current_val)
            
        paths.append(path)
        
    df = pd.DataFrame(paths).T
    df.columns = [f"Path {i+1}" for i in range(num_paths)]
    df.index.name = "Day"
    return df, stop_floor, profit_cap