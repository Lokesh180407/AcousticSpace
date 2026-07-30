import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import roc_curve, auc, f1_score, precision_score, recall_score, classification_report
import numpy as np
import time

from model import AudioSpoofCNN
from dataset_loader import SpoofDataset

def evaluate_model(
    csv_path,
    checkpoint_path="data/protocols/best_model.pth",
    batch_size=32
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating on device: {device}")
    
    # 1. Load Dataset
    print(f"Loading dataset from: {csv_path}")
    test_dataset = SpoofDataset(csv_path)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    total_test_batches = len(test_loader)
    print(f"Total samples: {len(test_dataset)} | Test batches: {total_test_batches}")
    
    # 2. Load Model
    print(f"Loading model checkpoint from: {checkpoint_path}")
    model = AudioSpoofCNN(n_mels=128, num_classes=2).to(device)
    try:
        model.load_state_dict(torch.load(checkpoint_path, map_location=device))
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    criterion = nn.CrossEntropyLoss()
    model.eval()
    
    test_loss, test_correct, test_total = 0.0, 0, 0
    all_test_labels = []
    all_test_probs = []
    all_test_preds = []
    
    start_time = time.time()
    
    # 3. Evaluation Loop
    print("\nStarting Evaluation...")
    print("-" * 60)
    with torch.no_grad():
        for batch_idx, (features, labels) in enumerate(test_loader, 1):
            features, labels = features.to(device), labels.to(device)
            outputs = model(features)
            loss = criterion(outputs, labels)

            test_loss += loss.item() * features.size(0)
            
            # Probability of 'spoof' (class 1)
            probs = torch.softmax(outputs, dim=1)[:, 1]
            preds = torch.argmax(outputs, dim=1)
            
            test_correct += (preds == labels).sum().item()
            test_total += labels.size(0)

            all_test_labels.extend(labels.cpu().numpy())
            all_test_probs.extend(probs.cpu().numpy())
            all_test_preds.extend(preds.cpu().numpy())

            if batch_idx % 50 == 0 or batch_idx == total_test_batches:
                print(f"  Processed batch {batch_idx}/{total_test_batches}", flush=True)

    test_loss /= test_total
    test_acc = test_correct / test_total
    
    # 4. Calculate Advanced Metrics
    fpr, tpr, thresholds = roc_curve(all_test_labels, all_test_probs, pos_label=1)
    roc_auc = auc(fpr, tpr)
    
    fnr = 1 - tpr
    eer_idx = np.nanargmin(np.absolute((fnr - fpr)))
    eer = fpr[eer_idx]
    eer_threshold = thresholds[eer_idx]
    
    f1 = f1_score(all_test_labels, all_test_preds, zero_division=0)
    precision = precision_score(all_test_labels, all_test_preds, zero_division=0)
    recall = recall_score(all_test_labels, all_test_preds, zero_division=0)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"EVALUATION RESULTS (Completed in {elapsed:.1f}s)")
    print("=" * 60)
    print(f"Loss:                 {test_loss:.4f}")
    print(f"Accuracy:             {test_acc:.4f} ({(test_acc*100):.1f}%)")
    print(f"Equal Error Rate (EER):{eer:.4f} (Threshold: {eer_threshold:.4f})")
    print(f"ROC AUC:              {roc_auc:.4f}")
    print(f"F1 Score:             {f1:.4f}")
    print(f"Precision:            {precision:.4f}")
    print(f"Recall:               {recall:.4f}")
    print("\nClassification Report:")
    print(classification_report(all_test_labels, all_test_preds, target_names=["Bonafide (0)", "Spoof (1)"], zero_division=0))
    print("=" * 60)

if __name__ == "__main__":
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Point this to your test/validation index CSV
    test_csv_path = os.path.join(script_dir, "../data/protocols/asvspoof2021_combined_index_clean.csv")
    
    evaluate_model(
        csv_path=test_csv_path,
        checkpoint_path=os.path.join(script_dir, "../data/protocols/best_model.pth"),
        batch_size=32
    )
