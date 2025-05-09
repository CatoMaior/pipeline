from abc import ABC, abstractmethod
from .utils import calculate_stats

class PerformanceTest(ABC):
    """Base class for performance tests"""

    def __init__(self, name, display_name=None):
        self.name = name
        self.display_name = display_name or name.capitalize()
        self.metrics = {}
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize the metrics dictionary with empty lists"""
        self.metrics = {
            "ram_usages": []
        }

    @abstractmethod
    def run_test(self, *args, **kwargs):
        """Run the test and collect metrics"""
        pass

    def add_metric(self, metric_name, value, collect_metrics=True):
        """Add a metric value to the collection"""
        if not collect_metrics:
            return

        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def get_results(self):
        """Calculate statistics for the collected metrics"""
        precision_map = {
            "rtf": 3,
            "ram_usage": 2,
            "eval_rate": 2
        }

        results = {
            "ram_usage": calculate_stats(self.metrics["ram_usages"],
                                        precision_map.get("ram_usage", 2))
        }

        for metric_name, values in self.metrics.items():
            if metric_name != "ram_usages" and values:
                if metric_name == "rtf_values":
                    base_name = "rtf"
                elif metric_name == "eval_rates":
                    base_name = "eval_rate"
                else:
                    base_name = metric_name.rstrip("s")

                precision = precision_map.get(base_name, 2)

                results[base_name] = calculate_stats(values, precision)

        return results
