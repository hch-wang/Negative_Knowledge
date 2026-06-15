"""
EEG2EEG: Learn mapping from Sub01 EEG representations to Sub03 EEG representations.
Architecture: U-Net-style 1D conv network with 8 layers, channel-wise convolutions.
"""

import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# ── Paths ──────────────────────────────────────────────────────────────────────
TRAIN_SUB01 = "benchmark/datasets/thingseeg2/train/sub01.npy"
TRAIN_SUB03 = "benchmark/datasets/thingseeg2/train/sub03.npy"
TEST_SUB01  = "benchmark/datasets/thingseeg2/test/sub01.npy"
OUTPUT_PATH = "pred_results/eeg2eeg_sub01tosub03_pred.npy"

os.makedirs("pred_results", exist_ok=True)

# ── Hyper-parameters ───────────────────────────────────────────────────────────
CHANNELS   = 17
TIMEPOINTS = 200
BATCH_SIZE = 64
EPOCHS     = 30
LR         = 1e-3
DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ── Model ──────────────────────────────────────────────────────────────────────
class ChannelWiseConv1d(nn.Module):
    """Apply the same 1D conv independently to each EEG channel (groups=channels)."""

    def __init__(self, in_ch, out_ch, kernel_size=3, padding=1):
        super().__init__()
        # groups=in_ch means each channel is convolved independently
        self.conv = nn.Conv1d(
            in_ch, out_ch, kernel_size=kernel_size, padding=padding, groups=in_ch
        )

    def forward(self, x):
        return self.conv(x)


class DoubleConv(nn.Module):
    """Two channel-wise conv+ReLU blocks."""

    def __init__(self, channels):
        super().__init__()
        self.net = nn.Sequential(
            ChannelWiseConv1d(channels, channels),
            nn.ReLU(inplace=True),
            ChannelWiseConv1d(channels, channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class EEG2EEG(nn.Module):
    """
    U-Net-style network with 8 layers (4 encoder + 4 decoder).
    All convolutions are applied channel-wise (independently per EEG channel).

    Encoder path  (layers 1-4): DoubleConv → MaxPool(2)
    Decoder path  (layers 5-8): Upsample → UpConv → cat(skip) → DoubleConv
    Final          layer:        Conv1d(kernel=1) to match output shape
    """

    def __init__(self, channels=17):
        super().__init__()
        C = channels

        # Encoder
        self.enc1 = DoubleConv(C)  # layer 1
        self.enc2 = DoubleConv(C)  # layer 2
        self.enc3 = DoubleConv(C)  # layer 3
        self.enc4 = DoubleConv(C)  # layer 4 (bottleneck)

        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)

        # Decoder up-convolutions (channel-wise)
        self.up3 = ChannelWiseConv1d(C, C, kernel_size=3, padding=1)  # layer 5
        self.dec3 = DoubleConv(C)

        self.up2 = ChannelWiseConv1d(C, C, kernel_size=3, padding=1)  # layer 6
        self.dec2 = DoubleConv(C)

        self.up1 = ChannelWiseConv1d(C, C, kernel_size=3, padding=1)  # layer 7
        self.dec1 = DoubleConv(C)                                       # layer 8

        # Final 1×1 conv to match output shape
        self.final = nn.Conv1d(C, C, kernel_size=1)

    def forward(self, x):
        # x: (B, C, T)
        # -- Encoder --
        s1 = self.enc1(x)           # (B, C, T)
        s2 = self.enc2(self.pool(s1))  # (B, C, T/2)
        s3 = self.enc3(self.pool(s2))  # (B, C, T/4)
        s4 = self.enc4(self.pool(s3))  # (B, C, T/8)  bottleneck

        # -- Decoder --
        # Layer 5: upsample + up-conv + cat(s3) + double-conv
        d3 = nn.functional.interpolate(s4, scale_factor=2, mode="linear", align_corners=False)
        d3 = self.up3(d3)
        if d3.shape[-1] != s3.shape[-1]:
            d3 = d3[..., : s3.shape[-1]]
        d3 = self.dec3(d3 + s3)   # skip connection (add instead of cat to keep C fixed)

        # Layer 6
        d2 = nn.functional.interpolate(d3, scale_factor=2, mode="linear", align_corners=False)
        d2 = self.up2(d2)
        if d2.shape[-1] != s2.shape[-1]:
            d2 = d2[..., : s2.shape[-1]]
        d2 = self.dec2(d2 + s2)

        # Layer 7 + 8
        d1 = nn.functional.interpolate(d2, scale_factor=2, mode="linear", align_corners=False)
        d1 = self.up1(d1)
        if d1.shape[-1] != s1.shape[-1]:
            d1 = d1[..., : s1.shape[-1]]
        d1 = self.dec1(d1 + s1)

        return self.final(d1)


# ── Data loading & normalisation ───────────────────────────────────────────────
def load_and_normalize():
    X_train = np.load(TRAIN_SUB01).astype(np.float32)  # (16540, 17, 200)
    Y_train = np.load(TRAIN_SUB03).astype(np.float32)
    X_test  = np.load(TEST_SUB01).astype(np.float32)   # (200,   17, 200)

    # Normalise using training statistics of Sub01 input
    mean = X_train.mean(axis=(0, 2), keepdims=True)   # (1, 17, 1)
    std  = X_train.std(axis=(0, 2), keepdims=True) + 1e-8

    X_train = (X_train - mean) / std
    X_test  = (X_test  - mean) / std

    # Normalise target using Sub03 training stats
    mean3 = Y_train.mean(axis=(0, 2), keepdims=True)
    std3  = Y_train.std(axis=(0, 2), keepdims=True) + 1e-8
    Y_train = (Y_train - mean3) / std3

    return X_train, Y_train, X_test, mean3, std3


# ── Training ───────────────────────────────────────────────────────────────────
def train():
    X_train, Y_train, X_test, mean3, std3 = load_and_normalize()

    X_t = torch.from_numpy(X_train)
    Y_t = torch.from_numpy(Y_train)
    dataset = TensorDataset(X_t, Y_t)
    loader  = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

    model = EEG2EEG(channels=CHANNELS).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * xb.size(0)
        avg = total_loss / len(dataset)
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{EPOCHS}  loss={avg:.6f}")

    # ── Inference ──────────────────────────────────────────────────────────────
    model.eval()
    X_te = torch.from_numpy(X_test).to(DEVICE)
    with torch.no_grad():
        pred_norm = model(X_te).cpu().numpy()  # (200, 17, 200) normalised

    # Denormalise back to Sub03 scale
    pred = pred_norm * std3 + mean3

    np.save(OUTPUT_PATH, pred)
    print(f"Saved predictions → {OUTPUT_PATH}  shape={pred.shape}")


if __name__ == "__main__":
    train()
