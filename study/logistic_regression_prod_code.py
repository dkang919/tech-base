import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def train_production_logreg(X: pd.DataFrame, y: pd.Series):
    """
    Trains a robust Logistic Regression model with scaling and L2 regularization.
    Returns the model and the interpretation of feature importance.
    """
    # 1. Scaling is MANDATORY for Regularized Logistic Regression
    # Without scaling, the regularization penalty unfairly crushes large-value features.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 2. Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 3. Initialize Model (L2 Penalty is default)
    # C is the inverse of regularization strength. Smaller C = Stronger Regularization.
    model = LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', max_iter=1000)
    
    logging.info("Training Logistic Regression Model...")
    model.fit(X_train, y_train)
    
    # 4. Evaluation
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred)
    logging.info(f"\n{report}")
    
    # 5. Extracting Business Insights (Odds Ratios)
    # Coefficients are in log-odds. We exponentiate them to get Odds Ratios.
    feature_importance = pd.DataFrame({
        'Feature': X.columns,
        'Coefficient (Log-Odds)': model.coef_[0],
        'Odds Ratio': np.exp(model.coef_[0])
    })
    
    # Sort by impact
    feature_importance = feature_importance.sort_values(
        by='Coefficient (Log-Odds)', key=abs, ascending=False
    )
    
    return model, feature_importance

# --- Hypothetical Usage ---
# df = pd.read_csv("customer_churn.csv")
# model, importance = train_production_logreg(df.drop('Churn', axis=1), df['Churn'])
# print(importance.head())