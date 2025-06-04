import torch.nn
from torch import nn


class FC(nn.Module):
    def __init__(self, in_features):
        super(FC, self).__init__()
        self.input = torch.nn.Linear(in_features, 16)
        self.relu = nn.ReLU()
        self.hidden = torch.nn.Linear(16, 32)
        self.output = torch.nn.Linear(32, 1)

    def forward(self, x):
        x = self.input(x)
        x = self.relu(x)
        x = self.hidden(x)
        x = self.relu(x)
        return self.output(x).squeeze()
