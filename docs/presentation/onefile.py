import sys
import os
import fnmatch


def load_patterns(ignore_file):
    base_dir = os.path.dirname(os.path.abspath(ignore_file))
    patterns = []

    with open(ignore_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)

    return base_dir, patterns


def is_ignored(path, base_dir, patterns):
    rel = os.path.relpath(path, base_dir)

    for pat in patterns:
        if fnmatch.fnmatch(rel, pat):
            return True

        if not any(c in pat for c in "*?[]"):
            if rel == pat or rel.startswith(pat + os.sep):
                return True

    return False


def main():
    if len(sys.argv) != 4:
        print("usage: python onefile.py <input_dir> <output_file> <ignore_file>")
        sys.exit(1)

    input_dir = os.path.abspath(sys.argv[1])
    output_file = os.path.abspath(sys.argv[2])
    ignore_file = os.path.abspath(sys.argv[3])
    self_file = os.path.abspath(__file__)

    ignore_base, patterns = load_patterns(ignore_file)
    patterns.extend(
        [
            os.path.relpath(output_file, ignore_base),
            os.path.relpath(self_file, ignore_base),
            os.path.relpath(ignore_file, ignore_base),
        ]
    )

    with open(output_file, "w", encoding="utf-8") as out:
        for root, dirs, files in os.walk(input_dir):
            root_abs = os.path.abspath(root)

            if is_ignored(root_abs, ignore_base, patterns):
                dirs[:] = []
                continue

            dirs[:] = [
                d
                for d in dirs
                if not is_ignored(os.path.join(root_abs, d), ignore_base, patterns)
            ]

            files.sort()
            for name in files:
                path = os.path.abspath(os.path.join(root_abs, name))

                if is_ignored(path, ignore_base, patterns):
                    continue

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue

                rel_path = os.path.relpath(path, input_dir)
                out.write(rel_path + "\n\n")
                out.write(content)
                if not content.endswith("\n"):
                    out.write("\n")
                out.write("\n")


if __name__ == "__main__":
    main()
