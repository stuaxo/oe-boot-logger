import dataclasses
from csv import DictReader
from functools import lru_cache
from pathlib import Path

import pandas as pd
from rich.pretty import pprint


@lru_cache(maxsize=1)
def get_pending_directory():
    return Path("runtime") / "pending"


def tests_are_pending():
    """
    Check if there are any pending tests in the runtime/pending directory
    """
    pending_directory = get_pending_directory()
    return pending_directory.is_dir() and any(pending_directory.iterdir())


def read_scenario_headers(csv_file):
    """
    Read only the headers from a csv file holding one or more test scenarios.

    Return a list of headers.
    """
    with open(csv_file, "r") as f:
        settings_reader = DictReader(f)
        return settings_reader.fieldnames


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


def read_single_concrete_scenario_csv(csv_file, raise_on_multiple=True):
    """
    Read a csv file holding a single test scenario.

    Return a dictionary for the row in the csv file.
    """
    reader = read_concrete_scenario_csv(csv_file)
    settings = next(reader)
    try:
        next(reader)
    except StopIteration:
        pass
    else:
        if raise_on_multiple:
            raise ValueError(f"Expected a single row in {csv_file}, but found more than one")

    return settings


def finalise_test(context):
    """
    Move test to results directory
    :param context:
    :return:
    """
    if context.get("test_finalised"):
        return

    config = context["config"]
    # Move test to results directory
    test_directory = context["test_directory"]
    results_directory = Path("results") / test_directory.name
    test_directory.rename(results_directory)

    context["test_finalised"] = True


def gather_scenario_results(config):
    """
    Gather results from the scenario.csv file
    :param test_directory:
    :return:
    """
    extra_headers = getattr(config, "custom_report_headers", [])
    expected_headers = read_scenario_headers(Path("templates") / config.template_name / "scenarios.csv")

    scenario_data = []
    for result_directory in Path("results").iterdir():
        scenario_file = result_directory / "scenario.csv"
        if not scenario_file.is_file():
            print("no scenario file", scenario_file)
            continue

        for scenario in read_scenario_csv(scenario_file):
            if list(scenario.keys()) != expected_headers:
                raise ValueError(
                    f"Unexpected headers in {scenario_file}, expected {expected_headers}, but found {scenario.keys()}")

            for extra_header in extra_headers:
                scenario.setdefault(extra_header, "")

            scenario_data.append(scenario)

    df = pd.DataFrame(scenario_data or [{h: "" for h in expected_headers+extra_headers}])
    markdown = df.to_markdown(index=False)
    print(markdown)
