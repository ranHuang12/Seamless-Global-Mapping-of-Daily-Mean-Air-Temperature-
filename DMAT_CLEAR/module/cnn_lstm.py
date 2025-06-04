from torch import nn


class CNNLSTM(nn.Module):
    hidden_size = 128  # 设置隐藏层
    num_layers = 2  # 设置LSTM层数

    def __init__(self, in_channels):
        super(CNNLSTM, self).__init__()
        self.in_channels = in_channels

        # CNN Layers
        self.conv1 = nn.Conv1d(in_channels=in_channels, out_channels=128, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm1d(128)  # 添加BatchNorm1d层
        self.relu = nn.ReLU()

        # LSTM Layer
        self.lstm = nn.LSTM(input_size=128, hidden_size=self.hidden_size, num_layers=self.num_layers, batch_first=True)

        # Fully Connected Layer
        self.fc = nn.Linear(self.hidden_size, 1)

    def forward(self, x):
        # CNN Forward
        x = x.view(-1, self.in_channels, 1)
        x = self.conv1(x)
        x = self.bn1(x)  # 在激活函数前添加BatchNorm
        x = self.relu(x)
        x = x.permute(0, 2, 1)

        # LSTM Forward
        lstm_out, _ = self.lstm(x)
        lstm_out = self.relu(lstm_out)

        # Fully Connected Layer
        fc_out = self.fc(lstm_out[:, -1, :])

        return fc_out.squeeze()