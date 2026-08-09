import torch
import torch.nn as nn
import torch.nn.functional as F
try:
    from transformers import ASTForAudioClassification, ASTConfig
except ImportError:
    pass # transformers will be required for AST


class AudioSpoofCNN(nn.Module):
    """
    Baseline CNN classifier for bonafide vs spoof detection.
    Takes a log-mel spectrogram as input, outputs binary classification logits.
    Input shape expected: (batch_size, 1, n_mels, time_frames)
    """

    def __init__(self, n_mels=128, num_classes=2):
        super(AudioSpoofCNN, self).__init__()

        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.pool1 = nn.MaxPool2d(2)

        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(32)
        self.pool2 = nn.MaxPool2d(2)

        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        self.pool3 = nn.MaxPool2d(2)

        # Adaptive pooling handles variable-length audio (different time_frames)
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))

        self.fc1 = nn.Linear(64, 32)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(32, num_classes)

    def forward(self, x):
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))

        x = self.global_pool(x)
        x = x.view(x.size(0), -1)  # flatten to (batch_size, 64)

        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)  # raw logits, apply softmax/argmax outside

        return x


class AudioSpoofAST(nn.Module):
    """
    HuggingFace Audio Spectrogram Transformer (AST) for spoof detection.
    Pre-trained weights are fine-tuned for bonafide vs spoof classification.
    """
    def __init__(self, num_classes=2, pretrained=False):
        super(AudioSpoofAST, self).__init__()
        
        # Load AST config
        # Default AST uses 128 mel bins and max 1024 frames. 
        self.config = ASTConfig(num_labels=num_classes)
        
        if pretrained:
            try:
                self.ast = ASTForAudioClassification.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593", num_labels=num_classes, ignore_mismatched_sizes=True)
            except Exception:
                self.ast = ASTForAudioClassification(self.config)
        else:
            self.ast = ASTForAudioClassification(self.config)

    def forward(self, x):
        # x is (batch_size, 1, n_mels, time_frames)
        # AST expects (batch_size, time_frames, n_mels)
        x = x.squeeze(1).transpose(1, 2)
        
        outputs = self.ast(x)
        # return logits
        return outputs.logits


if __name__ == "__main__":
    # Sanity check: does the model run and produce correctly shaped output?
    model = AudioSpoofCNN(n_mels=128, num_classes=2)
    print(model)

    # Simulate a batch of 4 spectrograms, shape (batch, channel, n_mels, time_frames)
    dummy_input = torch.randn(4, 1, 128, 605)  # 605 matches your real_speech sample's time frames
    output = model(dummy_input)

    print(f"\nInput shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Output (raw logits):\n{output}")

    probs = F.softmax(output, dim=1)
    print(f"\nOutput (probabilities):\n{probs}")
    print(f"Predicted classes: {torch.argmax(probs, dim=1)}")