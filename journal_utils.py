import csv
import datetime
import subprocess


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
