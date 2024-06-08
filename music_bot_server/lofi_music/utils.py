import datetime
import logging

logger = logging.getLogger(__name__)
LOG_FILE = 'url_log.txt'
url_log_file = 'url_log.txt'


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
        with open(url_log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1]
                # Split only once to avoid extra parts
                parts = last_line.split(' - ', 1)
                if len(parts) > 1:
                    last_url = parts[1].strip()
                    return last_url
                else:
                    logger.error(f"Unexpected log format: {last_line}")
    except Exception as e:
        logger.error(f"Failed to read the last URL from log file: {
                     e}", exc_info=True)
    return None
