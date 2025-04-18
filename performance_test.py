import argparse
from performance_tests.run import run_performance_tests

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run performance tests for pipeline components.")
    parser.add_argument("--no-transcription", action="store_true",
                        help="Skip transcription performance tests")
    parser.add_argument("--no-synthesis", action="store_true",
                        help="Skip synthesis performance tests")
    parser.add_argument("--no-llm", action="store_true",
                        help="Skip LLM inference performance tests")
    parser.add_argument("--save", action="store_true",
                        help="Save performance results to a file")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    run_performance_tests(
        run_transcription=not args.no_transcription,
        run_synthesis=not args.no_synthesis,
        run_llm=not args.no_llm,
        should_save_results=args.save
    )
