import os
from tqdm import tqdm
from .evaluation_texts import texts
from .transcription_test import TranscriptionTest
from .synthesis_test import SynthesisTest
from .llm_inference_test import LLMInferenceTest
from .utils import format_results, save_results

def run_performance_tests(run_transcription=True, run_synthesis=True, run_llm=True, should_save_results=False):
    """Main function to run all performance tests"""
    from core.config import Config

    test_runners = []

    if run_synthesis:
        test_runners.append(SynthesisTest())
    if run_transcription:
        test_runners.append(TranscriptionTest())
    if run_llm:
        test_runners.append(LLMInferenceTest(Config.LLM.MODEL))

    disabled_components = []
    if not run_transcription:
        disabled_components.append("Transcription (moonshine)")
    if not run_synthesis:
        disabled_components.append("Synthesis (piper)")
    if not run_llm:
        disabled_components.append(f"LLM inference ({Config.LLM.MODEL})")

    output_dir = "./wav_performance_tests"
    os.makedirs(output_dir, exist_ok=True)

    if not test_runners:
        print("All components disabled. No tests to run.")
        return

    print("Warming up the system...")

    dry_run_file = f"{output_dir}/dry_run.wav"

    if run_synthesis:
        synthesis_test = next((t for t in test_runners if t.name == "synthesis"), None)
        if synthesis_test:
            result = synthesis_test.run_test("Dry run text", dry_run_file, collect_metrics=False)
            if "error" in result:
                print(f"Warning: Dry run synthesis failed: {result['error']}")

    if not run_synthesis and run_transcription:
        if not os.path.exists(dry_run_file):
            print(f"Warning: Dry run file {dry_run_file} not found. Transcription dry run may fail.")

    if run_transcription:
        transcription_test = next((t for t in test_runners if t.name == "transcription"), None)
        if transcription_test:
            try:
                transcription_test.run_test(dry_run_file, collect_metrics=False)
            except Exception as e:
                print(f"Warning: Transcription dry run failed: {e}")

    if run_llm:
        llm_test = next((t for t in test_runners if t.name == "llm_inference"), None)
        if llm_test:
            try:
                llm_test.run_test(collect_metrics=False)
            except Exception as e:
                print(f"Warning: LLM inference dry run failed: {e}")

    print("Starting performance test...")

    for idx, text in enumerate(tqdm(texts, desc="Processing texts")):
        output_file = os.path.join(output_dir, f"text_{idx + 1}.wav")

        if run_synthesis:
            synthesis_test = next((t for t in test_runners if t.name == "synthesis"), None)
            if synthesis_test:
                try:
                    result = synthesis_test.run_test(text, output_file)
                    if "error" in result:
                        print(f"Warning: Synthesis failed for text {idx + 1}: {result['error']}")
                except Exception as e:
                    print(f"Error in synthesis test for text {idx + 1}: {e}")

        if run_transcription:
            if not run_synthesis and not os.path.exists(output_file):
                print(f"Warning: File {output_file} not found. Skipping transcription for this file.")
                continue

            transcription_test = next((t for t in test_runners if t.name == "transcription"), None)
            if transcription_test:
                try:
                    transcription_test.run_test(output_file)
                except Exception as e:
                    print(f"Error in transcription test for text {idx + 1}: {e}")

        if run_llm:
            llm_test = next((t for t in test_runners if t.name == "llm_inference"), None)
            if llm_test:
                try:
                    llm_test.run_test()
                except Exception as e:
                    print(f"Error in LLM inference test for text {idx + 1}: {e}")

    results = {test.name: test.get_results() for test in test_runners}
    results_string = format_results(results, test_runners, disabled_components)

    print(results_string)

    if should_save_results:
        saved_path = save_results(results_string)
        print(f"Results saved to: {saved_path}")
