import logging
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Optional

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_production_kmeans(
    X_train: np.ndarray, 
    n_clusters: int = 5, 
    batch_size: int = 1024,
    random_state: int = 42
) -> Tuple[Optional[MiniBatchKMeans], Optional[StandardScaler]]:
    """
    Trains a scalable Mini-Batch K-Means model on standardized data.
    
    Args:
        X_train: Raw feature matrix (n_samples, n_features).
        n_clusters: The target number of 'k' clusters.
        batch_size: Number of samples per batch to keep memory bounds low.
        random_state: Seed for reproducibility.
        
    Returns:
        A tuple containing the trained model and the fitted scaler, or (None, None) if failed.
    """
    try:
        if X_train.size == 0:
            raise ValueError("Input dataset X_train is empty.")

        logging.info(f"Standardizing data with shape {X_train.shape}...")
        # Production rule: ALWAYS scale features for distance-based algorithms
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_train)
        
        logging.info(f"Training MiniBatchKMeans with k={n_clusters}, batch_size={batch_size}...")
        # Use K-Means++ by default, with batching for high-scale memory efficiency
        model = MiniBatchKMeans(
            n_clusters=n_clusters,
            init='k-means++',
            batch_size=batch_size,
            random_state=random_state,
            n_init="auto", # Allows the algorithm to optimize initializations
            reassignment_ratio=0.01 # Helps handle centers that aren't getting data
        )
        
        model.fit(X_scaled)
        logging.info(f"Model converged in {model.n_iter_} iterations. Final Inertia: {model.inertia_:.2f}")
        
        return model, scaler

    except Exception as e:
        logging.error(f"Failed to train K-Means model: {str(e)}")
        return None, None

# Example Usage:
# dummy_data = np.random.rand(100000, 50) # 100k rows, 50 features
# model, scaler = train_production_kmeans(dummy_data, n_clusters=10)