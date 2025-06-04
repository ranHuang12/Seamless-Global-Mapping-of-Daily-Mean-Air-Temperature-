import torch
from torch import nn


class CNN(nn.Module):
    def __init__(self, feature_size):
        super(CNN, self).__init__()
        self.feature_size = feature_size
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=2, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(in_channels=2, out_channels=4, kernel_size=3, padding=1)
        self.conv3 = nn.Conv1d(in_channels=4, out_channels=8, kernel_size=3, padding=1)
        self.conv4 = nn.Conv1d(in_channels=8, out_channels=16, kernel_size=3, padding=1)
        self.conv5 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=3, padding=1)
        self.conv6 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.conv7 = nn.Conv1d(in_channels=64, out_channels=32, kernel_size=3, padding=1)
        self.conv8 = nn.Conv1d(in_channels=32, out_channels=16, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=3, stride=1)
        self.fc = nn.Linear(in_features=16, out_features=1)

    def forward(self, x):
        x = x.view(-1, 1, self.feature_size)
        x = self.conv1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.conv3(x)
        x = self.relu(x)
        x = self.conv4(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.conv5(x)
        x = self.relu(x)
        x = self.conv6(x)
        x = self.relu(x)
        x = self.pool(x)
        x = self.conv7(x)
        x = self.relu(x)
        x = self.conv8(x)
        x = self.relu(x)
        x = self.pool(x)
        return self.fc(x.squeeze()).squeeze()

