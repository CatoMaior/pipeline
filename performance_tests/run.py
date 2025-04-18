import os
from tqdm import tqdm
from .evaluation_texts import texts
from .transcription_test import TranscriptionTest
from .synthesis_test import SynthesisTest
from .llm_inference_test import LLMInferenceTest
from .utils import format_results, save_results

def run_performance_tests(run_transcription=True, run_synthesis=True, run_llm=True):
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
        disabled_components.append("transcription")
    if not run_synthesis:
        disabled_components.append("synthesis")
    if not run_llm:
        disabled_components.append("llm_inference")

    output_dir = "./performance_test_outputs"
    os.makedirs(output_dir, exist_ok=True)

    if not test_runners:
        print("All components disabled. No tests to run.")
        return

    print("Warming up the system...")

    dry_run_file = f"{output_dir}/dry_run.wav"

    if run_synthesis:
        synthesis_test = next((t for t in test_runners if t.name == "synthesis"), None)
        if synthesis_test:
            synthesis_test.run_test("Dry run text", dry_run_file, collect_metrics=False)

    if run_transcription:
        transcription_test = next((t for t in test_runners if t.name == "transcription"), None)
        if transcription_test:
            if not run_synthesis or not os.path.exists(dry_run_file):
                from core.synthesizer import Synthesizer
                synth = Synthesizer(Config.SYNTHESIS.PIPER_MODEL_PATH)
                os.makedirs(os.path.dirname(dry_run_file), exist_ok=True)
                synth.save_output("Dry run text for transcription only", dry_run_file)

            transcription_test.run_test(dry_run_file, collect_metrics=False)

    if run_llm:
        llm_test = next((t for t in test_runners if t.name == "llm_inference"), None)
        if llm_test:
            llm_test.run_test(collect_metrics=False)

    print("Starting performance test...")

    for idx, text in enumerate(tqdm(texts, desc="Processing texts")):
        output_file = os.path.join(output_dir, f"text_{idx + 1}.wav")

        if run_synthesis:
            synthesis_test = next((t for t in test_runners if t.name == "synthesis"), None)
            if synthesis_test:
                synthesis_test.run_test(text, output_file)

        if run_transcription and run_synthesis:
            transcription_test = next((t for t in test_runners if t.name == "transcription"), None)
            if transcription_test:
                transcription_test.run_test(output_file)

        if run_llm:
            llm_test = next((t for t in test_runners if t.name == "llm_inference"), None)
            if llm_test:
                llm_test.run_test()

    results = {test.name: test.get_results() for test in test_runners}
    results_string = format_results(results, test_runners, disabled_components)

    print(results_string)
    save_results(results_string)
