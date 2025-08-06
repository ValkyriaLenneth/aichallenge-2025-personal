import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from model import create_model

def load_model(model_path, model_config):
    """Load a trained model from checkpoint."""
    print(f"Loading model from: {model_path}")
    
    # Create model with saved configuration
    model = create_model(**model_config)
    
    # Load state dict
    if model_path.suffix == '.pth':
        # Loading just the state dict
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
    else:
        # Loading full checkpoint
        checkpoint = torch.load(model_path, map_location='cpu')
        model.load_state_dict(checkpoint['model_state_dict'])
    
    return model

def load_test_data(data_dir):
    """Load test data."""
    print("Loading test data...")
    
    x_path = Path(data_dir) / "X_data.npy"
    y_path = Path(data_dir) / "Y_data.npy"
    
    X = np.load(x_path)
    Y = np.load(y_path)
    
    print(f"  + Loaded X_data: {X.shape}")
    print(f"  + Loaded Y_data: {Y.shape}")
    
    X_tensor = torch.FloatTensor(X)
    Y_tensor = torch.FloatTensor(Y)
    
    return X_tensor, Y_tensor

def evaluate_model(model, X, Y, device, batch_size=32):
    """Evaluate model performance."""
    model.eval()
    model = model.to(device)
    
    dataset = TensorDataset(X, Y)
    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    all_predictions = []
    all_targets = []
    total_loss = 0.0
    criterion = nn.MSELoss()
    
    print("Evaluating model...")
    with torch.no_grad():
        for batch_x, batch_y in data_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            predictions = model(batch_x)
            loss = criterion(predictions, batch_y)
            
            all_predictions.append(predictions.cpu().numpy())
            all_targets.append(batch_y.cpu().numpy())
            total_loss += loss.item()
    
    # Concatenate all predictions and targets
    predictions = np.concatenate(all_predictions, axis=0)
    targets = np.concatenate(all_targets, axis=0)
    
    # Calculate metrics
    mse = np.mean((predictions - targets) ** 2)
    mae = np.mean(np.abs(predictions - targets))
    rmse = np.sqrt(mse)
    
    # Calculate R² score
    ss_res = np.sum((targets - predictions) ** 2)
    ss_tot = np.sum((targets - np.mean(targets)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    metrics = {
        'mse': mse,
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'avg_loss': total_loss / len(data_loader)
    }
    
    return predictions, targets, metrics

def plot_predictions_vs_targets(predictions, targets, save_dir, num_samples=5):
    """Plot prediction vs target sequences for sample cases."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Select random samples to visualize
    indices = np.random.choice(len(predictions), min(num_samples, len(predictions)), replace=False)
    
    for i, idx in enumerate(indices):
        plt.figure(figsize=(12, 6))
        
        time_steps = np.arange(predictions.shape[1])
        
        plt.plot(time_steps, targets[idx, :, 0], label='Target', color='blue', linewidth=2)
        plt.plot(time_steps, predictions[idx, :, 0], label='Prediction', color='red', linestyle='--', linewidth=2)
        
        plt.xlabel('Time Steps')
        plt.ylabel('Velocity (m/s)')
        plt.title(f'Velocity Prediction vs Target - Sample {idx}')
        plt.legend()
        plt.grid(True)
        
        save_path = save_dir / f"prediction_sample_{idx}.png"
        plt.savefig(save_path)
        plt.close()
        
        print(f"  + Saved prediction plot: {save_path}")

def plot_error_distribution(predictions, targets, save_dir):
    """Plot error distribution."""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    errors = predictions - targets
    errors_flat = errors.flatten()
    
    plt.figure(figsize=(12, 8))
    
    # Subplot 1: Error histogram
    plt.subplot(2, 2, 1)
    plt.hist(errors_flat, bins=50, alpha=0.7, color='blue')
    plt.xlabel('Prediction Error (m/s)')
    plt.ylabel('Frequency')
    plt.title('Error Distribution')
    plt.grid(True)
    
    # Subplot 2: Error vs target value
    plt.subplot(2, 2, 2)
    targets_flat = targets.flatten()
    plt.scatter(targets_flat[::100], errors_flat[::100], alpha=0.5, s=1)  # Sample every 100th point
    plt.xlabel('Target Velocity (m/s)')
    plt.ylabel('Prediction Error (m/s)')
    plt.title('Error vs Target Value')
    plt.grid(True)
    
    # Subplot 3: Absolute error vs target
    plt.subplot(2, 2, 3)
    abs_errors = np.abs(errors_flat)
    plt.scatter(targets_flat[::100], abs_errors[::100], alpha=0.5, s=1)
    plt.xlabel('Target Velocity (m/s)')
    plt.ylabel('Absolute Error (m/s)')
    plt.title('Absolute Error vs Target Value')
    plt.grid(True)
    
    # Subplot 4: Error statistics by time step
    plt.subplot(2, 2, 4)
    error_by_timestep = np.mean(np.abs(errors), axis=0)
    plt.plot(error_by_timestep[:, 0])
    plt.xlabel('Time Step')
    plt.ylabel('Mean Absolute Error (m/s)')
    plt.title('Error by Time Step')
    plt.grid(True)
    
    plt.tight_layout()
    save_path = save_dir / "error_analysis.png"
    plt.savefig(save_path)
    plt.close()
    
    print(f"  + Saved error analysis plot: {save_path}")

def main():
    parser = argparse.ArgumentParser(description="Evaluate trained LSTM model")
    
    parser.add_argument("model_path", type=str, help="Path to trained model (.pth file)")
    parser.add_argument("data_dir", type=str, help="Directory containing test data")
    parser.add_argument("--config_path", type=str, help="Path to model configuration JSON file")
    parser.add_argument("--output_dir", type=str, default="evaluation_output", help="Directory to save evaluation results")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for evaluation")
    parser.add_argument("--num_samples", type=int, default=5, help="Number of prediction samples to plot")
    
    args = parser.parse_args()
    
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load model configuration
    if args.config_path:
        with open(args.config_path, 'r') as f:
            config = json.load(f)
            model_config = {
                'model_type': config.get('model_type', 'simple'),
                'input_size': 13,  # Our feature count
                'hidden_size': config.get('hidden_size', 256),
                'num_layers': config.get('num_layers', 2),
                'output_seq_len': 50,  # Will be updated based on data
                'dropout': config.get('dropout', 0.2)
            }
    else:
        # Default configuration
        model_config = {
            'model_type': 'simple',
            'input_size': 13,
            'hidden_size': 256,
            'num_layers': 2,
            'output_seq_len': 50,
            'dropout': 0.2
        }
    
    # Load test data
    X, Y = load_test_data(args.data_dir)
    
    # Update output sequence length based on actual data
    model_config['output_seq_len'] = Y.shape[1]
    
    # Load model
    model = load_model(Path(args.model_path), model_config)
    
    # Evaluate model
    predictions, targets, metrics = evaluate_model(model, X, Y, device, args.batch_size)
    
    # Print metrics
    print("\nEvaluation Results:")
    print(f"  MSE:  {metrics['mse']:.6f}")
    print(f"  MAE:  {metrics['mae']:.6f}")
    print(f"  RMSE: {metrics['rmse']:.6f}")
    print(f"  R²:   {metrics['r2']:.6f}")
    
    # Save metrics
    with open(output_dir / "evaluation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    plot_predictions_vs_targets(predictions, targets, output_dir / "predictions", args.num_samples)
    plot_error_distribution(predictions, targets, output_dir)
    
    print(f"\nEvaluation completed! Results saved to: {output_dir}")

if __name__ == "__main__":
    main() 