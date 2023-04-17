import subprocess
import sys
from pathlib import Path

from rich.pretty import pprint

from actions import parse_response_file
from config import Config
from helpers import tests_are_pending, get_pending_directory, read_scenario_csv, read_concrete_scenario_csv, \
    finalise_test
from journal_utils import get_current_boot_id, write_journal_to_path
from menu_helper import choose_option


def get_next_pending_test():
    """
    :return:  The next pending test from the runtime/pending directory
    """
    pending_directory = get_pending_directory()
    return sorted(pending_directory.iterdir())[0]


def ensure_running_directory():
    running_directory = Path("runtime") / "running"
    running_directory.mkdir(parents=True, exist_ok=True)
    return running_directory


def get_boot_id_filename(test_directory):
    boot_id_file = test_directory / "boot_id"
    return boot_id_file


def get_test_boot_id(test_directory):
    boot_id_file = get_boot_id_filename(test_directory)
    return boot_id_file.read_text()


def setup_next_pending_test_directory():
    next_pending_test = get_next_pending_test()
    running_directory = ensure_running_directory()

    # Move the pending test directory to the runtime/running directory
    # and add the current boot ID as a suffix to the directory name.
    boot_id = get_current_boot_id()
    output_dir = running_directory / f"{next_pending_test.name}--{boot_id}"

    # Move the directory
    next_pending_test.rename(output_dir)

    boot_id_file = get_boot_id_filename(output_dir)
    boot_id_file.write_text(boot_id)

    return output_dir


def get_context(test_directory):
    boot_id = get_test_boot_id(test_directory)
    current_boot_id = get_current_boot_id()
    scenario_file = test_directory / "scenario.csv"
    context = {
        "is_current_boot": boot_id == current_boot_id,
        "boot_id": boot_id,
        "current_boot_id": current_boot_id,
        "test_directory": test_directory,
        "scenario_file": scenario_file,
    }
    return context


def run_s2idle(test_directory, config):
    # TODO - run s2idle
    use_sudo = True
    cmd = [f'{config.amd_s2idle}', '--log', str(test_directory / 'amd_s2idle.log'), '--wait', '10']

    if use_sudo:
        cmd = ['sudo'] + cmd
    # print in bright white:
    print('\033[1;37m' + ' '.join(cmd) + '\033[0m')
    subprocess.run(
        cmd)


def do_say(msg):
    print(msg)
    subprocess.run(['spd-say', msg])


def get_user_feedback(config, context, speak=False):
    # TODO
    menu_actions = parse_response_file(config.template_name, context)
    if speak:
        # TODO - speak the menu
        do_say('Ready')

    option = choose_option('Options', menu_actions.keys())
    actions = menu_actions.get(option, [])

    for action, params in actions:
        action.run(context, *params)

    finalise_test(context)


def run_test(test_directory, config):
    # Run the test
    print(f"run_test: {test_directory}")

    # Read the scenario
    context = get_context(test_directory)
    print("context:")
    pprint(context)

    scenario_file = context["scenario_file"]
    scenario = next(read_concrete_scenario_csv(scenario_file))
    context["scenario"] = scenario
    pprint(scenario)

    boot_id = context["boot_id"]
    # Gather boot log
    # TODO - don't gather the log if it has already been written and
    #        the size matches.
    write_journal_to_path(test_directory / "journal-k.log", boot_id)
    if context["is_current_boot"] and False:
        # Run s2idle
        run_s2idle(test_directory, config)

    # Ask user for test result
    # TODO
    get_user_feedback(config, context, speak=context["is_current_boot"])


def run_pending_tests(config):
    next_pending_test = setup_next_pending_test_directory()
    run_test(next_pending_test, config)


def test_are_running():
    """
    :return:  True if there are any tests running
    """
    running_directory = Path("runtime") / "running"
    if not running_directory.is_dir():
        return False

    return bool(any(running_directory.iterdir()))


def run_running_tests():
    """
    Run any tests that are currently running.
    """
    running_directory = Path("runtime") / "running"
    for test_directory in running_directory.iterdir():
        config = Config(template_name="power")
        run_test(test_directory, config)


def main():
    # If there are any running tests, then record the results.
    # TODO
    if test_are_running():
        run_running_tests()
        sys.exit(0)

    print("No tests running")

    # If there are any pending tests, then run them.
    # TODO
    if tests_are_pending():
        config = Config(template_name="power")
        run_pending_tests(config)
    else:
        print("No tests pending")


if __name__ == "__main__":
    main()
