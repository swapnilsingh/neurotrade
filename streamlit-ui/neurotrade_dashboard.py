from core.decorators.decorators import inject_logger, inject_config
import streamlit as st
from dashboard_runner import NeurotradeDashboard

@inject_logger()
@inject_config("configs/streamlit_dashboard.yaml")
class NeurotradeApp:
    def __init__(self):
        self.logger.info("🚀 Starting Neurotrade Streamlit Dashboard...")
        self.runner = NeurotradeDashboard()

if __name__ == "__main__":
    NeurotradeApp()
