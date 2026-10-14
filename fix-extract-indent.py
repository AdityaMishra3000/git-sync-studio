with open("apps/api/app/readme/extract.py", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i == 17 and line.startswith('if (repo_path'):
        new_lines.append('    ' + line)
    elif i >= 27 and i <= 43 and line.startswith('    elif'):
        # already properly indented or maybe need to ensure it's 4 spaces
        # actually let's just make sure all of them are exactly 4 spaces
        new_lines.append(line)
    else:
        new_lines.append(line)

with open("apps/api/app/readme/extract.py", "w") as f:
    f.writelines(new_lines)

print("Indentation fixed.")
