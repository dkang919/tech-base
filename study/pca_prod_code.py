import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_breast_cancer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def apply_production_pca(X: pd.DataFrame, variance_threshold: float = 0.95):
    """
    Applies PCA to a dataset, automatically selecting the number of components
    needed to explain 'variance_threshold' (e.g., 95%) of the data.
    """
    
    # 1. MANDATORY Scaling
    # The Principal Engineer's Rule: Never run PCA on raw data.
    logging.info("Standardizing data...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 2. Fit PCA without limiting components first (to see the full spectrum)
    pca_full = PCA()
    pca_full.fit(X_scaled)
    
    # 3. Determine optimal 'k' components
    # cumsum() gives us the cumulative variance explained (e.g., [0.4, 0.6, 0.75...])
    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    
    # Find the index where cumulative variance first exceeds the threshold
    # np.argmax returns the first index that is True
    n_components = np.argmax(cumulative_variance >= variance_threshold) + 1
    
    logging.info(f"Original Feature Count: {X.shape[1]}")
    logging.info(f"Components needed for {variance_threshold*100}% variance: {n_components}")
    
    # 4. Apply Final PCA
    pca_final = PCA(n_components=n_components)
    X_pca = pca_final.fit_transform(X_scaled)
    
    return pca_final, X_pca, cumulative_variance

# --- Hypothetical Usage ---
# We use the Breast Cancer dataset (30 features)
data = load_breast_cancer()
df = pd.DataFrame(data.data, columns=data.feature_names)

model, transformed_data, variance_curve = apply_production_pca(df, variance_threshold=0.95)

# Example output log:
# "Original Feature Count: 30"
# "Components needed for 95.0% variance: 10"
# (We compressed the data by 66% while keeping 95% of the information!)