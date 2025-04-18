import os
from tqdm import tqdm
import config
from .evaluation_texts import texts
from .transcription_test import TranscriptionTest
from .synthesis_test import SynthesisTest
from .llm_inference_test import LLMInferenceTest
from .utils import format_results, save_results

def run_performance_tests():
    """Main function to run all performance tests"""
    test_runners = [
        TranscriptionTest(),
        SynthesisTest(),
        LLMInferenceTest(config.LLM_MODEL)
    ]

    output_dir = "./performance_test_outputs"
    os.makedirs(output_dir, exist_ok=True)

    print("Warming up the system...")
    dry_run_file = f"{output_dir}/dry_run.wav"
    synthesis_test = next(t for t in test_runners if t.name == "synthesis")
    transcription_test = next(t for t in test_runners if t.name == "transcription")
    llm_test = next(t for t in test_runners if t.name == "llm_inference")

    # Perform dry run but don't collect metrics
    synthesis_test.run_test("Dry run text", dry_run_file, collect_metrics=False)
    transcription_test.run_test(dry_run_file, collect_metrics=False)
    llm_test.run_test(collect_metrics=False)

    print("Starting performance test...")

    for idx, text in enumerate(tqdm(texts, desc="Processing texts")):
        output_file = os.path.join(output_dir, f"text_{idx + 1}.wav")
        synthesis_test.run_test(text, output_file)
        transcription_test.run_test(output_file)
        llm_test.run_test()

    results = {test.name: test.get_results() for test in test_runners}
    results_string = format_results(results, test_runners)

    print(results_string)
    save_results(results_string)
