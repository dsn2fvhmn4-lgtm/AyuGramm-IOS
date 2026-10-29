#!/usr/bin/env python3
"""Publish the reviewed local IPA inventory using exact GitHub Actions commit boundaries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / 'artifacts/release-history'


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def api(repo, endpoint):
    return json.loads(run('gh', 'api', f'repos/{repo}/{endpoint}'))


def remote_tag(repo, tag):
    result = subprocess.run(['gh', 'api', f'repos/{repo}/git/ref/tags/{quote(tag, safe="")}'], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        if 'HTTP 404' in result.stderr:
            return None
        raise RuntimeError(result.stderr.strip())
    obj = json.loads(result.stdout)['object']
    while obj['type'] == 'tag':
        obj = api(repo, 'git/tags/' + obj['sha'])['object']
    return obj['sha']


def resolve(inventory):
    repo = inventory['repository']
    lines = run('gh', 'api', '--paginate', f'repos/{repo}/actions/workflows/build.yml/runs?per_page=100', '--jq', '.workflow_runs[] | @json')
    runs = {}
    for line in lines.splitlines():
        item = json.loads(line)
        runs[item['run_number']] = item
    releases = run('gh', 'api', '--paginate', f'repos/{repo}/releases?per_page=100', '--jq', '.[] | @json')
    existing = [json.loads(line) for line in releases.splitlines()]
    previous = run('git', 'rev-parse', 'v0.3.0-preview^{commit}')
    plan = []
    for build in inventory['builds']:
        number = build['build']
        if number not in runs:
            raise RuntimeError(f'No build workflow run found for IPA build {number}; refusing to guess its commit.')
        workflow = runs[number]
        commit = workflow['head_sha']
        try:
            run('git', 'cat-file', '-e', commit + '^{commit}')
        except subprocess.CalledProcessError:
            run('git', 'fetch', 'origin', commit)
        run('git', 'merge-base', '--is-ancestor', previous, commit)
        tag = 'v0.4.0-preview' if number == 11 else f'build-{number}'
        for release in existing:
            if any(asset.get('digest') == 'sha256:' + build['sha256'] for asset in release['assets']):
                tag = release['tag_name']
                break
        target = remote_tag(repo, tag)
        if target and target != commit:
            raise RuntimeError(f'Tag {tag} targets {target}, but IPA build {number} comes from {commit}.')
        commits = run('git', 'log', '--reverse', '--topo-order', '--no-merges', '--format=%H%x09%cI%x09%s', previous + '..' + commit)
        lines = [f'AyuGram iOS — сборка {number}', '', f'Telegram {build["version"]}', '', 'Изменения по хронологии коммитов', '']
        for line in commits.splitlines():
            sha, date, subject = line.split('\t', 2)
            lines.append(f'- {date}: {subject} ([{sha[:7]}](https://github.com/{repo}/commit/{sha}))')
        if not commits:
            lines.append('- Повторная сборка тех же исходников.')
        lines.extend(['', f'Исходники: `{commit}`', f'Сборка: [GitHub Actions #{number}]({workflow["html_url"]})', f'Результат CI: {workflow["conclusion"]}', f'SHA-256 IPA: `{build["sha256"]}`', '', 'Новые локальные изменения после этого коммита в данную IPA не входят.', ''])
        notes = HISTORY / 'notes' / f'build-{number}.md'
        notes.write_text('\n'.join(lines), encoding='utf-8')
        plan.append({**build, 'tag': tag, 'commit': commit, 'notes': str(notes), 'existing': next((r for r in existing if r['tag_name'] == tag), None)})
        previous = commit
    (HISTORY / 'resolved-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    return plan


def publish(repo, plan):
    # Check every local file before making any remote changes.
    for build in plan:
        source = Path(build['paths'][0])
        with source.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != build['sha256']:
                raise RuntimeError(f'IPA changed after inventory: {source}')
    for build in plan:
        tag = build['tag']
        asset_name = f'AyuGramm-iOS-build-{build["build"]}.ipa'
        existing = build['existing']
        assets = existing['assets'] if existing else []
        already_uploaded = any(a.get('digest') == 'sha256:' + build['sha256'] for a in assets)
        if not existing:
            run('gh', 'release', 'create', tag, '--repo', repo, '--target', build['commit'], '--draft', '--prerelease', '--latest=false', '--title', f'AyuGram iOS — Build {build["build"]}', '--notes-file', build['notes'])
        with tempfile.TemporaryDirectory(prefix='ayu-release-') as directory:
            asset_path = Path(directory) / asset_name
            if not already_uploaded and any(a['name'] == asset_name for a in assets):
                run('gh', 'release', 'download', tag, '--repo', repo, '--pattern', asset_name, '--dir', directory)
                with asset_path.open('rb') as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != build['sha256']:
                        raise RuntimeError(f'Existing asset {tag}/{asset_name} differs; refusing to overwrite it.')
                already_uploaded = True
            if not already_uploaded:
                asset_path.symlink_to(Path(build['paths'][0]))
                run('gh', 'release', 'upload', tag, str(asset_path), '--repo', repo)
        run('gh', 'release', 'edit', tag, '--repo', repo, '--notes-file', build['notes'], '--draft=false', '--latest=false')
        print(f'Published https://github.com/{repo}/releases/tag/{tag}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', help='Upload IPA files and publish releases after resolving every commit.')
    args = parser.parse_args()
    inventory = json.loads((HISTORY / 'inventory.json').read_text())
    plan = resolve(inventory)
    print(f'Resolved {len(plan)} releases with exact Actions commits. Notes: {HISTORY / "notes"}')
    if args.publish:
        publish(inventory['repository'], plan)


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError, OSError, ValueError, KeyError) as error:
        raise SystemExit(f'Release publication stopped: {error}')
