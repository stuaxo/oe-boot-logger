# open quick_response.csv in the csv reader
import csv
import functools
import shlex
import shutil
import subprocess

from collections import defaultdict
from pathlib import Path

from helpers import finalise_test
from menu_helper import SimplishMenu


@functools.lru_cache(maxsize=1)
def _get_headers(header_file):
    if not Path(header_file).is_absolute():
        raise ValueError(f"header_file must be path absolute: {header_file}")

    with open(header_file) as headers_file:
        row = next(csv.reader(headers_file))
        return row


def get_headers(header_file):
    return _get_headers(Path(header_file).resolve())


def verify_known_column(header_file, header):
    """
    :return True: if header is one of the headers in scenario.csv
    """
    headers = get_headers(header_file)
    if header in headers:
        return True

    raise ValueError(f"Header: {header} not allowed in {header_file}")


class Action:
    def prepare_params(self, *params):
        """
        Actions may need to do some processing on params.
        """
        return params

    def run(self, context, **args):
        raise NotImplementedError()

    def verify_params(self, *params):
        return True


class Reboot(Action):
    def run(self, context, **args):
        print("Rebooting")
        pprint(context)
        # Run sync
        subprocess.run(["sync"])
        # Run sudo reboot now

        # Rebooting interrupts the normal flow, so manually finalise the test.
        finalise_test(context)
        # subprocess.run(["sudo", "reboot", "now"])


class Discard(Action):
    def run(self, context, **args):
        test_directory = context["test_directory"]
        print("Discard test at path", test_directory)
        shutil.rmtree(test_directory)

        # Test finalisation would fail
        context["test_finalised"] = True


class WriteResult(Action):
    """
    Write a result to a column in scenario.csv

    See: `run` for the parameters.
    """

    def run(self, context, column, result):
        """
        Write a result to a column in scenario.csv

        :param column: The column to write to
        :param result: The result to write
        """
        print("Writing result to column", column, ":", result)
        scenario_file = context["scenario_file"]
        scenario = context["scenario"]
        scenario[column] = result
        print("Scenario is now:", scenario)
        with open(scenario_file, "w") as f:
            writer = csv.DictWriter(f, fieldnames=scenario.keys())
            writer.writeheader()
            writer.writerow(scenario)

    def prepare_params(self, *params):
        column, result = params
        fixed_column = column.strip().rstrip(",")
        result = params[1]
        return fixed_column, result

    def verify_params(self, *params):
        column, _result = params
        verify_known_column("templates/power/scenarios.csv", column)


class Quit(Action):
    def run(self, context, **args):
        print("Quitting")
        # Finalise the test, since we don't want to write any results.
        context["test_finalised"] = True


def camel_case_to_underscore_case(name):
    """
    Convert a camel case string to an underscore case string.

    :param name: The string to convert
    :return: The converted string
    """
    return "".join(
        ["_" + char.lower() if char.isupper() else char for char in name]
    ).lstrip("_")


ACTIONS = {
    camel_case_to_underscore_case(action.__name__): action
    for action in Action.__subclasses__()
}


def get_conditions():
    conditions = {"is_current_boot": False}  # TODO
    return conditions


def parse_conditions(condition_name, conditions_dict):
    if not condition_name:
        # If nothing is specified then default to True
        return True

    if condition_name in conditions_dict:
        return conditions_dict[condition_name]
    raise ValueError(f"Invalid condition: {condition_name}")


def parse_response_file(template_name, conditions_dict):
    """
    More than one action may be specified for a key, so parsing
    is in two parts.

    In the first, key_actions is populated with a list of actions
    per key, and descriptions is populated with the first description
    found for a specified key.

    In the second part, those dicts are parsed into a list of MenuItems.

    :return dict: key: MenuItem
    """

    # dict of text: [action...]
    menu_actions = defaultdict(list)
    key_descriptions = {}  # key: description

    filename = f"templates/{template_name}/quick-responses.csv"
    for row in csv.DictReader(open(filename)):
        if "description" not in row:
            raise ValueError(f"Invalid response file {filename}")

        condition_name = row.pop("condition")
        action_name = row.pop("action")
        description = row.pop("description")
        params = row.pop("params", "")

        action = ACTIONS.get(action_name)()
        if not action:
            raise ValueError(f"Invalid action: {action_name}")

        parsed_params = action.prepare_params(*shlex.split(params))
        action.verify_params(*parsed_params)

        condition = parse_conditions(condition_name, conditions_dict)
        if not condition:
            # Conditions allow actions to be ignored.
            continue

        hotkeys = SimplishMenu.get_hotkeys(description)
        for key in hotkeys:
            if key in key_descriptions and key_descriptions[key] != description:
                # Specifying the same hotkey more than once will specify as et
                # of actions to run in sequence, however the descriptions
                # MUST match.
                raise ValueError(f"Hotkey {key} is used for multiple descriptions")

            key_descriptions.setdefault(key, description)
        menu_actions[description].append((action, parsed_params))

    return menu_actions
