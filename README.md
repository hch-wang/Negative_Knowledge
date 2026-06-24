# Negative Knowledge

A single-file Python module that turns failed attempts into reusable memory.
It has no dependencies and works with any model backend.

## Install

Copy [`negative_knowledge.py`](negative_knowledge.py) into your project, or:

```bash
python3 -m pip install git+https://github.com/hch-wang/Negative_Knowledge.git
```

## Use

```python
from negative_knowledge import append, curate, load

def backend(prompt: str) -> str:
    return your_agent.generate_json(prompt)

record = curate(
    backend,
    task_id="072",
    task="Map Sub01 EEG signals to Sub03",
    evidence={
        "code": failed_code,
        "error": stderr,
        "reasoning": reasoning,
    },
)

append("negative_knowledge.jsonl", record)
memory = load("negative_knowledge.jsonl")
```

That is the whole interface:

- `curate(...)` creates and validates one record.
- `validate(record)` returns schema problems.
- `append(path, record)` stores one record as JSONL.
- `load(path)` reads the memory back.

See [`examples/quickstart.py`](examples/quickstart.py) for an offline example.
The paper artifacts remain under [`reproduction/`](reproduction/).

MIT licensed.
