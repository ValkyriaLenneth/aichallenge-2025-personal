import argparse
import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
from pathlib import Path
import json
from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from model import create_model

def load_data(data_dir):
    """Load and prepare training data."""
    print("Loading training data...")
    
    x_path = Path(data_dir) / "X_data.npy"
    y_path = Path(data_dir) / "Y_data.npy"
    
    if not x_path.exists() or not y_path.exists():
        raise FileNotFoundError(f"Data files not found in {data_dir}")
    
    X = np.load(x_path)
    Y = np.load(y_path)
    
    print(f"  + Loaded X_data: {X.shape}")
    print(f"  + Loaded Y_data: {Y.shape}")
    
    # Convert to PyTorch tensors
    X_tensor = torch.FloatTensor(X)
    Y_tensor = torch.FloatTensor(Y)
    
    return X_tensor, Y_tensor

def create_data_loaders(X, Y, batch_size=32, train_split=0.8, val_split=0.1):
    """Create train, validation, and test data loaders."""
    dataset = TensorDataset(X, Y)
    
    # Calculate split sizes
    total_size = len(dataset)
    train_size = int(train_split * total_size)
    val_size = int(val_split * total_size)
    test_size = total_size - train_size - val_size
    
    # Split dataset
    train_dataset, val_dataset, test_dataset = random_split(
        dataset, [train_size, val_size, test_size]
    )
    
    print(f"Data split: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)}")
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    return train_loader, val_loader, test_loader

def train_epoch(model, train_loader, criterion, optimizer, device):
    """Train the model for one epoch."""
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    progress_bar = tqdm(train_loader, desc="Training", leave=False)
    
    for batch_x, batch_y in progress_bar:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward pass
        predictions = model(batch_x)
        loss = criterion(predictions, batch_y)
        
        # Backward pass
        loss.backward()
        
        # Gradient clipping to prevent exploding gradients
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        # Update weights
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        
        # Update progress bar
        progress_bar.set_postfix({"Loss": f"{loss.item():.4f}"})
    
    return total_loss / num_batches

def evaluate(model, data_loader, criterion, device):
    """Evaluate the model."""
    model.eval()
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for batch_x, batch_y in data_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            predictions = model(batch_x)
            loss = criterion(predictions, batch_y)
            
            total_loss += loss.item()
            num_batches += 1
    
    return total_loss / num_batches

def save_checkpoint(model, optimizer, epoch, train_loss, val_loss, save_dir):
    """Save model checkpoint."""
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'train_loss': train_loss,
        'val_loss': val_loss,
    }
    
    save_path = Path(save_dir) / f"checkpoint_epoch_{epoch}.pth"
    torch.save(checkpoint, save_path)
    print(f"  + Saved checkpoint: {save_path}")

def plot_training_history(train_losses, val_losses, save_dir):
    """Plot and save training history."""
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label="Training Loss")
    plt.plot(val_losses, label="Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training History")
    plt.legend()
    plt.grid(True)
    
    save_path = Path(save_dir) / "training_history.png"
    plt.savefig(save_path)
    plt.close()
    print(f"  + Saved training history plot: {save_path}")

def train_model(args):
    """Main training function."""
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save training arguments
    with open(output_dir / "training_args.json", "w") as f:
        json.dump(vars(args), f, indent=2)
    
    # Load data
    X, Y = load_data(args.data_dir)
    train_loader, val_loader, test_loader = create_data_loaders(
        X, Y, batch_size=args.batch_size, train_split=args.train_split, val_split=args.val_split
    )
    
    # Create model
    model_kwargs = {
        'input_size': X.shape[2],  # number of features
        'hidden_size': args.hidden_size,
        'num_layers': args.num_layers,
        'output_seq_len': Y.shape[1],  # output sequence length
        'dropout': args.dropout
    }
    
    model = create_model(args.model_type, **model_kwargs)
    model = model.to(device)
    
    # Loss function and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.7, patience=5
    )
    
    # Training loop
    print(f"\nStarting training for {args.epochs} epochs...")
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        
        # Train
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # Validate
        val_loss = evaluate(model, val_loader, criterion, device)
        
        # Update learning rate
        scheduler.step(val_loss)
        
        # Save losses
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        
        print(f"  Train Loss: {train_loss:.6f}")
        print(f"  Val Loss:   {val_loss:.6f}")
        
        # Save checkpoint if this is the best model so far
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            save_checkpoint(model, optimizer, epoch + 1, train_loss, val_loss, output_dir)
            
            # Also save as "best_model.pth"
            torch.save(model.state_dict(), output_dir / "best_model.pth")
            print(f"  + New best model saved!")
        
        # Save checkpoint every few epochs
        if (epoch + 1) % args.save_interval == 0:
            save_checkpoint(model, optimizer, epoch + 1, train_loss, val_loss, output_dir)
    
    # Evaluate on test set
    print(f"\nEvaluating on test set...")
    test_loss = evaluate(model, test_loader, criterion, device)
    print(f"Test Loss: {test_loss:.6f}")
    
    # Save final results
    results = {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'test_loss': test_loss,
        'best_val_loss': best_val_loss,
        'final_epoch': args.epochs
    }
    
    with open(output_dir / "training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Plot training history
    plot_training_history(train_losses, val_losses, output_dir)
    
    print(f"\nTraining completed! Results saved to: {output_dir}")
    return model, results

def main():
    parser = argparse.ArgumentParser(description="Train LSTM model for velocity prediction")
    
    # Data arguments
    parser.add_argument("data_dir", type=str, help="Directory containing X_data.npy and Y_data.npy")
    parser.add_argument("--output_dir", type=str, default="training_output", help="Directory to save outputs")
    
    # Model arguments
    parser.add_argument("--model_type", type=str, default="simple", choices=["simple", "advanced"], 
                        help="Type of model to use")
    parser.add_argument("--hidden_size", type=int, default=256, help="LSTM hidden size")
    parser.add_argument("--num_layers", type=int, default=2, help="Number of LSTM layers")
    parser.add_argument("--dropout", type=float, default=0.2, help="Dropout rate")
    
    # Training arguments
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=1e-5, help="Weight decay")
    
    # Data split arguments
    parser.add_argument("--train_split", type=float, default=0.8, help="Training data ratio")
    parser.add_argument("--val_split", type=float, default=0.1, help="Validation data ratio")
    
    # Other arguments
    parser.add_argument("--save_interval", type=int, default=10, help="Save checkpoint every N epochs")
    
    args = parser.parse_args()
    
    # Train the model
    model, results = train_model(args)
    
    print(f"Training completed successfully!")
    print(f"Best validation loss: {results['best_val_loss']:.6f}")
    print(f"Final test loss: {results['test_loss']:.6f}")

if __name__ == "__main__":
    main() 