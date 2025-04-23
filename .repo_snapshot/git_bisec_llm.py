import os
import subprocess
import shutil
import difflib

REPO_PATH = os.getcwd()


def run_cmd(cmd):
    result = subprocess.run(cmd, cwd=REPO_PATH, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    if not result or not result.stdout:
        return f"Command failed: {cmd}"
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


def get_file_content_at_commit(commit, filepath):
    result = run_cmd(f"git show {commit}:{filepath}")
    return result.splitlines() if result else []


def summarize_diff_files(file_diffs):
    print("\n[LLM Summary] Here's what changed:")
    for filename, diff in file_diffs.items():
        print(f"\nFile: {filename}")
        for line in diff:
            if line.startswith('+'):
                print("[Added]", line)
            elif line.startswith('-'):
                print("[Removed]", line)
    print("------------------\n")


def prompt_user(msg):
    while True:
        choice = input(f"{msg} [g]ood/[b]ad: ").strip().lower()
        if choice in ["g", "b"]:
            return choice == "g"


def main():
    print("Initializing bisect helper...\n")

    head_commit = get_commit_hash("HEAD")
    root_commit = run_cmd("git rev-list --max-parents=0 HEAD")

    print(f"HEAD commit (bad): {head_commit}")
    print(f"Root commit (good): {root_commit}\n")

    print("Saving snapshot of current repo state...")
    save_path = ".repo_snapshot"
    if os.path.exists(save_path):
        shutil.rmtree(save_path)
    os.makedirs(save_path, exist_ok=True)
    for file in get_all_files():
        dest = os.path.join(save_path, file)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(os.path.join(REPO_PATH, file), dest)
    print("Snapshot saved.\n")

    print("Starting git bisect...")
    run_cmd(f"git bisect start {head_commit} {root_commit}")

    last_commit = None
    current_commit = get_commit_hash("HEAD")

    while True:
        if current_commit == last_commit:
            print("No new commit to compare.")
        else:
            print("\n--- File Content Diff ---")
            file_diffs = {}
            for file in get_all_files():
                before = get_file_content_at_commit(last_commit, file)
                after = get_file_content_at_commit(current_commit, file)
                if before != after:
                    diff = list(difflib.unified_diff(before, after, lineterm=''))
                    file_diffs[file] = diff
            summarize_diff_files(file_diffs)

            is_good = prompt_user("Is this commit good?")
            outs = run_cmd(f"git bisect {'good' if is_good else 'bad'}")
            last_commit = current_commit
            import re
            match = re.search(r'\[([0-9a-f]{40})\]', outs)

            if match:
                current_commit = match.group(1)
            else:
                # Fallback to retrieving the current HEAD commit hash
                current_commit = get_commit_hash("HEAD")

        log = run_cmd("git bisect log")
        if "is the first bad commit" in log:
            print("\nGit bisect complete.")
            break

    revert = input("Do you want to reset to HEAD state? [y/N]: ").strip().lower()
    if revert == "y":
        run_cmd("git bisect reset")
        run_cmd(f"git checkout {head_commit}")
        print("Restored to original HEAD state.")


if __name__ == "__main__":
    main()
