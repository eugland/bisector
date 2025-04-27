# app.py
import os
import shutil
import stat
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session
from summarizer import OpenRouterSummarizer, GPTDiffSummarizer

app = Flask(__name__)
app.secret_key = "your_secret_key"  # needed for session

# Constants
DEFAULT_REPO_PATH = "C:\\Users\\eugen\\Documents\\testground"
DEFAULT_TARGET_PATH = "game.py"
TEMP_DIR_NAME = "tmp"


# --- Classes ---
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
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except Exception as e:
            return "", str(e), 1

    def force_remove_readonly(self, func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def remove_repo(self):
        if os.path.exists(self.work_path):
            shutil.rmtree(self.work_path, onerror=self.force_remove_readonly)

    def sparse_checkout(self, repo_url):
        self.remove_repo()
        subprocess.run(f"git clone --filter=blob:none --no-checkout {repo_url} {self.work_path}", shell=True, check=True)
        subprocess.run("git sparse-checkout init --cone", cwd=self.work_path, shell=True, check=True)
        subprocess.run(f"git sparse-checkout set {self.target_path}", cwd=self.work_path, shell=True, check=True)
        try:
            subprocess.run("git checkout main", cwd=self.work_path, shell=True, check=True)
        except subprocess.CalledProcessError:
            subprocess.run("git checkout master", cwd=self.work_path, shell=True, check=True)


class BisectSession:
    def __init__(self, repo_manager, summarizer):
        self.repo = repo_manager
        self.summarizer = summarizer
        self.previous_content = ''

    def diff_and_summarize(self):
        target_file = os.path.join(self.repo.work_path, self.repo.target_path)
        if not os.path.isfile(target_file):
            return "[File not found]", ""

        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            current_content = f.read()

        diff_text = current_content
        return current_content
    
    def get_summary(self, diff_text):
        return self.summarizer.summarize(diff_text)

    def git_bisect_step(self, user_feedback):
        output, _, _ = self.repo.run_cmd(f"git bisect {'good' if user_feedback == 'good' else 'bad'}")
        print(output)
        if "first bad commit" in output.lower():
            # Extract first bad commit id
            commit_id = output
            return True, commit_id
        return False, None


# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session['repo_url'] = request.form['repo_url']
        session['target_path'] = request.form['target_path']
        session['problem'] = request.form['problem']

        session['repo_path'] = DEFAULT_REPO_PATH
        session['bisect_started'] = False

        return redirect(url_for('bisect'))

    return render_template("index.html")


@app.route("/bisect", methods=["GET", "POST"])
def bisect():
    repo_url = session.get('repo_url')
    target_path = session.get('target_path')
    problem = session.get('problem')
    repo_path = session.get('repo_path')

    repo = RepoManager(repo_path, target_path)
    summarizer = OpenRouterSummarizer(problem)
    bisect = BisectSession(repo, summarizer)

    if not session.get('bisect_started'):
        repo.sparse_checkout(repo_url)
        head_commit, _, _ = repo.run_cmd("git rev-parse HEAD")
        root_commit, _, _ = repo.run_cmd("git rev-list --max-parents=0 HEAD")
        repo.run_cmd(f"git bisect start {head_commit} {root_commit}")
        session['bisect_started'] = True
        session['bisect_finished'] = False

    if request.method == "POST" and not session.get('bisect_finished'):
        feedback = request.form.get("feedback")
        if feedback == "cancel":
            repo.run_cmd("git bisect reset")
            repo.remove_repo()
            session.clear()
            return redirect(url_for('index'))

        finished, bad_commit = bisect.git_bisect_step(feedback)
        if finished:
            session['bisect_finished'] = True
            session['bad_commit'] = bad_commit
            print(f"First bad commit found: {bad_commit}")

    current_commit, _, _ = repo.run_cmd("git rev-parse HEAD")
    file_content = bisect.diff_and_summarize()

    return render_template(
        "bisect.html",
        commit=current_commit,
        file_content=file_content,
        bisect_finished=session.get('bisect_finished', False),
        bad_commit=session.get('bad_commit')
    )


@app.route("/get_summary", methods=["POST"])
def get_summary():
    if session.get('bisect_finished', False):
        return {
            "summary": "BISECT COMPLETE: first bad commit found at: " + session.get('bad_commit', None),  # No summary because bisect is done
            "bisect_finished": True,
            "bad_commit": session.get('bad_commit', None)
        }

    problem = session.get('problem')
    summarizer = GPTDiffSummarizer(problem)
    bisect = BisectSession(None, summarizer)

    data = request.get_json()
    file_content = data.get('file_content', '')

    summary = bisect.summarizer.summarize(file_content)

    return {
        "summary": summary,
        "bisect_finished": False,
        "bad_commit": None
    }


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
