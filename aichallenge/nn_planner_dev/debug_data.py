import numpy as np
import torch

def debug_data():
    """Debug the processed data to understand why loss is 0."""
    print("Loading data for debugging...")
    
    X = np.load("aichallenge/nn_planner_dev/processed_data/X_data.npy")
    Y = np.load("aichallenge/nn_planner_dev/processed_data/Y_data.npy")
    
    print(f"X shape: {X.shape}")
    print(f"Y shape: {Y.shape}")
    
    print("\n=== X Data Statistics ===")
    print(f"X min: {X.min():.6f}")
    print(f"X max: {X.max():.6f}")
    print(f"X mean: {X.mean():.6f}")
    print(f"X std: {X.std():.6f}")
    print(f"X contains NaN: {np.isnan(X).any()}")
    print(f"X contains Inf: {np.isinf(X).any()}")
    
    print("\n=== Y Data Statistics ===")
    print(f"Y min: {Y.min():.6f}")
    print(f"Y max: {Y.max():.6f}")
    print(f"Y mean: {Y.mean():.6f}")
    print(f"Y std: {Y.std():.6f}")
    print(f"Y contains NaN: {np.isnan(Y).any()}")
    print(f"Y contains Inf: {np.isinf(Y).any()}")
    
    # Check if Y is all zeros
    zero_count = np.sum(Y == 0)
    total_count = Y.size
    print(f"Zero values in Y: {zero_count}/{total_count} ({zero_count/total_count*100:.2f}%)")
    
    # Check first few samples
    print(f"\nFirst 5 Y samples:")
    for i in range(min(5, Y.shape[0])):
        print(f"Sample {i}: {Y[i, :5, 0]} (showing first 5 timesteps)")
    
    # Check feature statistics
    print(f"\n=== Feature Statistics (X) ===")
    for i in range(X.shape[2]):
        feature_data = X[:, :, i]
        print(f"Feature {i}: min={feature_data.min():.4f}, max={feature_data.max():.4f}, mean={feature_data.mean():.4f}, std={feature_data.std():.4f}")
    
    # Test model forward pass
    print(f"\n=== Testing Model Forward Pass ===")
    X_tensor = torch.FloatTensor(X[:2])  # Take first 2 samples
    Y_tensor = torch.FloatTensor(Y[:2])
    
    # Import model
    import sys
    sys.path.append('aichallenge/nn_planner_dev')
    from model import create_model
    
    model = create_model("simple", input_size=13, output_seq_len=Y.shape[1])
    model.eval()
    
    with torch.no_grad():
        pred = model(X_tensor)
        print(f"Prediction shape: {pred.shape}")
        print(f"Prediction min: {pred.min():.6f}")
        print(f"Prediction max: {pred.max():.6f}")
        print(f"Prediction mean: {pred.mean():.6f}")
        
        # Calculate loss manually
        import torch.nn as nn
        criterion = nn.MSELoss()
        loss = criterion(pred, Y_tensor)
        print(f"Manual MSE loss: {loss.item():.6f}")

if __name__ == "__main__":
    debug_data() 