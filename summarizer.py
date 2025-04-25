import os
import threading
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
from accelerate import init_empty_weights, load_checkpoint_and_dispatch
import torch
from openai import OpenAI
import time

class DiffSummarizer:

    def summarize(self, diff_text):
        raise NotImplementedError("Must implement summarize method")


class GPTDiffSummarizer(DiffSummarizer):
    def __init__(self, problem):
        super().__init__()
        self.problem = problem
        load_dotenv()  # Load variables from .env
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
    def summarize(self, diff_text):
        if not diff_text or not diff_text.strip() or diff_text.strip() == "No changes.":
            return
        
        def worker():
            try:
                client = self.client
                print("--- GPT Summary ---")
                cur = time.time()
                response = client.chat.completions.create(
                    # model="gpt-4",
                    model="gpt-4.1",
                    # model="o4-mini",

                    messages=[
                        {"role": "system", "content": """You are an expert code analysis assistant helping the user perform a git bisect operation. 
                        Your task is to analyze a code change the user give you and answer the problem that the user asks about answer in json only 
                        and answer only in boolean or numbers
                        Also answer should_git_bisect_good when relevant code is not found, or relevant code is found but working properly"""},
                        {"role": "user", "content": 
                        "problem: " + self.problem 
                        + """answer the following in json:
                        has_compile_error:
                        relevant_code_found:
                        relevant_code_introduced:
                        number_of_relevant_code_occurance:
                        problem_found:
                        is_a_good_commit:
                        chance_of_first_bad_commit:
                        should_git_bisect_good: \n""" + diff_text
                        }
                    ]
                )
                print(response.choices[0].message.content)
                print("Time taken:", time.time() - cur)
            except Exception as e:
                print(f"[GPT Error] {e}")
        thread = threading.Thread(target=worker)
        thread.start()


class OpenRouterSummarizer(DiffSummarizer):
    def __init__(self, problem):
        super().__init__()
        self.problem = problem
        load_dotenv()  # Load variables from .env
        api_key = os.getenv("OEPNROUTER_API_KEY")
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        
    def summarize(self, diff_text):
        if not diff_text or not diff_text.strip() or diff_text.strip() == "No changes.":
            return
        try:
            client = self.client
            print("--- GPT Summary ---")
            cur = time.time()
            response = client.chat.completions.create(
                # model="gpt-4",
                model="microsoft/mai-ds-r1:free",
                messages=[
                        {"role": "system", "content": """You are an expert code analysis assistant helping the user perform a git bisect operation. 
                        Your task is to analyze a code change the user give you and answer the problem that the user asks about answer in json 
                        Also answer should_git_bisect_good when relevant code is not found, or relevant code is found but working properly. 
                        Lastly explain should_git_bisect_good decision"""},
                        {"role": "user", "content": 
                        "problem: " + self.problem 
                        + """answer the following in json:
                        has_compile_error:
                        relevant_code_found:
                        relevant_code_introduced:
                        number_of_relevant_code_occurance:
                        problem_found:
                        is_a_good_commit:
                        chance_of_first_bad_commit:
                        should_git_bisect_good:
                        explanation: \n""" + diff_text
                        }
                    ]
            )
            print(self.problem)
            print(response.choices[0].message.content)
            print("Time taken:", time.time() - cur)
        except Exception as e:
            print(f"[Open Router Error] {e}")
        

if __name__ == "__main__":
    # Example usage
    diff_text = """
--- previous+++ current@@ -1,12 +1,19 @@ 
 def main():
     name = input('Enter your name: ')
     health = 100
-    choice = input('Do you go left or right? ')
-    if choice == 'left':
-        print('You encounter a friendly dragon!')
+    treasure_found = False
+    while health > 0 and not treasure_found:
+        choice = input('Do you go left or right? ')
+        if choice == 'left':
+            print('You find a treasure chest!')
+            treasure_found = True
+        else:
+            print('You fall into a trap!')
+            health -= 50
+        print(f'{name} has {health} health points.')
+    if treasure_found:
+        print('Congratulations, you win!')
     else:
-        print('You fall into a trap!')
-        health -= 50
-    print(f'{name} has {health} health points.')
+        print('Game over!')
"""
    summarizer = OpenRouterSummarizer()
    summarizer.summarize(diff_text)