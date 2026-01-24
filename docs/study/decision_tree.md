# Decision Trees: The Interpretable "Flowchart" of Machine Learning

**Top-Line Summary:**
A Decision Tree is a non-parametric algorithm that models decisions as a flowchart-like structure. It breaks down a dataset into smaller and smaller subsets while at the same time an associated decision tree is incrementally developed.

* **The Superpower:** It requires almost no data preparation (no scaling/normalization) and is easily visualized.
* **The Kryptonite:** A single tree is extremely prone to overfitting. It will memorize your training data perfectly (high variance) and fail on new data unless you constrain it.

---

## 1. The Intuition: "20 Questions" (The Professor)

Imagine I am thinking of a transaction type, and you have to guess if it is **Fraud**.

1.  **You:** "Is the amount > $10,000?"
2.  **Me:** "Yes."
3.  **You:** "Did the transaction originate in a different country?"
4.  **Me:** "Yes."
5.  **You:** "Fraud!"

The Decision Tree algorithm figures out which question to ask first to separate the data most effectively.



### The Anatomy of a Tree
* **Root Node:** Represents the entire population. The first best question.
* **Decision Node:** A sub-node that splits into further sub-nodes.
* **Leaf Node (Terminal Node):** A node that does not split. It holds the final prediction (e.g., "Fraud").

---

## 2. The Math: How It Chooses the Split

The model tries every possible split on every feature and calculates a metric to see which split makes the resulting child nodes the most "pure."

### Metric A: Gini Impurity (The Industry Standard)
Used by the CART algorithm (Classification and Regression Trees). It measures the likelihood of an incorrect classification of a new instance of a random variable, if that new instance were randomly classified according to the distribution of class labels from the dataset.

$$Gini = 1 - \sum_{i=1}^{C} (p_i)^2$$

* **$p_i$**: The probability of an item belonging to class $i$.
* **Gini = 0**: Perfect purity (all items in the node are the same class).
* **Gini = 0.5**: Maximum impurity (for binary classification, a 50/50 split).

**The Goal:** We want the split that results in the **lowest weighted average Gini Impurity** for the child nodes.

### Metric B: Entropy & Information Gain
Derived from Information Theory. Entropy measures the amount of "disorder" or uncertainty.

$$Entropy = - \sum_{i=1}^{C} p_i \log_2(p_i)$$

* **Entropy = 0**: No disorder (Perfect purity).
* **Information Gain**: The reduction in entropy after a dataset is split on an attribute. The tree maximizes Information Gain.

!!! note "Professor's Note"
    In practice, **Gini and Entropy produce very similar trees 95% of the time**. Gini is slightly faster to compute because it doesn't use logarithms.

---

## 3. Regression Trees (Predicting Numbers)
If you are predicting a continuous value (like House Price) instead of a category:

* The metric is not Gini, but **MSE (Variance) Reduction**.
* The tree splits to minimize the variance of the values in the child nodes.
* **Prediction:** The prediction at the leaf node is the **Average (Mean)** of all training samples in that leaf.

---

## 4. Engineering & Production Reality (The Principal Engineer)

### A. The Overfitting Trap
A Decision Tree will keep splitting until every leaf is pure. If you have two identical customers but one churned and one didn't, the tree will find some obscure noise ("User clicked button at 4:02 PM vs 4:03 PM") to distinguish them.

* **Result:** 100% Training Accuracy, 60% Test Accuracy.
* **The Fix:** Pruning (Constraints).

### B. Crucial Hyperparameters (Your Knobs & Dials)
When deploying a tree, you must set these:

* **`max_depth`**: The maximum height of the tree. A depth of 3 to 5 is usually interpretable and generalizable. A depth of 50 is pure noise.
* **`min_samples_split`**: The minimum number of samples required to split an internal node. If set to 100, a node with 50 samples becomes a leaf (stops growing).
* **`min_samples_leaf`**: The minimum samples a leaf node must have. Prevents the tree from creating a leaf for a single outlier.

### C. Feature Scaling is Irrelevant
Unlike Logistic Regression or Neural Networks, Decision Trees do not care about the scale of your data.

* **Feature A:** 0.0 to 1.0
* **Feature B:** $1,000 to $1,000,000

The tree just asks: "Is Feature B > $500,000?" It is strictly orthogonal.