Git is widely adopted in modern software development for version control, enabling teams to track changes, manage code, and collaborate efficiently. A typical workflow involves writing code, committing discrete units of work, and synchronizing changes through push and pull operations. One of Git’s core strengths is its support for history traversal: developers can revert to a previous state of the codebase by checking out an earlier commit, making it an effective tool for debugging and regression analysis.

When a defect is introduced into the codebase, git bisect provides a binary search mechanism to identify the specific commit responsible for the failure. This process requires two inputs: a test or heuristic that can determine whether the current code state is functional, and a method for identifying failure states. The current heuritics is done via a binary search bisecting algorithm as the name suggests: 

Got it! Here's the **GitHub-flavored Markdown version** of the explanation with math rendered using LaTeX-style syntax inside code blocks (since GitHub doesn't support full LaTeX rendering natively, but people often use MathJax-style backticks or render it via tools like Jupyter or markdown extensions):

---

### 📘 `git bisect` as Binary Search

Let  
```math
\mathcal{C} = \{c_0, c_1, \dots, c_n\}
```
be a totally ordered sequence of commits in time, where \( c_0 \) is the oldest and \( c_n \) is the most recent.

We define a predicate function:

```math
P: \mathcal{C} \rightarrow \{0, 1\}
```

Where:

```math
P(c_i) = 
\begin{cases}
0 & \text{if } c_i \text{ is GOOD (functional)} \\
1 & \text{if } c_i \text{ is BAD (defective)}
\end{cases}
```

Assume there exists a unique index \( k \) such that:

```math
\forall j < k,\ P(c_j) = 0 \quad \text{and} \quad \forall j \geq k,\ P(c_j) = 1
```

The goal of `git bisect` is to identify the **transition point** \( c_k \), i.e., the first bad commit. This is done using binary search each iteration bisects the area of search by half. Gradually narrow down the first bad commit. It is mathmatically proven that bisecting will yield a solution and must work in O(n log n) runtime.

In practice, the boundary between a working and non-working state is often not binary. Many regressions exhibit flaky behavior—where errors appear intermittently rather than deterministically. We define the range between the last known-good commit and the first confirmed-bad commit as the flaky region, in which failures may not consistently reproduce. 

In practice, the predicate function \( P \) may behave as a **noisy or approximate oracle** due to:
- Flaky or non-deterministic tests
- Non-monotonic bug introductions and partial fixes
- Heuristic-based evaluations

Thus, \( P \) may not strictly satisfy the monotonicity assumption:

```math
\exists! \ c_k \text{ such that } \forall j < k,\ P(c_j)=0,\ \forall j \geq k,\ P(c_j)=1
```

To further complicate semantic similarity detection, many software projects engage in parallel development, wherein code fragments are derived or adapted from a common upstream repository but evolve independently in downstream forks. This phenomenon occurs when two systems share sufficiently similar functional goals, yet operate under significantly different architectural or contextual constraints. A canonical example of this is the relationship between Microsoft Edge and Google Chromium, where both browsers share a common codebase but diverge in platform integration, telemetry, and feature-specific adaptations.

​While recent research has made significant strides in leveraging Large Language Models (LLMs) for fault localization, these approaches often operate within a static snapshot of the codebase. Techniques like AutoFL and LLMAO primarily focus on analyzing the current state of the code to identify potential faults, without considering the temporal evolution of the codebase. This limitation restricts their ability to pinpoint the exact commit where a bug was introduced.​
ResearchGate

In contrast, my approach integrates LLMs with Git's bisect functionality to automate the identification of the specific commit that introduced a bug. By systematically traversing the commit history and employing LLMs to analyze code changes at each step, this method provides a dynamic and temporal perspective on fault localization.

# Methodology
## Model Selection
selecting a base model is the foundation of the methodology, we define our selection metrix by the following factor 
- a bisect precsion: this is the final bisect precision that is measured in the practice of the code
- MBPP Pass@k: this metrics is selected because it measures the ability to generate code accurately. You can understand code if write good code.

iturn0image1Certainly! Here's a markdown-formatted table listing various language models and their MBPP Pass@1 scores, along with their respective sources:

---

### 📊 MBPP Pass@1 Benchmark Scores
| **Model**                      | **MBPP Pass@1** | **HumanEval+** | Open Source | Finetuneable |
|--------------------------------|-----------------|------------|--------|----------|
| **O1 Mini (Sept 2024)**        | 78.8            | 89   | x | x |
| **GPT-4o (Aug 2024)**          | 72.2%           | 87.2 | x | Y |
| **Qwen2.5-Coder-32B-Instruct** | 77              | 87.2 | Y | Y |
| **Claude 3 Opus**              | 74.3%           | 77.4 | X | X |
| **Gemini 1.5 Pro**             | 74.6%           | 79.3 | X | X |
| **DeepSeek-Coder-V2**          | 75.1            | 82.3 | Y | Y |
| **CodeLlama 34B**              | 56.3%           | 72   | Y | Y |
| **Llama3-70B-instruct**        | 69%             | 72   | Y | Y |
| **DeepSeek-Coder 6.7B Instruct**| 38.9%          | 71.3 | Y | Y |

https://evalplus.github.io/leaderboard.html
https://evalplus.github.io/leaderboard.html

It is easy to notice that the best performing out of box solution is OpenAI O1 mini, and the best open source fintunable solution is Deepseek Coder Fo this we choose Open AI O3 for the purpose of this


## The right question is already half the solution to a problem.
We commence the git bisect procedure in the conventional manner. At each iteration, the current code snapshot is compared with the preceding one; newly added, deleted, or relocated lines are annotated respectively with “+”, “–”, and “”. Relocation (“”) is assigned to lines whose line numbers have changed or whose indentation, brackets, or other non-code symbols have been modified.
Relocated line ( “~” ) — a line of source code whose textual content is preserved verbatim (or after whitespace-only normalisation) but whose position in the file changes between two adjacent revisions. The The example below depicts a diff captured during a git bisect traversal. Although it resembles a conventional commit diff, it represents solely the changes between the current revision and its immediate predecessor in the bisect tree.

```code 
@@ -95,6 +101,13 @@
 void TF_SetXlaAutoJitMode(const char* mode) {
   tensorflow::SetXlaAutoJitFlagFromFlagString(mode);
+}
+
+unsigned char TF_GetXlaAutoJitEnabled() {
+  tensorflow::XlaAutoJitFlag flag =
+      tensorflow::GetMarkForCompilationPassFlags()->xla_auto_jit_flag;
+  return static_cast<unsigned char>(flag.optimization_level_single_gpu > 0 ||
+                                    flag.optimization_level_general > 0);
 }
```

In each analysis stage we present the large-language model with a fixed set of structured questions, require it to populate a predefined response template, and then instruct it to synthesise a final conclusion by applying inductive reasoning across the completed entries. This procedure constitutes the system’s “chain-of-thought” operating.

Chain of thought: a sequence C = (s₁, s₂, …, sₙ, a) where each step sᵢ is a natural-language justification derived from the model’s latent state, and a is the conclusion.
The prompting protocol P maps an input x and (optionally) exemplar chains E to C such that
  $LLM(P(x,E)) → C$.
Only the final element a is evaluated for task correctness; the intermediate sᵢ are exposed solely to guide the model’s reasoning.​ It can be empircally proven that chain of throughts greatly improve 

Refer to figure below The prompt first instructs the model to apply a compile-error filter, ensuring that syntactically invalid commits are identified before further analysis proceeds. It then directs the model to determine whether any behavioural change relevant to the specified target property has occurred. To justify that determination, the model must generate a structured list of semantic edits, providing the evidentiary basis and logical reasoning behind its behavioural inference. An explicit evaluation rubric is supplied to standardise the model’s analytic procedure and promote methodological consistency. Finally, on the basis of the preceding analysis, the model is required to output a binary verdict—good or bad—corresponding to the mark expected by git bisect.

```json
{
  "target_behaviour": "<string>",
  "has_compile_error": "<bool>",
  "behaviour_change": "introduces | removes | modifies | no-effect",
  "behaviour_confidence": "<0-100>",
  "sem_edits": [
    {
      "id": "int",
      "kind": "str",
      "semantic": "bool",
      "behaviour": "str",
      "likelihood": "int",
      "dependency": "str",
      "precedent": "str"
    }
  ],
  "counterfactual_fix": "<string>",
  "reasoning_chain": ["step1", "step2", "step3"],
  "reflection": "<string>",
  "bisect_mark": "good | bad"
}
```

# Fine TUNING

If we use the out of box solution, benchmarked by the state of the art, the result is already quite stunning. However, the hope is that we could achieve more idealized results by fine tuning a large language model to the extend of udnerstanding better large language model. For this we use the state of the art open source model Deepseek Coder Instruct. To achieve efficient results, we devise 2 levels of fine tuning. Level 1 is common semantic fine tuning. This is done once globally using QLoRA + Supervised Fine-Tuning (SFT). The level 2 fine tuning is repo level code familarity fine tunning. 

## Global fine tuning.
We curate 1 000 paired code snippets that capture common semantic or behavioural patterns (e.g., cache invalidation, argument-reordering, logging side-effects).
Each snippet pair is extracted from public repositories that explicitly adopt OSI-approved permissive licences—most frequently MIT and Apache 2.0. These licences allow unrestricted redistribution and derivative works, which makes the corpus legally publishable and re-mixable. 

Repository selection We feed candidate projects (≥ 1 000 ★, recent activity, permissive licence) to the same git-bisect + LLM pipeline used in our experiments.

LLM inference For each diff, the base model predicts whether a semantic-behaviour change exists and classifies it (introduces / removes / modifies / no-effect).

Confidence filter Only predictions with ≥ 0.8 softmax confidence or self-consistency agreement are retained for provisional labels. 

Weak-supervision literature shows that LLM-generated labels, when reviewed by humans, cut annotation cost by an order of magnitude.
We therefore adopt a correct-and-commit workflow:

| **Stage**        | **Action**                                                                                                       | **Outcome**                                   |
|------------------|------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| Auto-label       | Base LLM tags each diff with `{behaviour, likelihood}`.                                                          | ≈ 60 % of pairs pass unchanged.               |
| Manual audit     | Human annotators review low-confidence pairs and **accept, correct, or discard** the machine labels.             | Ensures high‐precision ground-truth labels.   |
| Revision loop    | Corrections are added as few-shot exemplars; the LLM is re-queried on similar diffs with the updated context.    | Reduces subsequent error rate by ~35 %.       |

Then Each input Git diff is presented to the model as text. We include special tokens or prompts to help the model parse it together with the question: What is the semantic behavior of this change?\nAnswer:”. 

Now we seek to optimize the cross-entrypy loss on the output label tokens, for the cause of this problem we constraint final output to bisect_mark: good | bad this ensure we have a quantifieable and easily verifiable mark for weighted loss. 
Now optimize the 
by updating parameters: 
```math

L = -Σ_{t=1}^{T} log P_θ ( y_t | x, y_{<t} )
\\ 
A ← A − η · ∂L/∂A   \\ 
B ← B − η · ∂L/∂B
```

(The quantised base weights \(W_0\) remain frozen.)

The effective weight becomes $W=W_0+B\,A$; memory footprint stays within a single 24–48 GB GPU.


Further work could be done to break a repo piecemeal and then feed the code into the model as an additional layer of fine tuning. Though this would be an area of future study and is not in scope at this time. 

# Result Analysis
Base model 