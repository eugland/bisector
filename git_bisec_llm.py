import os
import subprocess

REPO_PATH = os.getcwd()

REPO_PATH = 'C:\\Users\\eugen\\Documents\\testground'
TARGET_PATH = 'gamerepo/game.py'


def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, cwd=REPO_PATH, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        return stdout, stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def print_target_file_or_function():
    target_path = os.path.join(REPO_PATH, TARGET_PATH)
    if os.path.isfile(target_path):
        print(f"\nContents of file {TARGET_PATH} at current commit:\n")
        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
            print(f.read())
    else:
        # Attempt to locate a function in Python code
        print(f"\nSearching for function or identifier: {TARGET_PATH}\n")
        found = False
        for root, _, files in os.walk(REPO_PATH):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if TARGET_PATH in line:
                                print(f"Found in {file_path}, line {i+1}:")
                                print("".join(lines[max(0, i-2):i+3]))
                                found = True
                                break
                    if found:
                        break
        if not found:
            print(f"[Could not locate '{TARGET_PATH}' as a file or function]")


def prompt_user():
    while True:
        choice = input("Is this commit good or bad? [g]ood/[b]ad/[c]ancel: ").strip().lower()
        if choice in ["g", "b", "c"]:
            return choice


def main():
    head_commit, _, _ = run_cmd("git rev-parse HEAD")
    root_commit, _, _ = run_cmd("git rev-list --max-parents=0 HEAD")

    print(f"Starting git bisect from HEAD={head_commit} (bad) to ROOT={root_commit} (good)...")
    run_cmd(f"git bisect start {head_commit} {root_commit}")

    while True:
        current_commit, _, _ = run_cmd("git rev-parse HEAD")
        print(f"\nCurrently at commit: {current_commit}")

        if TARGET_PATH:
            print_target_file_or_function()
            
        choice = prompt_user()
        if choice == "c":
            print("Bisect cancelled by user.")
            break

        run_cmd(f"git bisect {'good' if choice == 'g' else 'bad'}")

        output, _, _ = run_cmd("git bisect log")
        print('output: ', output)
        if "first bad commit" in output:
            print("\nGit bisect complete.")
            print(output)
            break

    revert = input("Reset to original HEAD? [y/N]: ").strip().lower()
    if revert == "y":
        run_cmd("git bisect reset")
        run_cmd(f"git checkout {head_commit}")
        print("Restored to original HEAD state.")


if __name__ == "__main__":
    main()
