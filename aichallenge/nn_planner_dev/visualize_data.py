import argparse
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import random

# Define the names of our 13 features in the correct order
FEATURE_NAMES = [
    # Ego State
    "current_velocity_x",
    "current_angular_velocity_z",
    # Path-Relative
    "distance_from_centerline",
    "heading_error",
    # Curvature Fingerprint
    "curvature_at_-25m",
    "curvature_at_-15m",
    "curvature_at_-10m",
    "curvature_at_-5m",
    "curvature_at_0m",
    "curvature_at_+5m",
    "curvature_at_+10m",
    "curvature_at_+15m",
    "curvature_at_+25m",
]

# Distances for the y-axis of the curvature heatmap
CURVATURE_DISTANCES = [-25, -15, -10, -5, 0, 5, 10, 15, 25]

def visualize_sample(X_data, Y_data, sample_idx, data_path: Path):
    """
    Loads and visualizes a single sample from the processed data.
    """
    if sample_idx >= len(X_data):
        print(f"Error: sample_idx {sample_idx} is out of bounds. Max index is {len(X_data) - 1}.")
        return

    # Extract the single sample
    x_sample = X_data[sample_idx]  # Shape: (input_seq_len, num_features)
    y_sample = Y_data[sample_idx]  # Shape: (output_seq_len, 1)

    print(f"Visualizing sample #{sample_idx}")
    print(f"  - Input shape (X): {x_sample.shape}")
    print(f"  - Output shape (Y): {y_sample.shape}")

    # Create a figure with 4 subplots
    fig, axs = plt.subplots(4, 1, figsize=(12, 18), gridspec_kw={'height_ratios': [2, 2, 3, 2]})
    fig.suptitle(f"Data Visualization for Sample #{sample_idx}", fontsize=16)
    
    input_time_steps = np.arange(x_sample.shape[0])
    output_time_steps = np.arange(y_sample.shape[0])

    # --- Subplot 1: Ego State Features ---
    axs[0].set_title("Ego State Features (Input)")
    axs[0].plot(input_time_steps, x_sample[:, 0], label=FEATURE_NAMES[0] + " (m/s)")
    ax0_twin = axs[0].twinx() # Create a second y-axis
    ax0_twin.plot(input_time_steps, x_sample[:, 1], label=FEATURE_NAMES[1] + " (rad/s)", color='orange')
    axs[0].set_xlabel("Time Steps (Input Sequence)")
    axs[0].set_ylabel("Velocity", color='tab:blue')
    ax0_twin.set_ylabel("Angular Velocity", color='orange')
    axs[0].legend(loc='upper left')
    ax0_twin.legend(loc='upper right')
    axs[0].grid(True)

    # --- Subplot 2: Path-Relative Features ---
    axs[1].set_title("Path-Relative Features (Input)")
    axs[1].plot(input_time_steps, x_sample[:, 2], label=FEATURE_NAMES[2] + " (m)")
    ax1_twin = axs[1].twinx()
    ax1_twin.plot(input_time_steps, x_sample[:, 3], label=FEATURE_NAMES[3] + " (rad)", color='orange')
    axs[1].set_xlabel("Time Steps (Input Sequence)")
    axs[1].set_ylabel("Distance Error", color='tab:blue')
    ax1_twin.set_ylabel("Heading Error", color='orange')
    axs[1].legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    axs[1].grid(True)

    # --- Subplot 3: Curvature Fingerprint Heatmap ---
    axs[2].set_title("Path Curvature 'Fingerprint' (Input)")
    curvature_data = x_sample[:, 4:].T # Transpose to get (9, input_seq_len)
    im = axs[2].imshow(curvature_data, aspect='auto', cmap='coolwarm', interpolation='nearest')
    axs[2].set_xlabel("Time Steps (Input Sequence)")
    axs[2].set_ylabel("Position Relative to Vehicle (m)")
    axs[2].set_yticks(np.arange(len(CURVATURE_DISTANCES)))
    axs[2].set_yticklabels(CURVATURE_DISTANCES)
    fig.colorbar(im, ax=axs[2], label="Curvature (1/m)\n(Blue: Left Turn, Red: Right Turn)")

    # --- Subplot 4: Target Velocity ---
    axs[3].set_title("Target Velocity (Output/Label)")
    axs[3].plot(output_time_steps, y_sample[:, 0], label="Target Velocity (m/s)", color='green')
    axs[3].set_xlabel("Time Steps (Output Sequence)")
    axs[3].set_ylabel("Velocity (m/s)")
    axs[3].legend()
    axs[3].grid(True)
    axs[3].set_ylim(bottom=0)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # Save the figure to a file instead of showing a GUI window
    output_path = data_path / "visualizations"
    output_path.mkdir(exist_ok=True)
    save_path = output_path / f"sample_{sample_idx}.png"
    plt.savefig(save_path)
    plt.close(fig) # Close the figure to free up memory
    print(f"  + Visualization saved to: {save_path}")


def main():
    parser = argparse.ArgumentParser(description="Visualize processed training data samples.")
    parser.add_argument("data_path", type=str, help="Path to the directory containing X_data.npy and Y_data.npy.")
    parser.add_argument("--index", type=int, default=None, help="Specific sample index to visualize. If not provided, a random sample is chosen.")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_path)
    x_file = data_dir / "X_data.npy"
    y_file = data_dir / "Y_data.npy"

    if not x_file.exists() or not y_file.exists():
        print(f"Error: Could not find X_data.npy and/or Y_data.npy in '{data_dir}'")
        return

    print("Loading data files...")
    X_data = np.load(x_file)
    Y_data = np.load(y_file)
    print(f"  + Loaded X_data with shape: {X_data.shape}")
    print(f"  + Loaded Y_data with shape: {Y_data.shape}")

    if args.index is None:
        sample_idx = random.randint(0, len(X_data) - 1)
        print(f"No index provided. Choosing a random sample: #{sample_idx}")
    else:
        sample_idx = args.index
    
    visualize_sample(X_data, Y_data, sample_idx, data_dir)

if __name__ == '__main__':
    main() 