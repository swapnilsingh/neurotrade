from inference.evaluator_agent import EvaluatorAgent
from inference.reward_agent import RewardAgent
from inference.dynamic_tick_essemble_agent import DynamicTickEnsembleAgent
from utils.config_loader import load_config

def create_agents():
    evaluator_config = load_config("configs/evaluator_agent.yaml")
    reward_config = load_config("configs/reward_agent.yaml")
    ensemble_config = load_config("configs/ensemble_agent.yaml")

    evaluator = EvaluatorAgent(config=evaluator_config)
    reward_agent = RewardAgent(evaluator, config=reward_config)
    dqn_agent = DynamicTickEnsembleAgent(config=ensemble_config)

    return evaluator, reward_agent, dqn_agent
