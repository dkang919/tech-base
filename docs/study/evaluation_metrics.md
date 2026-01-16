# Machine Learning Metrics: Theory vs. Practice

## Part 1: Regression Metrics (Predicting Continuous Values)
These metrics are used when you are predicting a number (e.g., House Price, Eta for a taxi, Server Latency).

### 1. Mean Absolute Error (MAE)
**The Professor (Theory):**
The arithmetic average of the absolute differences between predicted and actual values. It treats all errors equally.

$$MAE = \frac{1}{n}\sum_{i=1}^{n} |y_i - \hat{y}_i|$$

**The Engineer (Practice):**
* **Why use it?** It is robust to outliers. If your dataset has a few "crazy" values (e.g., a mansion selling for $100M in a neighborhood of $500k homes), MAE won't skew your entire model to fit that one mansion.
* **Production Note:** It is highly interpretable for stakeholders. You can tell a Product Manager: "Our model is off by an average of $5.00."

### 2. Root Mean Squared Error (RMSE)
**The Professor (Theory):**
The square root of the average of squared differences. Because we square the error, larger errors are penalized disproportionately more than small errors.

$$RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$$

**The Engineer (Practice):**
* **Why use it?** In many systems (like self-driving cars or stock trading), one huge mistake is worse than many small ones. RMSE forces the model to care deeply about preventing those huge misses.
* **Pitfall:** If you have noisy data with many outliers, RMSE might force your model to overfit to that noise.

---

## Part 2: Classification Metrics (Predicting Categories)
These are used when predicting a class (e.g., Spam/Not Spam, Fraud/Not Fraud).

### 3. Accuracy
**The Professor (Theory):**
The ratio of correct predictions to total predictions.

$$Accuracy = \frac{TP + TN}{Total \ Examples}$$

**The Engineer (Practice):**
* **The Trap:** Never trust accuracy on imbalanced data.
* **Scenario:** You are building a Fraud Detector. 99.9% of transactions are legit. If you write a code that just says "Not Fraud" for everything, your accuracy is 99.9%. But you caught 0 fraud. The model is useless.

### 4 & 5. Precision & Recall (The Trade-off)
**The Professor (Theory):**
* **Precision:** Of all the instances predicted as positive, how many were actually positive? (Quality).
    $$Precision = \frac{TP}{TP + FP}$$
* **Recall (Sensitivity):** Of all the actual positive instances, how many did we correctly predict? (Quantity).
    $$Recall = \frac{TP}{TP + FN}$$

**The Engineer (Practice):**
You cannot maximize both. You must choose based on business cost.
* **Optimize Precision:** If a False Positive is expensive.
    * *Example:* YouTube Kids Content Filter. You'd rather miss a few bad videos (Low Recall) than accidentally ban a legitimate educational creator (High Precision needed).
* **Optimize Recall:** If a False Negative is dangerous.
    * *Example:* Cancer Screening. It is better to flag a healthy person for a re-check (False Positive) than to tell a sick person they are healthy (False Negative).

### 6. F1 Score
**The Professor (Theory):**
The Harmonic Mean of Precision and Recall. It penalizes extreme values. If either Precision or Recall is 0, the F1 score is 0.

$$F1 = 2 \times \frac{Precision \times Recall}{Precision + Recall}$$

**The Engineer (Practice):**
* **Why use it?** It gives you a single number to compare models when you have uneven class distribution (e.g., 90% class A, 10% class B). It prevents the "Accuracy Trap."

### 7. ROC-AUC (Area Under the Receiver Operating Characteristic Curve)
**The Professor (Theory):**
A plot of True Positive Rate vs. False Positive Rate at all possible classification thresholds. AUC (Area Under Curve) represents the probability that the model ranks a random positive example higher than a random negative example.

**The Engineer (Practice):**
* **Why use it?** It is threshold invariant. It tells you how good the model is generally, before you even decide on a cut-off point (e.g., "Flag fraud if probability > 0.7").
* **Scale:** Standard for comparing models offline before deploying.

### 8. Log Loss (Cross-Entropy Loss)
**The Professor (Theory):**
Measures the performance of a classification model where the prediction input is a probability value between 0 and 1. It heavily penalizes confident wrong predictions.

$$LogLoss = - \frac{1}{N} \sum_{i=1}^{N} [y_i \log(\hat{y}_i) + (1-y_i) \log(1-\hat{y}_i)]$$

**The Engineer (Practice):**
* **Why use it?** Critical for Ad-Tech and Click-Through Rate (CTR) prediction.
* **The Nuance:** Accuracy doesn't care if you predicted 0.51 (barely yes) or 0.99 (definitely yes). Log Loss does. If your model says "99% chance this is a cat" and it's a dog, Log Loss explodes. It forces the model to be calibrated (honest about its uncertainty).