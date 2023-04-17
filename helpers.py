from csv import DictReader
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_pending_directory():
    return Path("runtime") / "pending"


def tests_are_pending():
    """
    Check if there are any pending tests in the runtime/pending directory
    """
    pending_directory = get_pending_directory()
    return pending_directory.is_dir() and any(pending_directory.iterdir())


def read_scenario_csv(csv_file):
    """
    Read a csv file holding one or more test scenarios.

    Yield a dictionary for each row in the csv file.
    """
    with open(csv_file, "r") as f:
        settings_reader = DictReader(f)
        yield from settings_reader


def read_concrete_scenario_csv(csv_file):
    """
    Read scenario csv, but only return concrete fields (whose
    key does not contain a question mark).
    """
    for settings in read_scenario_csv(csv_file):
        yield {k: v for k, v in settings.items() if '?' not in k}


def finalise_test(context):
    """
    Move test to results directory
    :param context:
    :return:
    """
    if context.get("test_finalised"):
        return

    # Move test to results directory
    test_directory = context["test_directory"]
    results_directory = Path("results") / test_directory.name
    test_directory.rename(results_directory)

    context["test_finalised"] = True
