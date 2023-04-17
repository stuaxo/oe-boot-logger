import re
from csv import DictWriter
from pathlib import Path

from helpers import get_pending_directory, read_scenario_csv
from log_result import Config


def _normalise_item(item):
    """
    User regex to replace any non-alphanumeric characters with a single underscore
    """
    return re.sub(r'\W+', '_', item).lower()


def normalise_question_row(user_question_row):
    """
    Normalise user question data into a string that can be used as a directory name.

    :param user_question_row:  Dict of user question data
    """
    return '__'.join([f'{_normalise_item(k)}-{_normalise_item(v)}'
                      for (k, v) in user_question_row.items()
                      if '?' not in k])


def setup_pending_test(output_dir: Path, fieldnames, settings):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a new CSV file using the fieldnames from reader
    with open(output_dir / "scenario.csv", "w") as f:
        writer = DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(settings)


def setup_pending_tests(config):
    """
    Setup pending tests in the runtime/pending diectory based on data from user-question.csv
    """
    pending_directory = get_pending_directory()
    pending_directory.mkdir(parents=True, exist_ok=True)

    # If any tests are pending then raise an error
    if pending_directory.is_dir() and any(pending_directory.iterdir()):
        raise ValueError("There are pending tests. Please run them before creating new tests")

    template_directory = Path("templates") / config.template_name

    for number, settings in enumerate(read_scenario_csv(template_directory / "scenarios.csv"), start=1):
        output_dir = pending_directory / f"{number}-{config.template_name}--{normalise_question_row(settings)}"
        setup_pending_test(output_dir, settings.keys(), settings)


def main():
    config = Config(
        template_name="power"
    )

    setup_pending_tests(config)


if __name__ == "__main__":
    main()
