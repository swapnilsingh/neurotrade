def compute_reward(prev_equity, current_equity):
    return (current_equity - prev_equity) / prev_equity
