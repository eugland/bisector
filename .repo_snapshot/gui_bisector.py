import sys
import os
import subprocess
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox, QListWidget
)


from PySide6.QtCore import Qt

class GitBisectGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git Bisect GUI with LLM")
        self.setMinimumSize(800, 500)
        self.repo_path = ""
        self.bisect_log = []
        self.bisect_stack = []
        self.init_ui()
        load_dotenv()
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def init_ui(self):
        layout = QVBoxLayout()

        # Repository selection
        repo_layout = QHBoxLayout()
        self.repo_label = QLabel("Repository Path:")
        self.repo_input = QLineEdit()
        self.repo_browse = QPushButton("Browse")
        self.repo_browse.clicked.connect(self.browse_repo)
        repo_layout.addWidget(self.repo_label)
        repo_layout.addWidget(self.repo_input)
        repo_layout.addWidget(self.repo_browse)
        layout.addLayout(repo_layout)

        # Commit inputs
        input_layout = QHBoxLayout()
        self.good_input = QLineEdit()
        self.good_input.setPlaceholderText("Good Commit")
        self.bad_input = QLineEdit()
        self.bad_input.setPlaceholderText("Bad Commit")
        input_layout.addWidget(self.good_input)
        input_layout.addWidget(self.bad_input)
        layout.addLayout(input_layout)

        # Control buttons
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Bisect")
        self.start_button.clicked.connect(self.start_bisect)
        self.good_button = QPushButton("Mark Good")
        self.good_button.clicked.connect(self.mark_good)
        self.bad_button = QPushButton("Mark Bad")
        self.bad_button.clicked.connect(self.mark_bad)
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self.undo_last_bisect)
        self.reset_button = QPushButton("Reset Bisect")
        self.reset_button.clicked.connect(self.reset_bisect)
        self.status_button = QPushButton("Show Status")
        self.status_button.clicked.connect(self.show_current_status)
        self.analyze_button = QPushButton("LLM Analyze")
        self.analyze_button.clicked.connect(self.analyze_current_commit)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.good_button)
        control_layout.addWidget(self.bad_button)
        control_layout.addWidget(self.undo_button)
        control_layout.addWidget(self.reset_button)
        control_layout.addWidget(self.status_button)
        control_layout.addWidget(self.analyze_button)
        layout.addLayout(control_layout)

        # Output display
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        layout.addWidget(self.output_display)

        # Command history view
        self.history_view = QListWidget()
        layout.addWidget(self.history_view)

        self.setLayout(layout)

    def browse_repo(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Git Repository")
        if directory:
            self.repo_input.setText(directory)
            self.repo_path = directory

    def run_git_command(self, args):
        if not self.repo_path:
            QMessageBox.warning(self, "Error", "Please select a repository.")
            return
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True
            )
            self.output_display.append(f"$ git {' '.join(args)}\n{result.stdout}")
            self.history_view.addItem(f"git {' '.join(args)}")
            if args[0] == "bisect" and args[1] in ["good", "bad"]:
                commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, stdout=subprocess.PIPE, text=True).stdout.strip()
                self.bisect_stack.append(commit)
        except subprocess.CalledProcessError as e:
            self.output_display.append(f"$ git {' '.join(args)}\n{e.output}")
            QMessageBox.critical(self, "Git Error", e.output)

    def start_bisect(self):
        self.run_git_command(["bisect", "start"])
        self.run_git_command(["bisect", "bad", self.bad_input.text().strip()])
        self.run_git_command(["bisect", "good", self.good_input.text().strip()])

    def mark_good(self):
        self.run_git_command(["bisect", "good"])

    def mark_bad(self):
        self.run_git_command(["bisect", "bad"])

    def reset_bisect(self):
        self.run_git_command(["bisect", "reset"])
        self.bisect_stack.clear()

    def undo_last_bisect(self):
        if self.bisect_stack:
            prev_commit = self.bisect_stack.pop()
            self.run_git_command(["checkout", prev_commit])
            self.output_display.append(f"⏪ Reverted to {prev_commit}")

    def show_current_status(self):
        result = subprocess.run(["git", "bisect", "log"], cwd=self.repo_path, stdout=subprocess.PIPE, text=True)
        self.output_display.append("\n📜 Bisect Log:\n" + result.stdout)

    def analyze_current_commit(self):
        try:
            result = subprocess.run(
                ["git", "diff", "--unified=5", "HEAD~1", "HEAD"],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                text=True,
                check=True
            )
            diff = result.stdout[:8000]  # limit size to fit model context

          

            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI that helps debug git diffs."},
                    {"role": "user", "content": f"Explain what's happening in this diff:\n\n{diff}"}
                ]
            )

            answer = response.choices[0].message.content
            self.output_display.append("\n🤖 LLM Analysis:\n" + answer)

        except Exception as e:
            self.output_display.append("\n❌ OpenAI Error: " + str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitBisectGUI()
    window.show()
    sys.exit(app.exec())

# bad commit:
# 94f0b674070b7ff0b9b2497ac7a022fc38b3aa6

# good commit:
# 54dbce650d406dd2ba8bb85f1503863f42ec91a9