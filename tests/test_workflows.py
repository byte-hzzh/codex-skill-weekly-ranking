from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parents[1]


def test_collect_workflow_stages_only_generated_paths_before_cached_diff() -> None:
    workflow = yaml.safe_load(
        (PROJECT_ROOT / ".github" / "workflows" / "collect.yml").read_text(encoding="utf-8")
    )
    commit_steps = workflow["jobs"]["commit"]["steps"]
    commit_step = next(
        step for step in commit_steps if step.get("name") == "Commit validated generated changes"
    )
    commands = [line.strip() for line in commit_step["run"].splitlines() if line.strip()]

    stage_command = "git add -- README.md data docs"
    diff_command = "if git diff --cached --quiet -- README.md data docs; then"
    commit_command = 'git commit -m "data: refresh skill ranking" -- README.md data docs'
    stage_commands = [command for command in commands if command.startswith("git add ")]
    commit_commands = [command for command in commands if command.startswith("git commit ")]

    assert stage_commands == [stage_command]
    assert commands.count(diff_command) == 1
    assert commit_commands == [commit_command]
    assert commands.index(stage_command) < commands.index(diff_command)


def test_collect_workflow_separates_read_and_write_permissions() -> None:
    workflow = yaml.safe_load(
        (PROJECT_ROOT / ".github" / "workflows" / "collect.yml").read_text(encoding="utf-8")
    )

    assert workflow["jobs"]["collect"]["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["commit"]["permissions"] == {"contents": "write"}
