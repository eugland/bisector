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

