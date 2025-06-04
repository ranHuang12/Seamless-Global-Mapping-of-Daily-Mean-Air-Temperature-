import torch
from torch.utils.data import Dataset
from torch.utils.data.dataset import T_co


class DLDataset(Dataset):
    def __init__(self, x, y, device):
        self.x = torch.tensor(x, dtype=torch.float32, device=device)
        self.y = torch.tensor(y, dtype=torch.float32, device=device)

    def __getitem__(self, index) -> T_co:
        return self.x[index], self.y[index]

    def __len__(self):
        return len(self.x)
