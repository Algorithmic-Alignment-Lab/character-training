import argparse
import os
import shutil
from pathlib import Path

def copy_folders(input_folder_name: str, output_folder_name: str, replace: bool):
    """
    Copies specific json files from input folders to corresponding output folders.
    """

    base_dir = Path("auto_eval_gen/results/transcripts")
    files_to_copy = ["decomposition.json", "ideation.json", "variation.json"]

    if not base_dir.is_dir():
        print(f"Error: Base directory '{base_dir}' not found.")
        return

    print(f"Searching for subdirectories in: {base_dir}")
    for character_dir in base_dir.iterdir():
        if character_dir.is_dir():
            input_dir = character_dir / input_folder_name
            if input_dir.is_dir():
                output_dir = character_dir / output_folder_name
                
                print(f"Found input directory: {input_dir}")
                print(f"Creating output directory: {output_dir}")
                if output_dir.exists() and replace:
                    print(f"Emptying output folder: {output_dir}")
                    shutil.rmtree(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)


                for filename in files_to_copy:
                    source_file = input_dir / filename
                    dest_file = output_dir / filename
                    if source_file.is_file():
                        print(f"  Copying {source_file} to {dest_file}")
                        shutil.copy(source_file, dest_file)
                    else:
                        print(f"  Skipping. File not found: {source_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Copy specific files from input-named folders to output-named folders across character directories."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="The name of the input folder within each character directory (e.g., '17b-eval').",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="The name of the output folder to create (e.g., '17b-eval-no-system-prompt').",
    )

    # add replace argument so that it removes and replaces all the files in the output folder if --replace is set
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace the output folder if it exists.",
    )
    args = parser.parse_args()

    copy_folders(args.input, args.output, args.replace)
