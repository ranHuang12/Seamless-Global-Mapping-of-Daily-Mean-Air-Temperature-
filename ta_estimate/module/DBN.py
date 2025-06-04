import torch
import warnings
import torch.nn as nn
import numpy as np

from torch.utils.data import TensorDataset, DataLoader, Dataset
from torch.optim import Adam, SGD

from ta_estimate.module.rbm import RBM
from ta_estimate.module.genCsvData import indefDataSet


class DBN(nn.Module):
    def __init__(self, hidden_units, visible_units, output_units, k=2,
                 learning_rate=1e-5, learning_rate_decay=False, #1e-5不可改动
                 increase_to_cd_k=False, device='cpu'):
        super(DBN, self).__init__()

        self.n_layers = len(hidden_units)
        self.rbm_layers = []
        self.rbm_nodes = []
        self.device = device
        self.is_pretrained = False
        self.is_finetune = False

        # Creating different RBM layers
        for i in range(self.n_layers):
            if i == 0:
                input_size = visible_units
            else:
                input_size = hidden_units[i - 1]
            rbm = RBM(visible_units=input_size, hidden_units=hidden_units[i],
                      k=k, learning_rate=learning_rate,
                      learning_rate_decay=learning_rate_decay,
                      increase_to_cd_k=increase_to_cd_k, device=device)

            self.rbm_layers.append(rbm)

        self.W_rec = [self.rbm_layers[i].weight for i in range(self.n_layers)]
        self.bias_rec = [self.rbm_layers[i].h_bias for i in range(self.n_layers)]

        for i in range(self.n_layers):
            self.register_parameter('W_rec%i' % i, self.W_rec[i])
            self.register_parameter('bias_rec%i' % i, self.bias_rec[i])

        self.bpnn = torch.nn.Linear(hidden_units[-1], output_units).to(self.device)    
        """ 
        self.bpnn=nn.Sequential(            #用作回归和反向微调参数
            torch.nn.Linear(32, 16),
            torch.nn.ReLU(),
            #torch.nn.Dropout(0.5),
            torch.nn.Linear(16,output_units),
        ).to(self.device)  """

    def forward(self, input_data):
        """
        running a single forward process.

        Args:
            input_data: Input data of the first RBM layer. Shape:
                [batch_size, input_length]

        Returns: Output of the last RBM hidden layer.

        """
        v = input_data.to(self.device)
        
        hid_output = v.clone()
        for i in range(len(self.rbm_layers)):
            hid_output, _ = self.rbm_layers[i].to_hidden(hid_output)
        output = self.bpnn(hid_output)
        return output

    def reconstruct(self, input_data):
        """
        Go forward to the last layer and then go feed backward back to the
        first layer.

        Args:
            input_data: Input data of the first RBM layer. Shape:
                [batch_size, input_length]

        Returns: Reconstructed output of the first RBM visible layer.

        """
        h = input_data.to(self.device)
        p_h = 0
        for i in range(len(self.rbm_layers)):
            # h = h.view((h.shape[0], -1))
            p_h, h = self.rbm_layers[i].to_hidden(h)

        for i in range(len(self.rbm_layers) - 1, -1, -1):
            # h = h.view((h.shape[0], -1))
            p_h, h = self.rbm_layers[i].to_visible(h)
        return p_h, h

    def pretrain(self, x, y, epoch, batch_size):
        hid_output_i = x
        for i in range(len(self.rbm_layers)):
            dataset = indefDataSet(hid_output_i, y)
            dataloader_i = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True )
            self.rbm_layers[i].train_rbm(dataloader_i, epoch)
            hid_output_i, _ = self.rbm_layers[i].forward(dataloader_i)
        self.is_pretrained = True
        return 

    def pretrain_single(self, x, layer_loc, epoch, batch_size):
        """
        Train the ith layer of DBN model.

        Args:
            x: Input of the DBN model.
            layer_loc: Train layer location.
            epoch: Train epoch.
            batch_size: Train batch size.

        Returns:

        """
        if layer_loc > len(self.rbm_layers) or layer_loc <= 0:
            raise ValueError('Layer index out of range.')
        ith_layer = layer_loc - 1
        hid_output_i = torch.tensor(x, dtype=torch.float, device=self.device)

        for ith in range(ith_layer):
            hid_output_i, _ = self.rbm_layers[ith].forward(hid_output_i)

        dataset_i = TensorDataset(hid_output_i)
        dataloader_i = DataLoader(dataset_i, batch_size=batch_size, drop_last=False)

        self.rbm_layers[ith_layer].train_rbm(dataloader_i, epoch)
        hid_output_i, _ = self.rbm_layers[ith_layer].forward(hid_output_i)
        return

    def finetune(self, x, y, epoch, batch_size, loss_function, optimizer, lr_steps, shuffle=False):
        if not self.is_pretrained:
            warnings.warn("Hasn't pretrained DBN model yet. Recommend "
                          "run self.pretrain() first.", RuntimeWarning)
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, lr_steps , gamma=0.9)
        dataset = FineTuningDataset(x, y)
        dataloader = DataLoader(dataset, batch_size, shuffle=shuffle)
        for epoch_i in range(1, epoch + 1):
            total_loss = 0
            t = 0
            for batch in dataloader:
                input_data, ground_truth = batch
                input_data = input_data.view((input_data.shape[0] , -1))
                input_data = input_data.to(self.device)
                ground_truth = ground_truth.to(self.device)
                output = self.forward(input_data)
                ground_truth = ground_truth.reshape(-1,1)
                loss = loss_function(ground_truth, output)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                t += 1
            total_loss = total_loss/t
            if total_loss >= 1e-4:
                disp = '{2:.4f}'
            else:
                disp = '{2:.3e}'
            print(('Epoch:{0}/{1} -rbm_train_loss: ' + disp).format(epoch_i, epoch, total_loss))
            scheduler.step()
        self.is_finetune = True
        return

    def predict(self, x,y, batch_size, shuffle=False):
        """
        Predict

        Args:
            x: DBN input data. Type: ndarray. Shape: (batch_size, visible_units)
            batch_size: Batch size for DBN model.
            shuffle: True if shuffle predict input data.

        Returns: Prediction result. Type: torch.tensor(). Device is 'cpu' so
            it can transferred to ndarray.
            Shape: (batch_size, output_units)

        """
        if not self.is_pretrained:
            warnings.warn("Hasn't pretrained DBN model yet. Recommend "
                          "run self.pretrain() first.", RuntimeWarning)

        if not self.is_pretrained:
            warnings.warn("Hasn't finetuned DBN model yet. Recommend "
                          "run self.finetune() first.", RuntimeWarning)
        y_predict = []

        dataset = FineTuningDataset(x, y)
        dataloader = DataLoader(dataset, 1, shuffle=shuffle)        
        
        with torch.no_grad():
            for batch in dataloader:
                y = self.forward(batch[0].view(batch[0].shape[0], -1))
                y = y.view(-1, 1)
                y_predict.append(y)

        return torch.cat(y_predict, dim=0).cpu().numpy()


class FineTuningDataset(Dataset):
    """
    Dataset class for whole dataset. x: input data. y: output data
    """
    def __init__(self, x, y):
        pass
      
        self.x = x
        self.y = y

    def __getitem__(self, index):
        return self.x[index].astype(np.float32), self.y[index].astype(np.float32)

    def __len__(self):
        return len(self.x)
