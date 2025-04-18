from .base_test import PerformanceTest
from .ollama_test_utils import get_stats as get_ollama_stats

class LLMInferenceTest(PerformanceTest):
    def __init__(self, model_name):
        super().__init__("llm_inference", f"LLM inference ({model_name})")
        self.model_name = model_name
        self.metrics["eval_rates"] = []

    def run_test(self, collect_metrics=True):
        result = get_ollama_stats(self.model_name)
        self.add_metric("ram_usages", result["ram_usage_mb"], collect_metrics)
        self.add_metric("eval_rates", result.get("eval_rate", 0), collect_metrics)
        return result
