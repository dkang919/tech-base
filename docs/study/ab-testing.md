# A/B Testing: The Gold Standard of Causality

**Top-Line Summary:**
A/B Testing (or Split Testing) is the application of the scientific method (Randomized Controlled Trials) to product development. In the tech industry, we do not guess; we experiment.

* **The Goal:** Isolate the impact of a specific change (Variable) on a specific metric (Outcome).
* **The Mechanism:** Randomly split users into two groups: **Control** (Group A, sees the old version) and **Treatment** (Group B, sees the new version).
* **The Key:** Since the split is random, the only difference between the groups is your change. Therefore, any difference in metrics is *caused* by your change.

---

## 1. The Mathematical Intuition (The Professor)

### Hypothesis Testing
We start with two hypotheses:
* **Null Hypothesis ($H_0$):** The change does nothing. The conversion rate of A is equal to B ($p_A = p_B$).
* **Alternative Hypothesis ($H_1$):** The change does something. ($p_A \neq p_B$ or $p_B > p_A$).

### The Four Statistical Pillars
To run a valid test, you must define these **before** you start:

1.  **Significance Level ($\alpha$):** Usually 0.05 (5%).
    * The risk of a **Type I Error** (False Positive).
    * *"We claim the new feature is better, but it's actually not."*
2.  **Statistical Power ($1 - \beta$):** Usually 0.80 (80%).
    * The probability of correctly detecting an effect if one exists.
    * $\beta$ is the risk of a **Type II Error** (False Negative: missing a good idea).
3.  **Minimum Detectable Effect (MDE):**
    * The smallest improvement that matters to the business.
    * *Example:* "We only care if conversion improves by at least 1%." If it improves by 0.01%, it's not worth the engineering cost.
4.  **Sample Size ($N$):**
    * Calculated using $\alpha$, Power, and MDE.
    * *Rule:* Smaller MDE requires larger sample size. Detecting a tiny needle requires a huge haystack.

### The Test Statistic (Z-Test)
For conversion rates (proportions), we typically use a **Two-Proportion Z-Test**:

$$Z = \frac{\hat{p}_B - \hat{p}_A}{\sqrt{ \hat{p}_{pool}(1 - \hat{p}_{pool}) (\frac{1}{n_A} + \frac{1}{n_B}) }}$$

If the resulting **p-value is $< \alpha$** (0.05), we reject the Null Hypothesis. The result is "Statistically Significant."

---

## 2. Engineering & Production Reality (The Principal Engineer)

### A. Randomization (The Hashing Trick)
How do we randomly assign 100 million users to Group A or B efficiently? We don't store a database row for each user saying "User1: A". That's too slow.

**We use Hashing:**
1.  Take `User_ID` + `Experiment_Salt` (e.g., "User123" + "CheckoutTest").
2.  Compute a hash (MD5 or SHA256).
3.  Convert to an integer and take **Modulo 100**.
4.  If result < 50: Assign to **Control**. If >= 50: Assign to **Treatment**.

*Benefit:* This is **deterministic** (User123 is always in the same group) and **stateless** (no database lookup needed).

### B. Metric Selection: The Hierarchy
You need more than just one metric.

* **North Star (Primary) Metric:** The goal (e.g., Conversion Rate, Click-Through Rate).
* **Guardrail Metrics:** Things you cannot hurt.
    * *Example:* You increase Clicks by 10% (Great!), but Page Load Latency goes up by 200ms (Bad!). **You must kill the experiment.**
    * *Example:* You increase Revenue, but Unsubscribe Rate spikes.

### C. The "Peeking" Sin
!!! danger "CRITICAL: Do Not Peek"
    **The Scenario:** You run a test for 2 days. P-value is 0.04. You shout "Success!" and stop.
    
    **The Reality:** P-values fluctuate wildly at the start ("Random Walk").
    
    **The Rule:** You must decide the sample size/duration beforehand (e.g., 7 days) and **not look** (or at least not act) until the time is up.

### D. Novelty Effect & Primacy Effect
* **Novelty Effect:** Users click the new button just because it's new. The lift fades after 1 week.
* **Primacy Effect:** Users hate change. Metrics dip initially because they are confused, then recover.

!!! tip "Engineering Fix"
    Run experiments for at least **1-2 full business cycles** (e.g., 2 weeks) to let these effects wash out and capture weekly seasonality (e.g., users behave differently on weekends).

### E. The Final Reality Check
**"Statistical Significance $\neq$ Practical Significance"**

Imagine you test a change on 100 million users (Google scale).
* **Result:** You improved conversion from 2.0% to 2.0001%.
* **P-value:** 0.001 (Highly Significant!).

!!! warning "The Business Question"
    Does that 0.0001% increase cover the cost of maintaining this new code?
    
    If the answer is **No**, you should still **reject the change**, even if the math says it's "significant." Always weigh the lift against the technical debt.