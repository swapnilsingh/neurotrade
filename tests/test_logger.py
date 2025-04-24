from utils.trade_logger import log_trade
import os
import json

def test_log_trade(tmp_path):
    file_path = tmp_path / "log.json"
    data = {"symbol": "BTCUSDT", "signal": "BUY", "timestamp": 123, "equity": 1000, "reason": "test", "votes": {}, "indicators": {}, "strategy_config": {}, "model_version": "v1"}
    log_trade("BTCUSDT", data, file_path=str(file_path))
    assert file_path.exists()
    with open(file_path) as f:
        line = json.loads(f.readline())
        assert line["signal"] == "BUY"
