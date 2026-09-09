import sys, os, atexit, datetime, json, hashlib
from pathlib import Path
from rich.console import Console
from rich.traceback import install
from rich.prompt import Prompt
import ast


class ComplexityVisitor(ast.NodeVisitor):
    """Class to facilitate walking code to count depth and functions"""

    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0
        self.function_count = 0

    def visit_FunctionDef(self, node):
        self.function_count += 1
        self._visit_block_node(node)

    def visit_AsyncFunctionDef(self, node):
        self.function_count += 1
        self._visit_block_node(node)

    # Block-level constructs that increase nesting
    def visit_If(self, node):
        self._visit_block_node(node)

    def visit_For(self, node):
        self._visit_block_node(node)

    def visit_While(self, node):
        self._visit_block_node(node)

    def visit_With(self, node):
        self._visit_block_node(node)

    def visit_Try(self, node):
        self._visit_block_node(node)

    def _visit_block_node(self, node):
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            self.max_depth = self.current_depth
        self.generic_visit(node)
        self.current_depth -= 1


def is_interactive_student_run() -> bool:
    """Checks to ensure that the student has run the code directly"""

    # Check for any autograding or CI pipelines
    if any(
        k in os.environ
        for k in ("AUTOGRADE", "CI", "PYTEST_CURRENT_TEST", "DISABLE_RUNLOG")
    ):
        return False

    # Check if input from interactive terminal (not piped or headless)
    if not sys.stdin.isatty():
        return False

    # Check if process launched directly from testing framework
    main_script = Path(sys.argv[0]).stem.lower()
    if any(
        runner in main_script for runner in ("pytest", "unittest", "conftest", "grade")
    ):
        return False
    if main_script.startswith("test_") or main_script.endswith("_test"):
        return False

    return True


def get_code_metrics(script_path: str) -> dict:
    """Compiles a small code metrics dictionary with significant lines of code (sloc)
    the number of defined functions, and the largest amount of nesting present.
    """
    if not os.path.exists(script_path):
        return {"sloc": 0, "functions": 0, "max_depth": 0}

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # Strip docstrings/triple-quote comments using AST
        lines = source.splitlines()
        docstring_lines = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    # Mark line numbers containing docstrings
                    for item in node.body:
                        if (
                            isinstance(item, ast.Expr)
                            and isinstance(item.value, ast.Constant)
                            and isinstance(item.value.value, str)
                        ):
                            for lnum in range(item.lineno, item.end_lineno + 1):
                                docstring_lines.add(lnum)

        # Compute SLOC (excluding blank lines, # comments, and docstring lines)
        sloc = 0
        for lnum, line in enumerate(lines, start=1):
            sline = line.strip()
            if sline and not sline.startswith("#") and lnum not in docstring_lines:
                sloc += 1

        # Compute structural metrics
        visitor = ComplexityVisitor()
        visitor.visit(tree)

        return {
            "sloc": sloc,
            "functions": visitor.function_count,
            "max_depth": visitor.max_depth,
        }

    except Exception:
        # Fallback if parsing fails for unexpected reasons
        return {"sloc": 0, "functions": 0, "max_depth": 0}


def get_mandatory_prompt(prompt_text: str) -> str:
    """Prompts the user for a response, and keeps prompting if they enter nothing"""
    while True:
        response = Prompt.ask(prompt_text).strip()
        if response:
            return response
        console.print(
            "[bold red]Response required.[/bold red] Enter your observation to proceed."
        )


def get_previous_hash() -> str:
    """Finds the hash of the previous log, so as to propogate forwards."""
    if not os.path.exists(LOG_FILENAME):
        return GENESIS_HASH
    try:
        with open(LOG_FILENAME, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            if not lines:
                return GENESIS_HASH
            last_entry = json.loads(lines[-1])
            return last_entry.get("hash", GENESIS_HASH)
    except Exception:
        return GENESIS_HASH


def handle_exception(exc_type, exc_value, exc_traceback):
    """Callback to still log even if an error occurs."""
    # Ignore KeyboardInterrupt from main code, log it cleanly
    if issubclass(exc_type, KeyboardInterrupt):
        prompt_and_save_log(error_msg="KeyboardInterrupt (User Cancelled)")
    else:
        rich_excepthook(exc_type, exc_value, exc_traceback)
        prompt_and_save_log(error_msg=f"{exc_type.__name__}: {exc_value}")


def prompt_and_save_log(error_msg: str | None = None):
    """After finish or error, prompt for post-run questions and log."""

    # Ensure only prompted once, in case of errors or Tkinter
    global _has_prompted_post_run
    if _has_prompted_post_run:
        return
    _has_prompted_post_run = True

    console.rule("\n[bold cyan]📝 POST-RUN REFLECTION[/bold cyan]")

    # Status report
    if error_msg:
        console.print(f"[bold red]System Status:[/bold red] Crashed ({error_msg})")
        status_tag = f"CRASH: {error_msg}"
    else:
        console.print(
            "[bold green]System Status:[/bold green] Finished without crashing"
        )
        status_tag = "CLEAN_EXIT"

    # Prompts
    try:
        actual_result = get_mandatory_prompt("[yellow]What actually happened?[/yellow]")
        next_step = get_mandatory_prompt("[yellow]What is your next step?[/yellow]")
    except KeyboardInterrupt:  # In case of Ctrl + C
        console.print(
            "\n[bold yellow]Reflection interrupted. Logging run as interrupted.[/bold yellow]"
        )
        actual_result = "INTERRUPTED (Ctrl+C)"
        next_step = "N/A"

    timestamp = datetime.datetime.now().astimezone().isoformat()
    prev_hash = get_previous_hash()
    metrics = get_code_metrics(sys.argv[0])

    raw_payload = f"{timestamp}|{hypothesis}|{status_tag}|{actual_result}|{next_step}|{prev_hash}|{metrics}"
    current_hash = hashlib.sha256(raw_payload.encode()).hexdigest()

    log_entry = {
        "timestamp": timestamp,
        "script": ENTRY_SCRIPT,
        "expected": hypothesis,
        "status": status_tag,
        "actual_result": actual_result,
        "next_step": next_step,
        "code_metrics": metrics,
        "hash": current_hash,
    }

    with open(LOG_FILENAME, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


if is_interactive_student_run():

    console = Console()
    install(show_locals=True, width=100, word_wrap=True)
    rich_excepthook = sys.excepthook

    ENTRY_SCRIPT = Path(sys.argv[0]).stem
    LOG_FILENAME = f"{ENTRY_SCRIPT}_log.jsonl"
    GENESIS_HASH = "00000000000000000000000000000000"
    _has_prompted_post_run = False

    # Pre-run prompt
    console.rule("\n[bold cyan]🛑 PRE-RUN CHECKPOINT[/bold cyan]")
    try:
        hypothesis = get_mandatory_prompt(
            "[yellow]What do you EXPECT to happen on this run?[/yellow]"
        )
    except KeyboardInterrupt:
        console.print(
            "\n[bold red]\nRun canceled.[/bold red] You must complete the checkpoint to execute your code."
        )
        # Exit cleanly without triggering atexit/excepthook log saves
        os._exit(1)

    # Redefine what happens with exceptions, to ensure they are still logged
    sys.excepthook = handle_exception
    # When the program exits, prompt the user
    atexit.register(lambda: prompt_and_save_log(error_msg=None))
