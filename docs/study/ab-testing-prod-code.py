import numpy as np
from scipy import stats
import statsmodels.stats.api as sms
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class ABTestAnalyzer:
    """
    Toolkit for designing and evaluating A/B tests.
    """
    
    @staticmethod
    def calculate_sample_size(baseline_rate, mde, power=0.8, alpha=0.05):
        """
        How many users do we need per group?
        baseline_rate: Current conversion rate (e.g., 0.10 for 10%)
        mde: Minimum Detectable Effect (e.g., 0.02 for 2% absolute lift)
        """
        # Calculate effect size using Cohen's h or arcsin transformation logic
        effect_size = sms.proportion_effectsize(baseline_rate, baseline_rate + mde)
        
        required_n = sms.NormalIndPower().solve_power(
            effect_size, 
            power=power, 
            alpha=alpha, 
            ratio=1
        )
        
        # Round up to nearest whole number
        return int(np.ceil(required_n))

    @staticmethod
    def evaluate_experiment(control_conv, control_n, treatment_conv, treatment_n):
        """
        Evaluates the results using a Z-test.
        """
        # Count of successes (conversions)
        successes = np.array([control_conv, treatment_conv])
        nobs = np.array([control_n, treatment_n])
        
        # Calculate Z-stat and p-value
        stat, pval = sms.proportions_ztest(successes, nobs)
        
        # Calculate Lift
        rate_control = control_conv / control_n
        rate_treatment = treatment_conv / treatment_n
        lift = (rate_treatment - rate_control) / rate_control * 100
        
        return {
            "p_value": pval,
            "z_statistic": stat,
            "lift_percent": lift,
            "significant": pval < 0.05
        }

# --- Hypothetical Usage ---
# Scenario: We have a 10% conversion rate. We want to detect a 1% lift (to 11%).
# 1. Design Phase
n_required = ABTestAnalyzer.calculate_sample_size(0.10, 0.01)
logging.info(f"Design: Need {n_required} users per group.")

# 2. Evaluation Phase (After running the test)
# Suppose we got the users and these results:
results = ABTestAnalyzer.evaluate_experiment(
    control_conv=400, control_n=3900,   # ~10.2%
    treatment_conv=450, treatment_n=3900 # ~11.5%
)

logging.info(f"Results: {results}")
# Output might show p_value < 0.05, meaning the lift is real!