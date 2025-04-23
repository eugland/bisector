| Step | Stream | Change Description                                         | Behavior / Notes                                                                                 |
|------|--------|------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| 1    | Up     | Introduce `sanitize_input` function                        | Function returns input as-is; no audit line present.                                             |
| 2    | Down   | Mirror: Implement `sanitize_input` function                | Function returns input as-is; no audit line present.                                             |
| 3    | Down   | Add audit line before return                               | Audit line outputs raw input; no transformations applied.                                        |
| 4    | Up     | Add full-width to half-width conversion at top of function | Input is transformed; audit line still outputs raw input before transformation.                  |
| 5    | Down   | Merge upstream changes; move conversion to top, audit to bottom | Audit line now outputs transformed input; behavior change occurs here.                        |
| 6    | Down   | Subsequent changes; error discovered in later commits      | Audit line reflects transformed input; issue traced back to step 5 where behavior changed.       |

the debugger wrote a unit test that pinpoint where the auditor line could generate, the test shows step 3 when the auditor line is added because at this step this test was wrote and it only tests if auditor line gives an output or even worse no unit test wrote because it is not on critical path

Now what? how can llm help to pinpoint this area?


Instead of a gui application do this (you can use command line python git):
1. at the start of the current repo, find the head of the commit, store it, and tell me what that is, you will use it as the bad commit
2. then find the first ever commit you can find, store it, 
3. store the content of this repo at the current stage, that includes all code, 
4. when bisect start, show the difference between this commit and the previous bisect, use LLM this should show me highlight description and all code changes
5. then ask the user if this is good or bad like a normal git bisect would do. 
6. When finished ask the user if he or she wants to revert this to the head state
