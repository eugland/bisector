import os
import subprocess
import sys
import stat
import shutil

# === Constants ===
DEFAULT_REPO_PATH = "C:\\Users\\eugen\\Documents\\testground"
DEFAULT_TARGET_PATH = "game.py"
TEMP_DIR_NAME = "tmp"
REVERT = False

# These will be overwritten by CLI args if provided
REPO_PATH = DEFAULT_REPO_PATH
REPO_WORK_PATH = os.path.join(REPO_PATH, TEMP_DIR_NAME)
TARGET_PATH = DEFAULT_TARGET_PATH


def run_cmd(cmd, cwd=REPO_WORK_PATH):
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        return stdout, stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def get_repo_url(original_repo_path):
    url, _, _ = run_cmd("git config --get remote.origin.url", cwd=original_repo_path)
    if not url:
        print("Could not determine the Git remote URL from the original repo path.")
        sys.exit(1)
    return url


def force_remove_readonly(func, path, exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def sparse_checkout(repo_url):
    print(f"Cloning repo sparsely into: {REPO_WORK_PATH}\n")
    if os.path.exists(REPO_WORK_PATH):
        shutil.rmtree(REPO_WORK_PATH, onexc=force_remove_readonly)
    subprocess.run(f"git clone --filter=blob:none --no-checkout {repo_url} {REPO_WORK_PATH}", shell=True, check=True)
    subprocess.run("git sparse-checkout init --cone", cwd=REPO_WORK_PATH, shell=True, check=True)
    subprocess.run(f"git sparse-checkout set {TARGET_PATH}", cwd=REPO_WORK_PATH, shell=True, check=True)
    subprocess.run("git checkout main", cwd=REPO_WORK_PATH, shell=True, check=True)  # adjust branch if needed


def prompt_user():
    while True:
        choice = input("Is this commit good or bad? [g]ood/[b]ad/[c]ancel: ").strip().lower()
        if choice in ["g", "b", "c"]:
            return choice


def print_target_file():
    target_path = os.path.join(REPO_WORK_PATH, TARGET_PATH)
    if os.path.isfile(target_path):
        print(f"\nContents of file {TARGET_PATH} at current commit:\n")
        with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
            print(f.read())
    else:
        print(f"[File '{TARGET_PATH}' not found at current commit]")


def main():
    global REPO_PATH, REPO_WORK_PATH, TARGET_PATH

    if len(sys.argv) >= 3:
        REPO_PATH = os.path.abspath(sys.argv[1])
        TARGET_PATH = sys.argv[2]
        REPO_WORK_PATH = os.path.join(REPO_PATH, TEMP_DIR_NAME)

    repo_url = get_repo_url(REPO_PATH)
    sparse_checkout(repo_url)

    print(f"Using working repository path: {REPO_WORK_PATH}")
    print(f"Target file: {TARGET_PATH}\n")

    head_commit, _, _ = run_cmd("git rev-parse HEAD")
    root_commit, _, _ = run_cmd("git rev-list --max-parents=0 HEAD")

    print(f"Starting git bisect from HEAD={head_commit} (bad) to ROOT={root_commit} (good)...")
    run_cmd(f"git bisect start {head_commit} {root_commit}")

    while True:
        current_commit, _, _ = run_cmd("git rev-parse HEAD")
        print(f"\nCurrently at commit: {current_commit}")

        print_target_file()

        choice = prompt_user()
        if choice == "c":
            print("Bisect cancelled by user.")
            break

        run_cmd(f"git bisect {'good' if choice == 'g' else 'bad'}")

        output, _, _ = run_cmd("git bisect log")
        if "first bad commit" in output:
            print("\nGit bisect complete.")
            print(output)
            break

    revert = input("keep work directory[y/N]: ").strip().lower()
    REVERT = revert == "y"
    # if revert == "y":
    #     run_cmd("git bisect reset")
    #     run_cmd(f"git checkout {head_commit}")
    #     print("Restored to original HEAD state.")


if __name__ == "__main__":
    try:
        main()
    finally:
        if REVERT and os.path.exists(REPO_WORK_PATH):
            shutil.rmtree(REPO_WORK_PATH, onexc=force_remove_readonly)
            print(f"Cleaned up workspace at {REPO_WORK_PATH}")
