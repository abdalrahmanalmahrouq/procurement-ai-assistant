# Procurement agent evaluation

The evaluation dataset is versioned as `procurement-agent-baseline-v1`. It
covers greetings, project help, out-of-scope and unsafe requests, analytical
questions, table/chart requests, ambiguous questions, and contextual plus
analytical follow-ups.

Each LangSmith experiment records five deterministic checks:

- routing accuracy
- MongoDB query validity
- analytical correctness (required business fields, execution, and answer)
- presentation correctness
- conversation-context handling

Run the baseline from `ai-service` after configuring the same MongoDB,
OpenRouter, and LangSmith environment variables used by the service:

```bash
python scripts/run_evaluation.py
```

The runner creates the dataset once and runs the real graph with isolated,
in-memory conversations. It does not create records in the application's
conversations collection.

After a prompt, model, validator, or graph change, run the same dataset with a
new experiment prefix and compare it with the baseline in LangSmith:

```bash
python scripts/run_evaluation.py --experiment-prefix procurement-agent-regression
```
