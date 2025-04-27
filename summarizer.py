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
        
        
        try:
            client = self.client
            print("--- GPT Summary ---")
            cur = time.time()
            response = client.chat.completions.create(
                # model="gpt-4",
                model="gpt-4.1",
                # model="o4-mini",

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert code-analysis assistant guiding a git-bisect session. "
                            "Analyse each diff with the eight-step behaviour rubric below and "
                            "return ONLY the requested JSON. "
                            "Using the hypotheses above, decide behaviour_change.  Map that decision to bisect_mark (\"good\" or \"bad\") per the table and include it in the JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content":
                            f"target_behaviour: {self.problem}\n\n"
                            "Return JSON with the following keys:\n"
                            "has_compile_error: <bool>\n"
                            "behaviour_change: \"introduces|removes|modifies|no-effect\"\n"
                            "behaviour_confidence: <0-100>\n"
                            "sem_edits: [  # list of objects generated via Steps 1-4 above\n"
                            "  {id:int, kind:str, semantic:bool, behaviour:str, likelihood:int,\n"
                            "   dependency:str, precedent:str}\n"
                            "]\n"
                            "counterfactual_fix: <string>\n"
                            "reasoning_chain: [\"step1\",\"step2\",\"step3\"]\n"
                            "reflection: <string>\n"
                            "\nRubric questions:\n"
                            "1️⃣ Enumerate edits …\n2️⃣ Mark semantic …\n3️⃣ Hypothesise behaviour …\n"
                            "4️⃣ List dependencies …\n5️⃣ Precedent …\n6️⃣ Counter-factual …\n"
                            "7️⃣ Give verdict …\n8️⃣ Confidence & reflection …\n"
                            "bisect_mark: good | bad"
                            "\n--- BEGIN DIFF ---\n"
                            + diff_text +
                            "\n--- END DIFF ---"
                    }
                    ]
            )
            print(response.choices[0].message.content)
            print("Time taken:", time.time() - cur)
            return response.choices[0].message.content
        except Exception as e:
            print(f"[GPT Error] {e}")
        return 'No Changes.'


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
                    {
                        "role": "system",
                        "content": (
                            "You are an expert code-analysis assistant guiding a git-bisect session. "
                            "Analyse each diff with the eight-step behaviour rubric below and "
                            "return ONLY the requested JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content":
                            f"target_behaviour: {self.problem}\n\n"
                            "Return JSON with the following keys:\n"
                            "has_compile_error: <bool>\n"
                            "behaviour_change: \"introduces|removes|modifies|no-effect\"\n"
                            "behaviour_confidence: <0-100>\n"
                            "sem_edits: [  # list of objects generated via Steps 1-4 above\n"
                            "  {id:int, kind:str, semantic:bool, behaviour:str, likelihood:int,\n"
                            "   dependency:str, precedent:str}\n"
                            "]\n"
                            "counterfactual_fix: <string>\n"
                            "reasoning_chain: [\"step1\",\"step2\",\"step3\"]\n"
                            "reflection: <string>\n"
                            "\nRubric questions:\n"
                            "1️⃣ Enumerate edits …\n2️⃣ Mark semantic …\n3️⃣ Hypothesise behaviour …\n"
                            "4️⃣ List dependencies …\n5️⃣ Precedent …\n6️⃣ Counter-factual …\n"
                            "7️⃣ Give verdict …\n8️⃣ Confidence & reflection …\n"
                            "\n--- BEGIN DIFF ---\n"
                            + diff_text +
                            "\n--- END DIFF ---"
                    }
                    ]
            )
            print(self.problem)
            print(response.choices[0].message.content)
            return response.choices[0].message.content
        except Exception as e:
            print(f"[Open Router Error] {e}")
        return 'No changes.'
        

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