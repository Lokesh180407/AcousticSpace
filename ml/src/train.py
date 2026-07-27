import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import time
import sys
from pathlib import Path

from model import AudioSpoofCNN
from dataset_loader import SpoofDataset


def train_model(
    csv_path,
    epochs=10,
    batch_size=32,
    learning_rate=1e-3,
    val_split=0.15,
    checkpoint_path="data/protocols/best_model.pth",
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

    total_train_batches = len(train_loader)
    total_val_batches = len(val_loader)
    print(f"Train batches/epoch: {total_train_batches} | Val batches/epoch: {total_val_batches}")
    print("Starting training...")
    print("----------------------------------------------------------------------")

    # --- Model, loss, optimizer ---
    model = AudioSpoofCNN(n_mels=128, num_classes=2).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    from sklearn.metrics import roc_curve, auc, f1_score, precision_score, recall_score
    import numpy as np

    # Model saving setup
    best_eer = float("inf")  # Lower EER is better

    for epoch in range(1, epochs + 1):
        # --- Training phase ---
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0
        epoch_start = time.time()

        for batch_idx, (features, labels) in enumerate(train_loader, 1):
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

            # Progress log every 100 batches
            if batch_idx % 100 == 0 or batch_idx == total_train_batches:
                elapsed = time.time() - epoch_start
                batches_per_sec = batch_idx / elapsed if elapsed > 0 else 0
                remaining = (total_train_batches - batch_idx) / batches_per_sec if batches_per_sec > 0 else 0
                running_acc = train_correct / train_total
                running_loss = train_loss / train_total
                print(
                    f"  Epoch {epoch}/{epochs} | "
                    f"Batch {batch_idx}/{total_train_batches} | "
                    f"Loss: {running_loss:.4f} | Acc: {running_acc:.4f} | "
                    f"ETA: {remaining:.0f}s",
                    flush=True,
                )

        train_loss /= train_total
        train_acc = train_correct / train_total

        # --- Validation phase ---
        print(f"  Validating...", flush=True)
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        
        all_val_labels = []
        all_val_probs = []
        all_val_preds = []

        with torch.no_grad():
            for batch_idx, (features, labels) in enumerate(val_loader, 1):
                features, labels = features.to(device), labels.to(device)
                outputs = model(features)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * features.size(0)
                
                probs = torch.softmax(outputs, dim=1)[:, 1] # Probability of 'spoof' (class 1)
                preds = torch.argmax(outputs, dim=1)
                
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

                all_val_labels.extend(labels.cpu().numpy())
                all_val_probs.extend(probs.cpu().numpy())
                all_val_preds.extend(preds.cpu().numpy())

                if batch_idx % 200 == 0:
                    print(f"    Val batch {batch_idx}/{total_val_batches}", flush=True)

        val_loss /= val_total
        val_acc = val_correct / val_total
        
        # Calculate Advanced Metrics
        fpr, tpr, thresholds = roc_curve(all_val_labels, all_val_probs, pos_label=1)
        roc_auc = auc(fpr, tpr)
        
        # Calculate EER (Equal Error Rate) - the point where False Positive Rate == False Negative Rate (1 - TPR)
        fnr = 1 - tpr
        eer_threshold = thresholds[np.nanargmin(np.absolute((fnr - fpr)))]
        eer = fpr[np.nanargmin(np.absolute((fnr - fpr)))]
        
        f1 = f1_score(all_val_labels, all_val_preds, zero_division=0)
        precision = precision_score(all_val_labels, all_val_preds, zero_division=0)
        recall = recall_score(all_val_labels, all_val_preds, zero_division=0)

        elapsed = time.time() - epoch_start

        print(f"\n----------------------------------------------------------------------")
        print(
            f"  EPOCH {epoch}/{epochs} COMPLETE | Time: {elapsed:.1f}s\n"
            f"  [Train] Loss: {train_loss:.4f} | Acc: {train_acc:.4f}\n"
            f"  [Valid] Loss: {val_loss:.4f} | Acc: {val_acc:.4f}\n"
            f"  [Advanced Metrics] EER: {eer:.4f} | AUC: {roc_auc:.4f} | F1: {f1:.4f} | Prec: {precision:.4f} | Rec: {recall:.4f}"
        )

        # --- Save best model based on EER ---
        if eer < best_eer:
            best_eer = eer
            Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), checkpoint_path)
            print(f"  -> New best model saved! (EER improved to {eer:.4f})")

        print(f"----------------------------------------------------------------------\n")

    print(f"\nTraining complete. Best validation EER: {best_eer:.4f}")
    print(f"Best model saved to: {checkpoint_path}")


if __name__ == "__main__":
    # --- IMPORTANT: update this path to your real ASVspoof CSV ---
    csv_path = "data/protocols/asvspoof2021_combined_index_clean.csv"

    train_model(
        csv_path=csv_path,
        epochs=10,
        batch_size=32,
        learning_rate=1e-3,
    )