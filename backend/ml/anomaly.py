import numpy as np
from sklearn.ensemble import IsolationForest

class AnomalyEngine:
    def __init__(self):
        # Using Isolation Forest for multivariate anomaly detection
        self.model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        self.warmup()

    def warmup(self):
        # Generate synthetic "healthy" physics residuals for EGT and RPM
        # EGT residual ~ N(0, 5°C), RPM residual ~ N(0, 20 RPM)
        np.random.seed(42)
        healthy_egt_res = np.random.normal(0, 5, 1000)
        healthy_rpm_res = np.random.normal(0, 20, 1000)
        X = np.column_stack((healthy_egt_res, healthy_rpm_res))
        self.model.fit(X)

    def score(self, egt_residual, rpm_residual):
        X = np.array([[egt_residual, rpm_residual]])
        # decision_function returns > 0 for normal, < 0 for anomaly
        raw_score = self.model.decision_function(X)[0]
        
        # Convert raw score to a normalized anomaly probability (0.0 to 1.0)
        # Higher score = more anomalous
        anomaly_prob = max(0, min(1, 0.5 - (raw_score * 5)))
        return anomaly_prob
