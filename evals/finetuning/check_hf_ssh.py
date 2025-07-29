import os
import requests
import argparse

def main():
    """
    Verifies that the user is logged in and can connect to Hugging Face Hub.
    """
    parser = argparse.ArgumentParser(description="Check Hugging Face SSH keys.")
    parser.add_argument("--token", type=str, help="Your Hugging Face Hub token.")
    args = parser.parse_args()

    token = args.token
    if not token:
        try:
            with open(os.path.expanduser("~/.cache/huggingface/token"), "r") as f:
                token = f.read().strip()
        except FileNotFoundError:
            print("Hugging Face token not found. Please provide it with the --token argument,")
            print("or log in with 'huggingface-cli login'.")
            return

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("https://huggingface.co/api/ssh-keys", headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        ssh_keys = response.json()
        if not ssh_keys:
            print("No SSH keys found on your Hugging Face account.")
            return

        print("Your SSH keys on Hugging Face:")
        for key in ssh_keys:
            print(f"- {key['title']} (created at {key['createdAt']})")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure you have a valid token.")

if __name__ == "__main__":
    main()
