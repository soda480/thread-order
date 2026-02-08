[![ci](https://github.com/soda480/thread-order/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/soda480/thread-order/actions/workflows/ci.yml)
![Coverage](https://raw.githubusercontent.com/soda480/thread-order/main/badges/coverage.svg)
[![PyPI version](https://badge.fury.io/py/thread-order.svg?icon=si%3Apython)](https://badge.fury.io/py/thread-order)

# thread-order
`thread-order` is a lightweight Python framework for running functions in parallel while honoring explicit dependency order.
You declare dependencies; the scheduler handles sequencing, concurrency, and correctness.

Great for dependency-aware test runs, build steps, pipelines, and automation flows that need structure without giving up speed.

## Why thread-order?

Use it when you want:
* Parallel execution with strict upstream → downstream ordering
* A simple, declarative way to express dependencies (`after=['a', 'b']`)
* Deterministic behavior even under concurrency
* A DAG-driven execution model without heavyweight tooling
* A clean decorator-based API for organizing tasks
* A CLI (`tdrun`) for running functions as parallel tasks

## Key Features
* Parallel execution using Python threads backed by a dependency DAG
* Deterministic ordering based on `after=[...]` relationships
* Decorator-based API (`@mark`, `@dregister`) for clean task definitions
* Shared state (opt-in) with a thread-safe, built-in lock
* Thread-safe logging via `ThreadProxyLogger`
* Graceful interrupt handling and clear run summaries
* CLI: `tdrun` — dependency-aware test runner with tag filtering
* DAG visualization — inspect your dependency graph with --graph
* Simple, extensible design — no external dependencies
* Prebuilt Docker image available to run tdrun with no local setup required
* Optional GUI: A visual alternative to the CLI with deterministic execution visibility, live thread monitoring, and progress feedback

### About the DAG

thread-order schedules work using a Directed Acyclic Graph (DAG) — this structure defines which tasks must run before others.  
If you’re new to DAGs or want a quick refresher, this short primer is helpful: https://en.wikipedia.org/wiki/Directed_acyclic_graph

## Installation

```
pip install thread-order
```

To install GUI:

```
pip install thread-order[ui]
```

## CLI Overview (`tdrun`)

`tdrun` is a DAG-aware, parallel test runner built on top of the thread-order scheduler.

It discovers `@mark` functions inside a module, builds a dependency graph, and executes everything in parallel while preserving deterministic order.

You get:
* Parallel execution based on the Scheduler
* Predictable, DAG-driven ordering
* Tag filtering (`--tags=tag1,tag2`)
* Arbitrary state injection via `--key=value`
* Mock upstream results for single-function runs
* Graph inspection (`--graph`) to validate ordering and parallelism
* Clean pass/fail summary
* Functions with failed dependendencies are skipped (default behaivor)
* Progress Bar integration-ready - requires [progress1bar](https://pypi.org/project/progress1bar) package.
* Thread Viewer integration-ready - requires [thread-viewer](https://pypi.org/project/thread-viewer/) package.

### CLI usage
```bash
usage: tdrun [-h] [--workers WORKERS] [--tags TAGS] [--log] [--verbose] [--graph] [--skip-deps]
             [--progress] [--viewer] [--state-file STATE_FILE] target

A thread-order CLI for dependency-aware, parallel function execution.

positional arguments:
  target                Python file containing @mark functions

options:
  -h, --help            show this help message and exit
  --workers WORKERS     Number of worker threads 
                            (default: Scheduler default or number of tasks whichever is less)
  --tags TAGS           Comma-separated list of tags to filter functions by
  --log                 enable logging output
  --verbose             enable verbose logging output
  --graph               show dependency graph and exit
  --skip-deps           skip functions whose dependencies failed
  --progress            show progress bar (requires progress1bar package)
  --viewer              show thread viewer visualizer (requires thread-viewer package)
  --state-file STATE_FILE
                        Path to a file containing initial state values in JSON format
```

### Run all marked functions in a module:

```bash
tdrun path/to/module.py
```

### `tdrun` [Example](https://github.com/soda480/thread-order/blob/main/examples/example4c.py)

![graph](https://github.com/soda480/thread-order/blob/main/docs/images/graph.png?raw=true)

<details><summary>Code</summary>

```Python
import time
import random
from faker import Faker
from thread_order import mark, ThreadProxyLogger

logger = ThreadProxyLogger()

def setup_state(state):
    state.update({'faker': Faker()})

def run(name, state, deps=None, fail=False):
    with state['_state_lock']:
        last_name = state['faker'].last_name()
    sleep = random.uniform(.5, 2.5)
    logger.debug(f'{name} \"{last_name}\" running - sleeping {sleep:.2f}s')
    time.sleep(sleep)
    if fail:
        assert False, 'Intentional Failure'
    else:
        results = []
        for dep in (deps or []):
            dep_result = state['results'].get(dep, '--no-result--')
            results.append(f'{name}.{dep_result}')
        if not results:
            results.append(name)
        logger.debug(f'{name} PASSED')
        return '|'.join(results)

@mark()
def pre_op_assessment_A(state): return run('pre_op_assessment_A', state)

@mark(after=['pre_op_assessment_A'])
def assign_surgical_staff_B(state): return run('assign_surgical_staff_B', state, deps=['pre_op_assessment_A'])

@mark(after=['pre_op_assessment_A'])
def prepare_operating_room_C(state): return run('prepare_operating_room_C', state, deps=['pre_op_assessment_A'])

@mark(after=['prepare_operating_room_C'])
def sterilize_instruments_D(state): return run('sterilize_instruments_D', state, deps=['prepare_operating_room_C'], fail=True)
    
@mark(after=['prepare_operating_room_C'])
def equipment_safety_checks_E(state): return run('equipment_safety_checks_E', state, deps=['prepare_operating_room_C'])

@mark(after=['assign_surgical_staff_B', 'sterilize_instruments_D'])
def perform_surgery_F(state): return run('perform_surgery_F', state, deps=['assign_surgical_staff_B', 'sterilize_instruments_D'])
```

</details>

![test_dag1](https://github.com/soda480/thread-order/blob/main/docs/images/test_dag1.gif?raw=true)


### Run a single function:
```bash
tdrun module.py::fn_b
```

This isolates the function and ignores its upstream dependencies.

You can provide mocked results:
```bash
tdrun module.py::fn_b --result-fn_a=mock_value
```

### Inject arbitrary state parameters
```bash
tdrun module.py --env=dev --region=us-west
```
These appear in `initial_state` and can be processed in your module’s `setup_state(state)`.

This allows your module to compute initial state based on CLI parameters.

### DAG Inspection

Use graph-only mode to inspect dependency structure:
```bash
tdrun examples/example4c.py --graph
```

Example output:
```bash
Graph: 6 nodes, 6 edges
Roots: [3]
Leaves: [1], [2]
Levels: 4

Nodes:
  [0] assign_surgical_staff_B
  [1] equipment_safety_checks_E
  [2] perform_surgery_F
  [3] pre_op_assessment_A
  [4] prepare_operating_room_C
  [5] sterilize_instruments_D

Edges:
  [0] -> [2]
  [1] -> (none)
  [2] -> (none)
  [3] -> [0], [4]
  [4] -> [1], [5]
  [5] -> [2]

Stats:
  Longest chain length (edges): 3
  Longest chains:
    pre_op_assessment_A -> prepare_operating_room_C -> sterilize_instruments_D -> perform_surgery_F
  High fan-in nodes (many dependencies):
    perform_surgery_F (indegree=2)
  High fan-out nodes (many dependents):
    pre_op_assessment_A (children=2)
    prepare_operating_room_C (children=2)
```

## Running Docker Image

```bash
docker run -it --rm -v $PWD:/work soda480/thread-order <<tdrun args>>
```

`-it` parameter required for `--progress` and `--viewer` options

## GUI Overview (`tdrun-ui`)

![ui](https://github.com/soda480/thread-order/blob/main/docs/images/tdrun-ui.gif?raw=true)


## API Overview

thread-order also exposes a low-level scheduler API for embedding into custom workflows.

Most users should start with `tdrun` CLI.

```python
class Scheduler(
    workers=None,                 # max number of worker threads
    state=None,                   # shared state dict passed to @mark functions
    store_results=True,           # save return values into state["results"]
    clear_results_on_start=True,  # wipe previous results
    setup_logging=False,          # enable built-in logging config
    add_stream_handler=True,      # attach stream handler to logger
    add_file_handler=True,        # attach file handlers for each thread to logger
    verbose=False,                # enable extra debug logging on stream handler
    skip_dependents=False         # skip dependents when prerequisites fail
)
```

Runs registered callables across multiple threads while respecting declared dependencies.

### Core Methods
| Method | Description |
| --- | --- |
| `register(obj, name, after=None, with_state=False)` |	Register a callable for execution. after defines dependencies by name, specify if function is to receive the shared state. |
| `dregister(after=None, with_state=False)` | Decorator variant of register() for inline task definitions. |
| `start()` | Start execution, respecting dependencies. Returns a summary dictionary. |
| `mark(after=None, with_state=True, tags=None)` | Decorator that marks a function for deferred registration by the scheduler, allowing you to declare dependencies (after) and whether the function should receive the shared state (with_state), and optionally add tags to the function (tags) for execution filtering. |

### Callbacks

All are optional and run on the scheduler thread (never worker threads).

| Callback | When Fired | Signature |
| --- | --- | --- |
| `on_task_start(fn)`      | Before a task starts | (name) |
| `on_task_run(fn)`        | When tasks starts running on a thread | (name, thread) |
| `on_task_done(fn)`       | After a task finishes | (name, status, count) |
| `on_scheduler_start(fn)` | Before scheduler starts running tasks | (meta) |
| `on_scheduler_done(fn)`  | After all tasks complete | (summary) |

### Shared state and `_state_lock`

If `with_state=True`, tasks receive the shared state dict.
thread-order inserts a re-entrant lock at state['_state_lock'] you can use when modifying shared values.

For more information refer to [Shared State Guidelines](https://github.com/soda480/thread-order/blob/main/docs/shared_state.md)

### Interrupt Handling

Press Ctrl-C during execution to gracefully cancel outstanding work:
* Running tasks finish naturally or are marked as cancelled
* Remaining queued tasks are discarded
* Final summary reflects all results

## More Examples

See the examples/ folder for runnable demos.

## Development

Clone the repository and ensure the latest version of Docker is installed on your development server.

Build the Docker image:
```sh
docker image build \
-t thread-order:latest .
```

Run the Docker container:
```sh
docker container run \
--rm \
-it \
-v $PWD:/code \
thread-order:latest \
bash
```

Execute the dev pipeline:
```sh
make dev
```
