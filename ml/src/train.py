import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import time
from pathlib import Path

from model import AudioSpoofCNN
from dataset_loader import SpoofDataset


def train_model(
    csv_path,
    epochs=10,
    batch_size=16,
    learning_rate=1e-3,
    val_split=0.15,
    checkpoint_path="ml/data/protocols/best_model.pth",
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # --- Load dataset and split into train/val ---
    full_dataset = SpoofDataset(csv_path)
    val_size = int(len(full_dataset) * val_split)
    train_size = len(full_dataset) - val_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    print(f"Total samples: {len(full_dataset)} | Train: {train_size} | Val: {val_size}")

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # --- Model, loss, optimizer ---
    model = AudioSpoofCNN(n_mels=128, num_classes=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        # --- Training phase ---
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0
        start_time = time.time()

        for features, labels in train_loader:
            features, labels = features.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * features.size(0)
            preds = torch.argmax(outputs, dim=1)
            train_correct += (preds == labels).sum().item()
            train_total += labels.size(0)

        train_loss /= train_total
        train_acc = train_correct / train_total

        # --- Validation phase ---
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for features, labels in val_loader:
                features, labels = features.to(device), labels.to(device)
                outputs = model(features)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * features.size(0)
                preds = torch.argmax(outputs, dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_loss /= val_total
        val_acc = val_correct / val_total
        elapsed = time.time() - start_time

        print(
            f"Epoch {epoch}/{epochs} | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
            f"Time: {elapsed:.1f}s"
        )

        # --- Save best model ---
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), checkpoint_path)
            print(f"  -> New best model saved (val_acc={val_acc:.4f})")

    print(f"\nTraining complete. Best validation accuracy: {best_val_acc:.4f}")
    print(f"Best model saved to: {checkpoint_path}")


if __name__ == "__main__":
    # --- IMPORTANT: update this path to your real ASVspoof CSV ---
    csv_path = "ml/data/protocols/asvspoof/asvspoof2021_la_index.csv"

    train_model(
        csv_path=csv_path,
        epochs=10,
        batch_size=16,
        learning_rate=1e-3,
    )