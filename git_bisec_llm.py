import os
import subprocess
import shutil
import difflib
import json

REPO_PATH = os.getcwd()
STATE_FILE = ".bisect_state.json"


def run_cmd(cmd):
    result = subprocess.run(cmd, cwd=REPO_PATH, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout.strip()


def get_commit_hash(rev):
    return run_cmd(f"git rev-parse {rev}")


def get_all_files():
    file_list = []
    for root, _, files in os.walk(REPO_PATH):
        for file in files:
            if ".git" not in root:
                full_path = os.path.relpath(os.path.join(root, file), REPO_PATH)
                file_list.append(full_path)
    return file_list


def save_repo_state(path=".repo_snapshot"):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
    for file in get_all_files():
        dest = os.path.join(path, file)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(os.path.join(REPO_PATH, file), dest)


def diff_between_commits(commit1, commit2):
    return run_cmd(f"git diff {commit1} {commit2}")


def save_state_file(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)


def load_state_file():
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def prompt_user(msg):
    while True:
        choice = input(f"{msg} [g]ood/[b]ad: ").strip().lower()
        if choice in ["g", "b"]:
            return choice == "g"


def summarize_diff(diff_text):
    # Placeholder LLM summary logic
    print("\n[LLM Summary] Here's what changed:")
    print("------------------")
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            print("[Added]", line)
        elif line.startswith("-") and not line.startswith("---"):
            print("[Removed]", line)
    print("------------------\n")


def main():
    print("Initializing bisect helper...\n")

    head_commit = get_commit_hash("HEAD")
    root_commit = run_cmd("git rev-list --max-parents=0 HEAD")

    print(f"HEAD commit (bad): {head_commit}")
    print(f"Root commit (good): {root_commit}\n")

    print("Saving snapshot of current repo state...")
    save_repo_state()
    print("Snapshot saved.\n")

    save_state_file({
        "head_commit": head_commit,
        "root_commit": root_commit,
        "last_commit": head_commit
    })

    print("Starting git bisect...")
    run_cmd(f"git bisect start {head_commit} {root_commit}")

    while True:
        state = load_state_file()
        current_commit = get_commit_hash("HEAD")

        if current_commit == state["last_commit"]:
            print("No new commit to compare.")
            log = run_cmd("git bisect log")
            print("Current log:", log)
            break
        else:
            print("\n--- Commit Diff Summary ---")
            diff = diff_between_commits(state["last_commit"], current_commit)
            summarize_diff(diff)

            is_good = prompt_user("Is this commit good?")
            run_cmd(f"git bisect {'good' if is_good else 'bad'}")

            state["last_commit"] = current_commit
            save_state_file(state)

        log = run_cmd("git bisect log")
        if "is the first bad commit" in log:
            print("\nGit bisect complete.")
            break

    revert = input("Do you want to reset to HEAD state? [y/N]: ").strip().lower()
    if revert == "y":
        run_cmd("git bisect reset")
        run_cmd(f"git checkout {state['head_commit']}")
        print("Restored to original HEAD state.")


if __name__ == "__main__":
    main()
