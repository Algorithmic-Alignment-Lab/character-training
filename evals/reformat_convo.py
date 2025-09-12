
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target_file", help="The path to the conversation file to reformat.")
    args = parser.parse_args()

    with open(args.target_file, 'r') as f:
        convo = json.load(f)

    with open(args.target_file, 'w') as f:
        json.dump(convo, f, indent=4)

if __name__ == "__main__":
    main()

