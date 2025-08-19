## Brief overview
  - Project-specific rules for NovelCreator Transformer repository.
  - Focus on code cleanup, minimal-diff changes, CLI usage discipline, and text-generation QA loops.
  - Enforce concise, reliable operations on Windows/PowerShell with .conda/python.exe.

## Communication style
  - Default language: Chinese (简洁直接，技术性，避免寒暄)；命令与路径保持英文精确性。
  - Acknowledge constraints explicitly when necessary (e.g., network/API timeout) and provide deterministic fallback.
  - When user says “只使用单一短命令”，always execute exactly one short command per step.

## Development workflow
  - Plan first, then execute; prefer minimal changes that preserve behavior.
  - After every edit or install, verify with a single, focused command.
  - Iterate: edit → run small check → read outputs → continue.
  - For long shell pipelines, split into separate commands across steps.
  - Respect ACT/PLAN modes and tool boundaries; one tool per message.

## Coding best practices
  - Prefer remove unused imports/deps; keep optional TF path but disable heavy features by default unless used.
  - Centralized logger singleton; avoid duplicate handlers; implement verbose flag to control levels.
  - Config keys must match code; remove unused keys; align video settings to code (width/height/fps/etc.).
  - Defensive API usage with timeouts; add retries/backoff for Ollama requests.
  - Regex operations on text must be safe and deterministic; avoid catastrophic patterns.
  - Avoid creating invalid caches (e.g., saving pipeline.state_dict()).

## CLI and environment usage
  - Use .\.conda\python.exe explicitly for all Python invocations.
  - One command per execute_command call; avoid here-doc and multi-line compositions in PowerShell.
  - For quick inspections, prefer small -c Python snippets; when they become long, transform into multiple short commands.
  - Do not assume PATH contains Scripts; avoid relying on transformers-cli or other global binaries.
  - Before executing any command, state the purpose or intent of the command execution.
>>>>>>> REPLACE

## Novel generation QA (M2/M3)
  - M2: Expand chapters toward target length and run Reader review; use sampling for long texts (head/key/tail).
  - M3: Hard length guarantee:
    - Target min non-whitespace chars per chapter: 4000.
    - Steps: multi-round organic expansion → if still short, append supplemental paragraphs until >= target.
    - Use backoff on API timeouts; log warnings but do not break pipeline.
  - Reader review remediation focuses on minimal necessary edits near reported locations; preserve style and facts.
  - Summaries should be 200–400 chars; regenerate if missing/too short.

## File and config conventions
  - Config: keep only used keys. settings.video uses width/height/fps/font_size/text_color/bg_color/margin/line_spacing.
  - Ollama section must contain endpoint/model; trust_remote_code only relevant when TF mode is enabled.
  - Paths resolved relative to repository; avoid hardcoding user-specific paths.

## Testing and diagnostics
  - Use single short commands to:
    - List outputs (e.g., chapters).
    - Count non-whitespace characters for chapters.
    - Print key config fields.
  - When checking chapter metrics, run one command per file to avoid quoting/escaping issues.
  - On API issues, confirm endpoint reachability separately from generation calls.

## Error handling and timeouts
  - Treat HTTP timeouts from Ollama as non-fatal; proceed with backoff and retries where applicable.
  - If a repair step cannot reach target length after configured attempts, log and move to append mode (strategy B).
  - Do not halt full-book generation due to a single chapter’s failure; report and continue.

## Naming and structure
  - Use clear, descriptive method names (e.g., _ensure_min_length, _ensure_hard_min_length_by_append).
  - Prefer lower_snake_case for functions and variables; UpperCamelCase for classes.
  - Avoid introducing new global state; pass through context and configuration as needed.

## Future extensibility (non-blocking)
  - Optional: add dedicated CLI subcommand for chapter-specific length repair (fixlen) operating on one chapter at a time.
  - Optional: write chapter_stats.json capturing per-chapter length, rounds, retries, and review scores.
