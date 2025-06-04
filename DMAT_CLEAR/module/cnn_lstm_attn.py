import torch
from torch import nn


cnn_out_channels = 128
lstm_hidden_size = 128
lstm_num_layers = 2


class CNNLSTMAttention(nn.Module):
    def __init__(self, feature_size, time_size):
        super(CNNLSTMAttention, self).__init__()
        self.feature_size = feature_size
        self.time_size = time_size

        self.conv1 = nn.Conv1d(in_channels=feature_size, out_channels=cnn_out_channels, kernel_size=3, stride=1, padding=1)

        self.bn1 = nn.BatchNorm1d(cnn_out_channels)  # 添加BatchNorm1d层
        self.relu = nn.ReLU()

        self.lstm = nn.LSTM(input_size=cnn_out_channels, hidden_size=lstm_hidden_size, num_layers=lstm_num_layers, batch_first=True)
        self.attn = nn.Linear(lstm_hidden_size+cnn_out_channels, time_size)

        self.fc = nn.Linear(lstm_hidden_size, 1)

    def forward(self, x):
        x = x.view(-1, self.feature_size, self.time_size)
        x = self.conv1(x)
        x = self.relu(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = x.permute(0, 2, 1)
        lstm_out, _ = self.lstm(x)
        lstm_out = self.relu(lstm_out)
        attn_weights = torch.tanh(self.attn(torch.cat((lstm_out, x), 2)))
        attn_weights = torch.softmax(attn_weights, dim=1)
        attn_applied = torch.bmm(attn_weights.transpose(1, 2), lstm_out)
        fc_out = self.fc(attn_applied[:, -1, :])
        return fc_out.squeeze()
