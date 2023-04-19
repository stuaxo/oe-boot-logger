import dataclasses
from pathlib import Path

from actions import get_conditions, parse_response_file
from config import Config
from menu_helper import choose_option


def ensure_result_directory(template_name):
    result_directory = Path("results") / template_name
    result_directory.mkdir(parents=True, exist_ok=True)
    return result_directory


def main():
    config = Config(
        template_name="power", custom_report_headers=["amd_s2idle", "kernel_log"]
    )

    ensure_result_directory(config.template_name)

    conditions = get_conditions()
    menu_actions = parse_response_file(config.template_name, conditions)
    option = choose_option("Options", menu_actions.keys())
    actions = menu_actions.get(option, [])

    for action, params in actions:
        action.run(None, *params)


if __name__ == "__main__":
    main()
