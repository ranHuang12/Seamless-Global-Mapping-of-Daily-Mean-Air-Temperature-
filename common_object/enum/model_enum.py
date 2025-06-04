from enum import Enum


class ModelEnum(Enum):
    LINEAR = "Linear"
    POLYNOMIAL = "Poly"
    LASSO = "Lasso"
    RANDOM_FOREST = "RF"
    SUPPORT_VECTOR_MACHINE = "SVM"
    GRADIENT_BOOSTING_DECISION_TREE = "GBDT"
    EXTREME_GRADIENT_BOOSTING = "XGB"
    FC = "FC"
    CNN = "CNN"
    CNN_LSTM = "CNNLSTM"
    CNN_LSTM_ATTENTION = "CNNLSTMAttention"
