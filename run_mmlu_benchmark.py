import os
import json
import time
import re
import numpy as np
from datasets import load_dataset
from tqdm import tqdm
import ollama
from core.config import LLMConfig
import argparse
import sys

# Define constants
MMLU_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmarks/mmlu")

def get_available_subjects():
    """Get all available MMLU subjects from the dataset_infos.json file"""
    dataset_info_path = os.path.join(MMLU_DIR, "dataset_infos.json")
    with open(dataset_info_path, 'r') as f:
        dataset_info = json.load(f)

    subjects = list(dataset_info.keys())
    return subjects

def format_prompt(question, choices):
    """Format the prompt for the MMLU benchmark"""
    prompt = f"""Answer the following multiple-choice question by selecting the correct option (A, B, C, or D).

Question: {question}

Options:
A. {choices[0]}
B. {choices[1]}
C. {choices[2]}
D. {choices[3]}

Provide just the letter of your answer (A, B, C, or D) with no additional text.
Answer:"""
    return prompt

def extract_answer(response):
    """Extract the answer (A, B, C, or D) from the LLM response"""
    response = response.strip()

    # Case 1: Look for patterns indicating a structured response with thinking
    if "Here is my response:" in response:
        # Split by the marker and take the part after it
        parts = response.split("Here is my response:")
        if len(parts) > 1:
            final_answer = parts[1].strip()
            # If the final answer is just a single letter, return it
            if re.match(r'^[A-D]$', final_answer):
                return final_answer
            # Try to find a letter on its own line or surrounded by space
            for match in re.finditer(r'(?:^|\s)([A-D])(?:$|\s)', final_answer):
                return match.group(1)

    # Case 2: For models that output an answer and explanation
    # Try to find a standalone letter (A, B, C, or D)
    standalone_match = re.search(r'(?:^|\s)([A-D])(?:$|\s)', response)
    if standalone_match:
        return standalone_match.group(1)

    # Case 3: Look for "Answer: X" pattern
    answer_match = re.search(r'Answer:\s*([A-D])', response, re.IGNORECASE)
    if answer_match:
        return answer_match.group(1).upper()

    # Case 4: Fallback to checking if A, B, C, or D appears anywhere in the response
    # Prioritize the order they appear to handle cases where multiple letters are present
    letter_positions = []
    for letter in ['A', 'B', 'C', 'D']:
        pos = response.upper().find(letter)
        if pos >= 0:
            letter_positions.append((pos, letter))

    if letter_positions:
        # Return the letter that appears first in the response
        letter_positions.sort()
        return letter_positions[0][1]

    # No clear answer found
    return None

def evaluate_subject(subject, model_name, num_examples=None, log_file=None):
    """Evaluate the LLM on a specific MMLU subject"""
    print(f"Loading dataset for subject: {subject}")

    # Log subject header
    if log_file:
        log_file.write(f"\n\n{'='*40}\n")
        log_file.write(f"SUBJECT: {subject}\n")
        log_file.write(f"{'='*40}\n\n")

    dataset = load_dataset(os.path.join(MMLU_DIR, subject))

    # Use the test split
    test_data = dataset["test"]

    # Limit the number of examples if specified
    if num_examples is not None and num_examples > 0:
        test_data = test_data.select(range(min(num_examples, len(test_data))))

    print(f"Running evaluation on {len(test_data)} examples")

    # Initialize the Ollama client
    client = ollama.Client()

    correct = 0
    total = 0

    # Process each example
    for i, example in enumerate(tqdm(test_data)):
        question = example["question"]
        choices = example["choices"]
        correct_answer_idx = example["answer"]
        correct_answer = "ABCD"[correct_answer_idx]

        # Format the prompt
        prompt = format_prompt(question, choices)

        # Query the model - use system prompt for reasoning if it's a granite3.2 model
        try:
            messages = []

            # Add system message to enable reasoning for granite3.2 models
            if model_name.startswith("granite3.2"):
                messages.append({
                    'role': 'control',
                    'content': 'thinking'
                })

            # Add the user prompt
            messages.append({
                'role': 'user',
                'content': prompt
            })

            # Send the request to Ollama
            response = client.chat(model=model_name, messages=messages)
            model_answer = extract_answer(response['message']['content'])
            full_response = response['message']['content'].strip()

            is_correct = model_answer == correct_answer
            if is_correct:
                correct += 1
            total += 1

            # Log the question, choices, and answers
            if log_file:
                log_file.write(f"Question {i+1}:\n{question}\n\n")
                log_file.write("Options:\n")
                for j, choice in enumerate(choices):
                    log_file.write(f"{chr(65+j)}. {choice}\n")
                log_file.write(f"\nModel's full response: {full_response}\n")
                log_file.write(f"Model's answer: {model_answer}\n")
                log_file.write(f"Correct answer: {correct_answer}\n")
                log_file.write(f"Result: {'✓ Correct' if is_correct else '✗ Incorrect'}\n")
                log_file.write(f"\n{'-'*40}\n\n")

            # Add a small delay to avoid rate limiting
            time.sleep(0.1)

        except Exception as e:
            print(f"Error querying model: {e}")
            if log_file:
                log_file.write(f"Error processing question: {e}\n\n")
            continue

    # Calculate accuracy
    accuracy = correct / total if total > 0 else 0

    # Log summary for this subject
    if log_file:
        log_file.write(f"Subject Summary: {subject}\n")
        log_file.write(f"Accuracy: {accuracy:.4f} ({correct}/{total})\n\n")

    return {
        "subject": subject,
        "accuracy": accuracy,
        "correct": correct,
        "total": total
    }

def get_user_input():
    """Get all benchmark options from the user interactively"""
    print("\n===== MMLU Benchmark Configuration =====\n")

    # Show the model that will be used (but don't ask for input)
    model_name = LLMConfig.MODEL
    print(f"Using model from configuration: {model_name}")

    # 2. Get the subject
    subjects = get_available_subjects()
    # Filter out non-test subjects
    test_subjects = [s for s in subjects if s not in ['all', 'auxiliary_train']]

    print("\nAvailable subjects:")
    print("0. All subjects")
    for i, subject in enumerate(test_subjects, 1):
        print(f"{i}. {subject}")

    default_subject_idx = test_subjects.index('high_school_biology') + 1 if 'high_school_biology' in test_subjects else 1
    while True:
        try:
            subject_choice = input(f"\nSelect a subject (1-{len(test_subjects)}, 0 for all) [default: {default_subject_idx}]: ")
            if subject_choice.strip() == "":
                subject_choice = default_subject_idx
            else:
                subject_choice = int(subject_choice)

            if subject_choice == 0:
                subject = "all"
                break
            elif 1 <= subject_choice <= len(test_subjects):
                subject = test_subjects[subject_choice - 1]
                break
            else:
                print(f"Please enter a number between 0 and {len(test_subjects)}")
        except ValueError:
            print("Please enter a valid number")

    print(f"Selected subject: {'All subjects' if subject == 'all' else subject}")

    # 3. Get the number of examples
    default_examples = 20
    while True:
        try:
            examples_input = input(f"\nNumber of examples per subject (0 for all) [default: {default_examples}]: ")
            if examples_input.strip() == "":
                num_examples = default_examples
            else:
                num_examples = int(examples_input)

            if num_examples >= 0:
                break
            else:
                print("Please enter a non-negative number")
        except ValueError:
            print("Please enter a valid number")

    print(f"Using {num_examples if num_examples > 0 else 'all'} examples per subject")

    # Return all user inputs
    return {
        "model_name": model_name,
        "subject": subject,
        "num_examples": num_examples
    }

def parse_args():
    """Parse command line arguments for the MMLU benchmark"""
    parser = argparse.ArgumentParser(description="MMLU Benchmark for Large Language Models")
    
    # Run all tests from all categories with a single option
    parser.add_argument('-r', '--run-all', action='store_true',
                      help='Run all tests for all categories non-interactively')
    
    # Subject selection options (mutually exclusive)
    subject_group = parser.add_mutually_exclusive_group()
    subject_group.add_argument('-a', '--all-subjects', action='store_true', 
                              help='Run benchmark on all available subjects')
    subject_group.add_argument('-s', '--subject', type=str, 
                              help='Specific subject to test (name or index)')
    
    # Number of examples
    parser.add_argument('-e', '--examples', type=int, default=20,
                       help='Number of examples per subject (0 for all examples)')
    
    # Non-interactive mode flag
    parser.add_argument('-y', '--non-interactive', action='store_true',
                       help='Run in non-interactive mode (requires -a or -s)')
    
    return parser.parse_args()

def validate_subject(subject_arg):
    """Validate and normalize the subject argument from command line"""
    # Get available subjects
    all_subjects = get_available_subjects()
    test_subjects = [s for s in all_subjects if s not in ['all', 'auxiliary_train']]
    
    # If it's a number (as string), convert to subject name
    if subject_arg.isdigit():
        idx = int(subject_arg)
        if 1 <= idx <= len(test_subjects):
            return test_subjects[idx-1]
    
    # Check if it's a valid subject name
    if subject_arg in test_subjects:
        return subject_arg
        
    # Invalid subject, print help and exit
    print(f"Error: '{subject_arg}' is not a valid subject.")
    print("\nAvailable subjects:")
    for i, subject in enumerate(test_subjects, 1):
        print(f"{i}. {subject}")
    sys.exit(1)

def run_benchmark(options):
    """Run the MMLU benchmark on selected subjects"""
    model_name = options["model_name"]
    safe_model_name = model_name.replace(':', '-')

    # Create base directories
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Create test-specific folder structure
    # benchmark_results/mmlu/{model_name}/
    result_base_dir = os.path.join(base_dir, "benchmark_results", "mmlu")
    logs_base_dir = os.path.join(base_dir, "logs", "mmlu")

    result_dir = os.path.join(result_base_dir, safe_model_name)
    logs_dir = os.path.join(logs_base_dir, safe_model_name)

    os.makedirs(result_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    # Generate timestamp for both results and logs
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    # Create paths with only timestamps in filenames
    log_filename = os.path.join(logs_dir, f"{timestamp}.txt")
    result_file = os.path.join(result_dir, f"{timestamp}.json")

    with open(log_filename, 'w') as log_file:
        # Write log header
        log_file.write("="*50 + "\n")
        log_file.write(f"MMLU BENCHMARK LOG - {timestamp}\n")
        log_file.write(f"Model: {model_name}\n")
        log_file.write("="*50 + "\n\n")

        if options["subject"] == "all":
            subjects = get_available_subjects()
            # Exclude 'all' and 'auxiliary_train' if they exist
            subjects = [s for s in subjects if s not in ['all', 'auxiliary_train']]
        else:
            subjects = [options["subject"]]

        results = []
        for i, subject in enumerate(subjects, 1):
            # Display progress for multiple subjects
            if len(subjects) > 1:
                print(f"\nRunning category {i}/{len(subjects)}: {subject}")
            
            subject_result = evaluate_subject(
                subject,
                model_name,
                options["num_examples"],
                log_file
            )
            results.append(subject_result)
            print(f"Subject: {subject}, Accuracy: {subject_result['accuracy']:.4f} ({subject_result['correct']}/{subject_result['total']})")

        # Calculate overall accuracy if multiple subjects
        overall_accuracy = 0
        if len(results) > 1:
            total_correct = sum(r["correct"] for r in results)
            total_examples = sum(r["total"] for r in results)
            overall_accuracy = total_correct / total_examples if total_examples > 0 else 0
            print(f"\nOverall Accuracy: {overall_accuracy:.4f} ({total_correct}/{total_examples})")

            # Write overall summary to log
            log_file.write("\n" + "="*50 + "\n")
            log_file.write("OVERALL SUMMARY\n")
            log_file.write(f"Total Accuracy: {overall_accuracy:.4f} ({total_correct}/{total_examples})\n")
            log_file.write("="*50 + "\n\n")
            log_file.write("Subject Breakdown:\n")
            for result in results:
                log_file.write(f"- {result['subject']}: {result['accuracy']:.4f} ({result['correct']}/{result['total']})\n")
        else:
            overall_accuracy = results[0]["accuracy"]

        # Save results to a JSON file
        with open(result_file, 'w') as f:
            json.dump({
                "model_name": model_name,
                "subjects": results,
                "overall_accuracy": overall_accuracy,
                "timestamp": timestamp,
                "log_file": os.path.relpath(log_filename, base_dir)  # Store relative path in the JSON
            }, f, indent=2)

        # Get relative paths for display
        current_dir = os.getcwd()
        relative_result_path = os.path.relpath(result_file, current_dir)
        relative_log_path = os.path.relpath(log_filename, current_dir)

        print(f"Results saved to {relative_result_path}")
        print(f"Detailed log saved to {relative_log_path}")

if __name__ == "__main__":
    print("Welcome to the MMLU Benchmark")
    print("This tool evaluates Large Language Models on various subjects")

    # Parse command line arguments
    args = parse_args()
    
    # Simple option to run all tests
    if args.run_all:
        model_name = LLMConfig.MODEL
        print(f"\nRunning all tests for all categories with model: {model_name}")
        
        options = {
            "model_name": model_name,
            "subject": "all",
            "num_examples": 0  # Run all examples for each subject
        }
        run_benchmark(options)
    # Determine if we should use command line arguments or interactive mode
    elif args.non_interactive and (args.all_subjects or args.subject):
        model_name = LLMConfig.MODEL
        
        # Determine subject
        if args.all_subjects:
            subject = "all"
        else:
            subject = validate_subject(args.subject)
            
        # Display configuration
        print(f"\nRunning benchmark with:")
        print(f"- Model: {model_name}")
        print(f"- Subject: {subject}")
        print(f"- Examples per subject: {args.examples if args.examples > 0 else 'all'}")
        
        # Run benchmark with command line options
        options = {
            "model_name": model_name,
            "subject": subject,
            "num_examples": args.examples
        }
        run_benchmark(options)
    else:
        # If -y is specified but no subject is chosen, show error
        if args.non_interactive:
            print("Error: Non-interactive mode requires specifying a subject (-s) or all subjects (-a)")
            sys.exit(1)
            
        # Interactive mode
        options = get_user_input()
        run_benchmark(options)
