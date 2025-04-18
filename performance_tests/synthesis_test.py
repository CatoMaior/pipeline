from .base_test import PerformanceTest
from core.synthesizer import get_stats as get_synth_stats

class SynthesisTest(PerformanceTest):
    def __init__(self):
        super().__init__("synthesis", "Synthesis (piper)")
        self.metrics["rtf_values"] = []

    def run_test(self, text, output_file, collect_metrics=True):
        result = get_synth_stats(text, output_file)

        # Check if needed keys exist in the result before accessing them
        if "ram_usage_mb" in result:
            self.add_metric("ram_usages", result["ram_usage_mb"], collect_metrics)
        if "real_time_factor" in result:
            self.add_metric("rtf_values", result["real_time_factor"], collect_metrics)

        return result
