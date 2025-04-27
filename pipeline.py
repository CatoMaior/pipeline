import argparse
from pipeline_components.pipeline import Pipeline

def parse_arguments():
    """Parse command line arguments for the pipeline."""
    # Create main parser with improved description and epilog
    parser = argparse.ArgumentParser(
        description="Interactive pipeline for voice transcription, local LLM interaction, and speech synthesis.",
        epilog="""
Examples:
  # Run in text mode with specific input
  python pipeline.py --mode text --text "What's the capital of France?"

  # Process audio from a WAV file and save the output
  python pipeline.py --mode audio --source file --file recordings/input.wav --output save

  # Use the thermostat use case with microphone input
  python pipeline.py --use-case thermostat --mode audio --source microphone

  # Play the synthesized output
  python pipeline.py --mode text --text "Explain quantum computing" --output play
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Create argument groups for better organization
    mode_group = parser.add_argument_group('Input Mode Options', 'Configure how the pipeline receives input')
    audio_group = parser.add_argument_group('Audio Options', 'Settings for audio input (when --mode=audio)')
    llm_group = parser.add_argument_group('LLM Options', 'Configure the Large Language Model behavior')
    output_group = parser.add_argument_group('Output Options', 'Control how the LLM response is handled')
    misc_group = parser.add_argument_group('Miscellaneous Options')

    # Use case selection
    parser.add_argument("-u", "--use-case", type=str, metavar="CASE",
                        help="Specify the use case for the pipeline ('general' or 'thermostat')")

    # Input mode options
    mode_group.add_argument("-m", "--mode", choices=["audio", "text"],
                        help="Select input mode: 'audio' for speech input or 'text' for text input")
    mode_group.add_argument("-t", "--text", type=str, metavar="TEXT",
                        help="Provide the text input directly (used when --mode=text)")

    # Audio options
    audio_group.add_argument("-s", "--source", choices=["file", "microphone"],
                        help="Select audio source: 'file' to use a WAV file or 'microphone' to record live")
    audio_group.add_argument("-f", "--file", type=str, metavar="PATH",
                        help="Path to WAV file for audio input (used when --source=file)")

    # Output options
    output_group.add_argument("-o", "--output", choices=["save", "play", "both", "none"],
                        help="Control output handling: 'save' to file, 'play' immediately, 'both', or 'none'")
    output_group.add_argument("-n", "--output-name", type=str, metavar="FILENAME",
                        help="Custom filename for saving the synthesized speech output (used when --output includes 'save')")

    # Miscellaneous
    misc_group.add_argument("--log-to-console", action="store_true",
                        help="Display detailed debug information in the console during execution")
    misc_group.add_argument("--no-follow-up", action="store_true",
                        help="Disable follow-up questions for additional details")

    return parser.parse_args()

def main():
    """Entry point for the pipeline."""
    args = parse_arguments()

    # Create a dictionary of options from command line arguments
    options = {}

    if args.use_case:
        options["use_case"] = args.use_case

    if args.mode:
        options["interaction_mode"] = args.mode == "audio"  # Convert to boolean

    if args.text:
        options["text_input"] = args.text

    if args.source:
        options["audio_source"] = args.source == "file"  # Convert to boolean

    if args.file:
        options["wav_file_path"] = args.file

    if args.output:
        output_map = {"save": "1", "play": "2", "both": "3", "none": "4"}
        options["output_mode"] = output_map[args.output]

    if args.output_name:
        options["output_filename"] = args.output_name

    if args.log_to_console is not None:
        options["log_to_console"] = args.log_to_console

    # Set the follow-up interactions option (enabled by default)
    options["enable_follow_up"] = not args.no_follow_up

    pipeline = Pipeline(options=options)
    pipeline.run()

if __name__ == "__main__":
    main()