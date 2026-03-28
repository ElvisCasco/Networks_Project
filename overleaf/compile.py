import subprocess
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

commands = [
    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
    ["bibtex", "main"],
    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
]

for cmd in commands:
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "bibtex" not in cmd[0]:
        print(f"Error:\n{result.stdout[-500:]}")
        break
    print("OK")

print("\nDone. Output: main.pdf")
