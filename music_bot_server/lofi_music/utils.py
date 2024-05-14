import datetime

LOG_FILE = 'url_log.txt'


def log_url(url):
    # Read the existing log file lines
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    # Append the new log line
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_log_line = f"{timestamp} {url}\n"
    lines.append(new_log_line)

    # Ensure only the last 25 lines are kept
    lines = lines[-25:]

    # Write the updated lines back to the log file
    with open(LOG_FILE, 'w') as f:
        f.writelines(lines)


def get_last_url():
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            if lines:
                last_log_line = lines[-1]
                # Extract the URL part
                return last_log_line.split(' ', 1)[1].strip()
    except FileNotFoundError:
        return None

    return None
