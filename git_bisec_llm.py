import os
import subprocess

REPO_PATH = os.getcwd()


def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, cwd=REPO_PATH, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        return stdout, stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


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

        choice = prompt_user()
        if choice == "c":
            print("Bisect cancelled by user.")
            break

        run_cmd(f"git bisect {'good' if choice == 'g' else 'bad'}")

        output, _, _ = run_cmd("git bisect log")
        if "is the first bad commit" in output:
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
