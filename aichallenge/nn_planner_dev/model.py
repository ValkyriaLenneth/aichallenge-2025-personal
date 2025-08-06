import torch
import torch.nn as nn

class VelocityLSTM(nn.Module):
    """
    LSTM model for predicting future velocity sequences based on vehicle state and path features.
    
    Architecture:
    - 2-layer LSTM with 256 hidden units
    - Input: (batch_size, input_seq_len, num_features)
    - Output: (batch_size, output_seq_len, 1)
    """
    
    def __init__(self, input_size=13, hidden_size=256, num_layers=2, output_seq_len=50, dropout=0.2):
        super(VelocityLSTM, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_seq_len = output_seq_len
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Output projection layers
        self.output_projection = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1)
        )
        
    def forward(self, x):
        """
        Forward pass through the model.
        
        Args:
            x: Input tensor of shape (batch_size, input_seq_len, num_features)
            
        Returns:
            output: Predicted velocity sequence of shape (batch_size, output_seq_len, 1)
        """
        batch_size = x.size(0)
        
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(x.device)
        
        # Forward through LSTM
        lstm_out, (hn, cn) = self.lstm(x, (h0, c0))
        
        # We want to predict the future sequence, so we'll use the final hidden state
        # to generate predictions step by step
        predictions = []
        hidden = (hn, cn)
        
        # For autoregressive generation, we'll use a dummy input vector
        # and rely on the hidden state to carry information
        dummy_input = torch.zeros(batch_size, 1, self.input_size).to(x.device)
        current_input = dummy_input
        
        for _ in range(self.output_seq_len):
            # Forward through LSTM with current input and hidden state
            lstm_step_out, hidden = self.lstm(current_input, hidden)
            
            # Project LSTM output to velocity prediction
            pred = self.output_projection(lstm_step_out.squeeze(1))  # Shape: (batch_size, 1)
            predictions.append(pred.unsqueeze(1))  # Shape: (batch_size, 1, 1)
            
            # For the next step, we can either:
            # 1. Use a dummy input (current approach)
            # 2. Create an input that includes the predicted velocity
            # For simplicity, we'll stick with dummy input and rely on hidden state
            current_input = dummy_input
        
        # Concatenate all predictions
        output = torch.cat(predictions, dim=1)  # Shape: (batch_size, output_seq_len, 1)
        
        return output
    
    def predict_step_by_step(self, x):
        """
        Alternative prediction method that generates output step by step.
        Useful for inference and understanding model behavior.
        """
        self.eval()
        with torch.no_grad():
            return self.forward(x)


class SimplerVelocityLSTM(nn.Module):
    """
    A simpler version that directly maps the entire input sequence to output sequence.
    This approach is more straightforward and might work better initially.
    """
    
    def __init__(self, input_size=13, hidden_size=256, num_layers=2, output_seq_len=50, dropout=0.2):
        super(SimplerVelocityLSTM, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_seq_len = output_seq_len
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Direct mapping to output sequence
        self.output_layer = nn.Linear(hidden_size, output_seq_len)
        
    def forward(self, x):
        """
        Forward pass: encode input sequence, then decode to output sequence.
        
        Args:
            x: Input tensor of shape (batch_size, input_seq_len, num_features)
            
        Returns:
            output: Predicted velocity sequence of shape (batch_size, output_seq_len, 1)
        """
        batch_size = x.size(0)
        
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size).to(x.device)
        
        # Forward through LSTM
        lstm_out, _ = self.lstm(x, (h0, c0))
        
        # Use the last output to predict the entire future sequence
        last_output = lstm_out[:, -1, :]  # Shape: (batch_size, hidden_size)
        predictions = self.output_layer(last_output)  # Shape: (batch_size, output_seq_len)
        
        # Reshape to match expected output format
        output = predictions.unsqueeze(-1)  # Shape: (batch_size, output_seq_len, 1)
        
        return output


def count_parameters(model):
    """Count the number of trainable parameters in the model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def create_model(model_type="simple", **kwargs):
    """
    Factory function to create model instances.
    
    Args:
        model_type: Either "simple" or "advanced"
        **kwargs: Additional arguments passed to model constructor
        
    Returns:
        model: PyTorch model instance
    """
    if model_type == "simple":
        model = SimplerVelocityLSTM(**kwargs)
    elif model_type == "advanced":
        model = VelocityLSTM(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    print(f"Created {model_type} model with {count_parameters(model):,} trainable parameters")
    return model


if __name__ == "__main__":
    # Test the models
    batch_size = 8
    input_seq_len = 149
    output_seq_len = 50
    num_features = 13
    
    # Create test input
    x = torch.randn(batch_size, input_seq_len, num_features)
    
    # Test simple model
    print("Testing SimplerVelocityLSTM:")
    simple_model = create_model("simple", output_seq_len=output_seq_len)
    simple_output = simple_model(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {simple_output.shape}")
    
    # Test advanced model
    print("\nTesting VelocityLSTM:")
    advanced_model = create_model("advanced", output_seq_len=output_seq_len)
    advanced_output = advanced_model(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {advanced_output.shape}") 