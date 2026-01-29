import pandas as pd
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def train_interpretable_tree(X: pd.DataFrame, y: pd.Series):
    """
    Trains a Decision Tree optimized for interpretability (limited depth).
    """
    
    # 1. Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # 2. Initialize Model with Constraints (The Engineer's Touch)
    # max_depth=4: Deep enough to learn patterns, shallow enough to read.
    # min_samples_leaf=10: Prevents the model from chasing outliers.
    model = DecisionTreeClassifier(
        criterion='gini',
        max_depth=4, 
        min_samples_leaf=10,
        random_state=42
    )
    
    logging.info("Training Constrained Decision Tree...")
    model.fit(X_train, y_train)
    
    # 3. Evaluation
    y_pred = model.predict(X_test)
    logging.info(f"Performance:\n{classification_report(y_test, y_pred)}")
    
    # 4. Feature Importance
    # Trees naturally provide feature importance based on how much they reduce impurity.
    feature_importance = pd.DataFrame({
        'Feature': X.columns,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    return model, feature_importance

def visualize_tree_logic(model, feature_names, class_names):
    """
    Visualizes the decision logic. 
    In production, we often export this as a PDF for Legal/Compliance teams.
    """
    plt.figure(figsize=(20, 10))
    plot_tree(
        model, 
        feature_names=feature_names, 
        class_names=class_names, 
        filled=True, 
        rounded=True, 
        fontsize=10
    )
    plt.title("Decision Tree Logic Flow")
    plt.show()

# --- Hypothetical Usage ---
# model, importance = train_interpretable_tree(X_data, y_data)
# visualize_tree_logic(model, X_data.columns, ['Not Fraud', 'Fraud'])