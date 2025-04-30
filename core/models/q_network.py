
import torch.nn as nn

class QNetwork(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_layers=None):
        super(QNetwork, self).__init__()
        hidden_layers = hidden_layers or [128, 128]

        layers = []
        in_dim = input_dim
        for h in hidden_layers:
            layers.append(nn.Linear(in_dim, h))
            layers.append(nn.ReLU())
            in_dim = h
        layers.append(nn.Linear(in_dim, output_dim))

        self.model = nn.Sequential(*layers)

    def forward(self, x):
        return self.model(x)

