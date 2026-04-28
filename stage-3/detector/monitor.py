import time
import json


def tail_log(path):
    """
    Generator function to read a log file in real-time.
    """

    with open(path, "r") as file:
        # Move the cursor to the end of the file
        file.seek(0, 2)

        while True:
            line = file.readline()
            if not line:
                time.sleep(0.05)  # Sleep briefly to avoid busy waiting
                continue
            line = line.strip()
            if line: 
                try:
                    # Attempt to parse the line as JSON
                    data = json.loads(line)
                    yield data
                except json.JSONDecodeError:
                    # If the line is not valid JSON, skip it
                    continue