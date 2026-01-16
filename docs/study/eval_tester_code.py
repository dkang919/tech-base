import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_score, recall_score
import logging

# Configure production logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ModelEvaluator:
    """
    A production-ready evaluator that handles edge cases and 
    computes business-critical metrics.
    """
    
    @staticmethod
    def evaluate_regression(y_true: np.array, y_pred: np.array) -> dict:
        """
        Computes regression metrics with safety checks.
        """
        if len(y_true) == 0:
            logging.error("Empty dataset provided for evaluation.")
            return {}

        try:
            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            
            # Engineer's Check: Calculate 'Mean Absolute Percentage Error' (MAPE) 
            # Useful for explaining error in % terms to business stakeholders.
            # We add a small epsilon to avoid division by zero.
            epsilon = 1e-10
            mape = np.mean(np.abs((y_true - y_pred) / (y_true + epsilon))) * 100
            
            return {"MAE": mae, "RMSE": rmse, "MAPE_%": mape}
            
        except Exception as e:
            logging.error(f"Failed to compute regression metrics: {e}")
            return {}

    @staticmethod
    def evaluate_classification(y_true: np.array, y_pred: np.array) -> dict:
        """
        Computes classification metrics focusing on the Precision-Recall tradeoff.
        """
        try:
            # specifically handling zero_division to avoid warnings in logs
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            
            # F1 Score manual calc to show understanding (or use sklearn f1_score)
            if (precision + recall) == 0:
                f1 = 0.0
            else:
                f1 = 2 * (precision * recall) / (precision + recall)
                
            return {
                "Precision": precision, 
                "Recall": recall, 
                "F1_Score": f1
            }
        except Exception as e:
            logging.error(f"Failed to compute classification metrics: {e}")
            return {}

# --- Example Usage ---
if __name__ == "__main__":
    # Simulate a "Production" run
    actuals = np.array([100, 150, 200, 250])
    predictions = np.array([110, 140, 210, 245])
    
    metrics = ModelEvaluator.evaluate_regression(actuals, predictions)
    logging.info(f"Regression Performance: {metrics}")