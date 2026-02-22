import sys
import argparse
import json
from contextlib import nullcontext
from pathlib import Path
from thread_order import (
    Scheduler, ThreadProxyLogger, default_workers, load_and_collect_functions, register_functions)
from thread_order.graph_summary import format_graph_summary
try:
    from progress1bar import ProgressBar
    HAS_PROGRESS_BAR = True
except ImportError:
    HAS_PROGRESS_BAR = False
try:
    from thread_viewer import ThreadViewer
    HAS_VIEWER = True
except ImportError:
    HAS_VIEWER = False

logger = ThreadProxyLogger()

def get_parser():
    """ return argument parser
    """
    parser = argparse.ArgumentParser(
        prog='tdrun',
        description='A thread-order CLI for dependency-aware, parallel function execution.')
    parser.add_argument(
        'target',
        help='Python file containing @mark functions')
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of worker threads '
             '(default: Scheduler default or number of tasks whichever is less)')
    parser.add_argument(
        '--tags',
        type=str,
        default=None,
        help='Comma-separated list of tags to filter functions by')
    parser.add_argument(
        '--log',
        action='store_true',
        help='enable logging output')
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='enable verbose logging output')
    parser.add_argument(
        '--graph',
        action='store_true',
        help='show dependency graph and exit')
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='skip functions whose dependencies failed')
    parser.add_argument(
        '--progress',
        action='store_true',
        help='show progress bar (requires progress1bar package)')
    parser.add_argument(
        '--viewer',
        action='store_true',
        help='show thread viewer visualizer (requires thread-viewer package)')
    parser.add_argument(
        '--state-file',
        type=str,
        default=None,
        help='Path to a file containing initial state values in JSON format')
    return parser

def _maybe_load_state_file(state_file):
    """ load initial state from a JSON file
    """
    if not state_file:
        return {}
    path = Path(state_file)
    if not path.exists():
        raise FileNotFoundError(f"State file '{state_file}' not found")
    with open(path, 'r', encoding='utf-8') as f:
        state = json.load(f)
    # protect reserved keys
    if any(k.startswith('_') for k in state.keys()):
        raise ValueError('State file keys cannot start with an underscore (_) character')
    return state

def get_initial_state(unknown_args, state_file):
    """ parse arbitrary --key=value pairs from the unknown args list
        Example:
        ["--env=dev", "--region=us_west_2"] -> {"env": "dev", "region": "us_west_2"}
    """
    initial_state = _maybe_load_state_file(state_file)
    clear_results_on_start = True
    for item in unknown_args:
        if not item.startswith('--'):
            continue
        if '=' not in item:
            continue
        key, value = item[2:].split('=', 1)
        if key.startswith('result-'):
            test_name = key[len('result-'):]
            initial_state.setdefault('results', {})[test_name] = value
            clear_results_on_start = False
        else:
            initial_state[key] = value
    return initial_state, clear_results_on_start

def _setup_output(scheduler, args):
    """ configure progress output based on args
    """
    total = len(scheduler.graph.nodes())
    if args.progress:
        if not HAS_PROGRESS_BAR:
            raise SystemExit('progress1bar package is required for progress bar output')

        def on_task_done(task_name, thread_name, status, count, total, pbar, *args):
            pbar.count += 1
            pbar.alias = task_name

        pbar = ProgressBar(
            total=total,
            show_complete=False,
            clear_alias=True)
        scheduler.on_task_done(on_task_done, total, pbar)
        return pbar
    elif args.viewer:
        if not HAS_VIEWER:
            raise SystemExit('thread-viewer package is required for thread viewer output')

        def on_task_run(task_name, thread_name, viewer, *args):
            viewer.run(thread_name)

        def on_task_done(task_name, thread_name, status, count, viewer, *args):
            viewer.done(thread_name)

        viewer = ThreadViewer(
            thread_count=args.effective_workers,
            task_count=total,
            thread_prefix='thread_',
            inactive_char='░')
        scheduler.on_task_run(on_task_run, viewer)
        scheduler.on_task_done(on_task_done, viewer)
        return viewer
    else:
        def on_task_done(name, thread_name, status, count, total):
            _percent = int((count / total) * 100)
            percent = f'{status.value} [{_percent:3d}% ]'
            base = f'[{thread_name}] {name}' if thread_name else name
            dots = '.' * max(0, 75 - len(base) - len(percent))
            logger.info(f'{base} {dots} {percent}')

        scheduler.on_task_done(on_task_done, total)
        return nullcontext()

def _parse_tags_filter(tags):
    """ parse comma-separated tag list into a normalized filter list
    """
    if not tags:
        return []
    return [t.strip() for t in tags.split(',') if t.strip()]

def _maybe_call_setup_state(module, initial_state):
    """ invoke module-level setup_state(initial_state) if defined
    """
    setup_state_function = getattr(module, 'setup_state', None)
    if callable(setup_state_function):
        setup_state_function(initial_state)

def _build_scheduler_kwargs(args, initial_state, clear_results_on_start, module):
    """ build Scheduler constructor kwargs and configure logging if requested
    """
    scheduler_kwargs = {
        'workers': args.effective_workers,
        'state': initial_state,
        'clear_results_on_start': clear_results_on_start,
        'skip_dependents': args.skip_deps
    }
    # prefer module-provided logging hook if available
    setup_logging_function = getattr(module, 'setup_logging', None)
    if callable(setup_logging_function):
        setup_logging_function(
            args.effective_workers,
            verbose=args.verbose,
            add_stream_handler=not args.progress and not args.viewer,
            add_file_handler=args.log)
    else:
        scheduler_kwargs['setup_logging'] = True
        scheduler_kwargs['verbose'] = args.verbose
        scheduler_kwargs['add_stream_handler'] = not args.progress and not args.viewer
        scheduler_kwargs['add_file_handler'] = args.log

    return scheduler_kwargs

def validate_args(args):
    """ validate parsed args
    """
    if args.progress and not HAS_PROGRESS_BAR:
        raise SystemExit(
            'Error: progress1bar package is required for progress bar output')
    if args.progress and args.verbose:
        raise SystemExit(
            'Error: the --progress and --verbose arguments cannot be used together')
    if args.viewer and not HAS_VIEWER:
        raise SystemExit(
            'Error: thread-viewer package is required for viewer output')
    if args.viewer and args.verbose:
        raise SystemExit(
            'Error: the --viewer and --verbose arguments cannot be used together')
    if args.progress and args.viewer:
        raise SystemExit('Error: --progress and --viewer cannot be used together')
    if args.workers and args.workers < 1:
        raise SystemExit('Error: --workers must be >= 1')

def set_effective_workers(args, task_count):
    """ set args.effective_workers to the actual number of workers to use
        based on task count and requested workers.
    """
    args.effective_workers = args.workers if args.workers else min(default_workers, task_count)

def _main(argv=None):
    """ main CLI entry point
    """
    parser = get_parser()

    # parse args and initialize shared state
    args, unknown_args = parser.parse_known_args(argv)
    validate_args(args)

    initial_state, clear_results_on_start = get_initial_state(unknown_args, args.state_file)

    # collect and optionally filter marked functions
    tags_filter = _parse_tags_filter(args.tags)
    module, marked_functions, single_function_mode = load_and_collect_functions(
        args.target, tags_filter)
    task_count = len(marked_functions)

    set_effective_workers(args, task_count)

    # build scheduler configuration and configure logging
    scheduler_kwargs = _build_scheduler_kwargs(args, initial_state, clear_results_on_start, module)

    # allow module to mutate initial state if supported
    _maybe_call_setup_state(module, initial_state)

    scheduler = Scheduler(**scheduler_kwargs)
    logger.info(f'collected {task_count} marked functions')
    register_functions(scheduler, marked_functions, tags_filter, single_function_mode)

    if args.graph:
        print(format_graph_summary(scheduler.graph))
        return

    with _setup_output(scheduler, args):
        summary = scheduler.start()

    # debug final state and print user-facing summary
    logger.debug('Scheduler::State: ' + json.dumps(
        scheduler.sanitized_state, indent=2, default=str))
    print(summary['text'])

    if summary.get('failed'):
        sys.exit(1)

def main(argv=None):
    """ main entry point with error handling
    """
    try:
        _main(argv)
        sys.exit(0)
    except Exception as e:
        args = argv if argv is not None else sys.argv[1:]
        if '--verbose' in args:
            raise
        print(f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
