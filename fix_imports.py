import os
import fileinput
import sys

# Target directories
dirs_to_scan = ["app", "locustfiles"]
targets = []

for d in dirs_to_scan:
    if os.path.exists(d):
        for root, dirs, files in os.walk(d):
            for name in files:
                if name.endswith(".py"):
                    targets.append(os.path.join(root, name))

print(f"Scanning {len(targets)} files...")
for file in targets:
    try:
        with fileinput.FileInput(file, inplace=True) as f:
            for line in f:
                # Replace exact package import start
                # from locust_app... -> from app...
                line = line.replace("from locust_app", "from app")
                # import locust_app -> import app
                line = line.replace("import locust_app", "import app")
                print(line, end='')
    except Exception as e:
        sys.stderr.write(f"Error processing {file}: {e}\n")

print("Done.")
