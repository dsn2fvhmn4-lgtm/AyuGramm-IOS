"""Stream build diagnostics while redacting configured API values in both sinks."""
import subprocess


def run_logged_build(command, cwd, log_path, secret_values=()):
    secrets = tuple(value for value in secret_values if value)
    with log_path.open('w', encoding='utf-8') as log:
        with subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, encoding='utf-8', errors='replace', bufsize=1) as process:
            for line in process.stdout:
                for value in secrets:
                    line = line.replace(value, '[REDACTED]')
                print(line, end='', flush=True)
                log.write(line)
            result = process.wait()
    if result != 0:
        raise subprocess.CalledProcessError(result, command)
