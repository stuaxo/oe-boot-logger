
import csv
import datetime
import functools
import pathlib
import subprocess
import textwrap
#
# LOG_OUTPUT_ROOT = "/home/stu/projects/external/os/linux/logbits/logs"
# TIMEZONE = "Europe/London"
#
#
def parse_date(date_str):
    """
    Parse a journalctl boot log date into a datetime

    :param date_str:
    :return: datetime
    """
    # Parse the start datetime string
    date_str = " ".join(date_str.strip().split(" ")[1:3])
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt


def parse_daterange(daterange_str):
    """
    Parse a journalctl boot log range into a tuple of datetimes

    >>> parse_daterange("Sat 2023-04-01 17:26:32 BST—Sat 2023-04-01 17:28:21 BST")
    (datetime.datetime(2023, 4, 1, 17, 26, 32),
 datetime.datetime(2023, 4, 1, 17, 26, 32))
    """
    start_str, end_str = daterange_str.split("—")

    return parse_date(start_str), parse_date(end_str)


def get_current_boot_id():
    """
    Get the current boot ID from /proc/sys/kernel/random/boot_id
    """
    with open("/proc/sys/kernel/random/boot_id") as f:
        return f.read().strip().replace("-", "")

def get_boot_journals():
    """
    Call journalctl and use pythons CSVReader to parse the output
    journalctl --list-boot

    For each available boot:

    yield bootno: int, uuid: str, dt: datetime
    """
    cmd = ["journalctl", "--list-boot"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)

        # Parse the output line by line using CSV reader
        csv_data = csv.reader(proc.stdout, delimiter=" ", skipinitialspace=True)

        # Skip the header row
        next(csv_data)

        # Iterate over each row and extract the boot number, UUID, and datetime
        for row in csv_data:
            boot_ref = int(row[0])
            boot_id = row[1]
            daterange_str = " ".join(row[2:])

            daterange = parse_daterange(daterange_str)
            yield boot_ref, boot_id, *daterange

    finally:
        # Close the process
        proc.kill()
#
#
# def get_current_build_options(config_keys):
#     """
#     If the kernel was configure with the option CONFIG_IKCONFIG_PROC=y then get the values of the
#     options passed in config_keys from /proc/config.gz and write them to a file in the journal
#     directory, otherwise create an empty file called no_config_gz.
#
#     :param config_keys:
#     :return:
#     """
#     current_boot_id = get_current_boot_id()
#     ensure_logs_dir(current_boot_id)
#
#     # if /proc/config.gz does not exist then touch the file no_config_gz and return
#     current_journal_dir = get_journal_dir(current_boot_id)
#     if not pathlib.Path("/proc/config.gz").exists():
#         (current_journal_dir / "no_config_gz").touch()
#         return
#
#     current_journal_dir.mkdir(parents=True, exist_ok=True)
#
#     # Decompress and open /proc/config.gz read the values of any arguments passed in config_keys
#     # and write them to a file in the journal directory
#     cmd = ["zcat", "/proc/config.gz"]
#     proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
#     try:
#         with (current_journal_dir / "config_options").open("w") as f:
#             for line in proc.stdout:
#                 for key, value in config_keys.items():
#                     if line.startswith(key) or line.startswith(f"# {key} is not set"):
#                         f.write(line)
#     finally:
#         proc.kill()
#
#
def write_journal_to_path(journal_log_path, boot_ref):
    # Write the journalctl output to a file
    cmd = ["journalctl", "-b", str(boot_ref), "-k"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    try:
        with journal_log_path.open("w") as f:
            for line in proc.stdout:
                f.write(line)
    finally:
        proc.kill()
#
#
# @functools.lru_cache(maxsize=1)
# def get_journal_dir(boot_id):
#     # Create a path to the journal file
#     return pathlib.Path(LOG_OUTPUT_ROOT) / "by-id" / boot_id
#
#
# def ensure_logs_dir(boot_id):
#     get_journal_dir(boot_id).mkdir(parents=True, exist_ok=True)
#
#
# def write_boot_journal(boot_ref, boot_id, start_date):
#     journal_dir = get_journal_dir(boot_id)
#
#     is_current = boot_ref == 0
#     was_current = not is_current and (journal_dir / "is_current_boot").exists()
#
#     # Create boot journal file with name in the format boot-journal-YYYYMMDDTHHMMSS
#     journal_log_path = journal_dir / f"boot-journal-{start_date.strftime('%Y%m%dT%H%M')}"
#
#     if is_current:
#         # Create empty file is_current_boot in jounal directory
#         (journal_dir / "is_current_boot").touch()
#     elif was_current and journal_log_path.exists():
#         (journal_dir / "is_current_boot").unlink()
#
#     if not journal_log_path.exists():
#         # Don't write logs that already exist, unless they were created
#         # during a current boot.
#         write_journal_to_path(journal_log_path, boot_ref)
#
#
# def write_bug_summary(boot_ref, boot_id, start_date):
#     journal_dir = get_journal_dir(boot_id)
#
#     # Create bug summary file with name in the format bug-summary-YYYYMMDDTHHMMSS if one doesn't already exist
#     bug_summary_path = journal_dir / f"bug-summary-{start_date.strftime('%Y%m%dT%H%M')}"
#     if not bug_summary_path.exists():
#         bug_text = textwrap.dedent(f"""
#         # Log files are in the directory: file:///{str(journal_dir)}
#
#         # Bug text follows
#         """)
#
#
# def ensure_date_symlink(boot_id, start_date):
#     """
#     Create a symlink to the journal file using the date format YYYYMMDDTHHMMSS
#     """
#
#     by_date = pathlib.Path(LOG_OUTPUT_ROOT) / "by-date"
#     by_date.mkdir(parents=True, exist_ok=True)
#     path = by_date / start_date.strftime("%Y%m%dT%H%M")
#     if not path.exists():
#         path.symlink_to(get_journal_dir(boot_id))
#
#
# def gather_logs(boot_ref, boot_id, start_date):
#     ensure_logs_dir(boot_id)
#     ensure_date_symlink(boot_id, start_date)
#
#     write_boot_journal(boot_ref, boot_id, start_date)
#     write_bug_summary(boot_ref, boot_id, start_date)
