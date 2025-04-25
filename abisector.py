import os
import subprocess
import sys
import stat
import shutil
import difflib
from summarizer import GPTDiffSummarizer, OpenRouterSummarizer


# === Constants ===
DEFAULT_REPO_PATH = "C:\\Users\\eugen\\Documents\\testground"
DEFAULT_TARGET_PATH = "game.py"
TEMP_DIR_NAME = "tmp"
REVERT = False
previous_content = ''


REPO_PATH = DEFAULT_REPO_PATH
REPO_WORK_PATH = os.path.join(REPO_PATH, TEMP_DIR_NAME)
TARGET_PATH = DEFAULT_TARGET_PATH



class RepoManager:
    def __init__(self, repo_path, target_path):
        self.repo_path = repo_path
        self.target_path = target_path
        self.work_path = os.path.join(repo_path, TEMP_DIR_NAME)

    def run_cmd(self, cmd, work_path=None):
        if work_path is None:
            work_path = self.work_path
        try:
            result = subprocess.run(cmd, cwd=work_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""
            return stdout, stderr, result.returncode
        except Exception as e:
            return "", str(e), 1

    def get_repo_url(self):
        url, _, _ = self.run_cmd("git config --get remote.origin.url", REPO_PATH)
        if not url:
            print("Could not determine the Git remote URL from the original repo path.")
            sys.exit(1)
        return url
    

    def force_remove_readonly(self, func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)


    def remove_repo(self):
        if os.path.exists(self.work_path):
            shutil.rmtree(self.work_path, onexc=self.force_remove_readonly)


    def sparse_checkout(self, repo_url):
        print(f"Cloning repo sparsely into: {self.work_path}")
        self.remove_repo()
        print(f"git clone --filter=blob:none --no-checkout {repo_url} {self.work_path}")
        subprocess.run(f"git clone --filter=blob:none --no-checkout {repo_url} {self.work_path}", shell=True, check=True)
        subprocess.run("git sparse-checkout init --cone", cwd=self.work_path, shell=True, check=True)
        subprocess.run(f"git sparse-checkout set {self.target_path}", cwd=self.work_path, shell=True, check=True)
        try:
            subprocess.run("git checkout main", cwd=self.work_path, shell=True, check=True)
        except subprocess.CalledProcessError:
            subprocess.run("git checkout master", cwd=self.work_path, shell=True, check=True)
            print("Checked out 'master' branch.")


class BisectSession:
    def __init__(self, repo_manager, summarizer):
        self.repo = repo_manager
        self.summarizer = summarizer
        self.previous_content = ''

    def diff_and_summarize(self):
        target_file = os.path.join(self.repo.work_path, self.repo.target_path)
        if not os.path.isfile(target_file):
            print(f"[File '{self.repo.target_path}' not found at current commit]")
            return

        print(f"Contents of file {self.repo.target_path} at current commit:\n")
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            current_content = f.readlines()
            # diff = list(difflib.unified_diff(self.previous_content, current_content, lineterm='', fromfile='previous', tofile='current'))
            # print("--- Diff from previous commit ---")
            # diff_text = ''.join(diff) if diff else "No changes."
            # print(diff_text)
            # self.previous_content = current_content
            diff_text = "".join(current_content)
            print(diff_text)
            self.summarizer.summarize(diff_text)

    def prompt_user(self):
        while True:
            choice = input("Is this commit good or bad? [g]ood/[b]ad/[c]ancel: \n\n").strip().lower()
            if choice in ["g", "b", "c"]:
                return choice

    def run(self):
        head_commit, _, _ = self.repo.run_cmd("git rev-parse HEAD")
        root_commit, _, _ = self.repo.run_cmd("git rev-list --max-parents=0 HEAD")

        print(f"Starting git bisect from HEAD={head_commit} (bad) to ROOT={root_commit} (good)...")
        self.repo.run_cmd(f"git bisect start {head_commit} {root_commit}")

        while True:
            current_commit, _, _ = self.repo.run_cmd("git rev-parse HEAD")
            print(f"Currently at commit: {current_commit}")
            self.diff_and_summarize()

            choice = self.prompt_user()
            if choice == "c":
                print("Bisect cancelled by user.")
                break

            output, _, _ = self.repo.run_cmd(f"git bisect {'good' if choice == 'g' else 'bad'}")
            if "first bad commit" in output:
                print(output)
                # output, _, _ = self.repo.run_cmd("git bisect log") # this line shows the log of getting here:
                break


class GitBisectCLI:
    def __init__(self):
        self.repo_path = None
        self.target_path = None
        self.revert = False
        self.repo_url = None

    def parse_args(self):
        print("Parsing arguments...", sys.argv)
        
        self.repo_path = DEFAULT_REPO_PATH
        self.target_path = DEFAULT_TARGET_PATH
        args = {arg.split('=')[0]: arg.split('=')[1] for arg in sys.argv[1:] if '=' in arg}

        self.repo_path = os.path.abspath(args.get('repo_path', DEFAULT_REPO_PATH))
        self.target_path = args.get('target_path', DEFAULT_TARGET_PATH)
        self.repo_url = args.get('repo_url', None)
        self.problem = args.get('problem', None)
        print(f"repo_path: {self.repo_path}, target_path: {self.target_path}, repo_url: {self.repo_url}")

    def run(self):
        work_path = os.path.join(self.repo_path, TEMP_DIR_NAME)
        repo = RepoManager(self.repo_path, self.target_path)
        if not self.repo_url:
            self.repo_url = repo.get_repo_url()
        repo.sparse_checkout(self.repo_url)

        print(f"Using working repository path: {repo.work_path}")
        print(f"Target file: {repo.target_path}")

        bisect = BisectSession(repo, OpenRouterSummarizer(self.problem))
        bisect.run()

        revert = input("keep work directory[y/N]: ").strip().lower()
        self.revert = revert == "y"
        if not self.revert:
            repo.remove_repo()


if __name__ == "__main__":
    app = GitBisectCLI()
    app.parse_args()
    app.run()
    