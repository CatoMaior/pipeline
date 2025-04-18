from .base_test import PerformanceTest
from core.transcriber import get_stats as get_trans_stats

class TranscriptionTest(PerformanceTest):
    def __init__(self):
        super().__init__("transcription", "Transcription (moonshine)")
        self.metrics["rtf_values"] = []

    def run_test(self, audio_file, collect_metrics=True):
        result = get_trans_stats(audio_file)
        self.add_metric("ram_usages", result["ram_usage_mb"], collect_metrics)
        self.add_metric("rtf_values", result["real_time_factor"], collect_metrics)
        return result
