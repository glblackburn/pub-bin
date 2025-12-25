# Paired Secret Rotation Example

## Example: Rotating AWS Access Key Pair

This example shows how to rotate an AWS Access Key ID and Secret Access Key pair using the identifier from a trufflehog report.

### Scenario

You have a trufflehog analysis report that identified an AWS Access Key ID with identifier `RAW_c25c34ee_bb9c4917`. The Secret Access Key is in the same files but wasn't detected separately by trufflehog.

### Step 1: Dry-Run with Automatic Discovery

Run the script in dry-run mode to see what changes will be made:

```bash
./trufflehog/scripts/trufflehog-rotate-aws-key.py \
    -r /path/to/tokenized_analysis_20251217_180420.md \
    -i RAW_c25c34ee_bb9c4917 \
    --paired-secret \
    -p \
    --prompt-paired-secret \
    --mode dry-run
```

**What happens:**
1. Script prompts for new Access Key ID (input is hidden)
2. Script prompts for new Secret Access Key (input is hidden)
3. Script searches for the old Access Key ID in all repositories
4. For each file containing the Access Key ID, script searches within ±50 lines for the Secret Access Key
5. Script creates branches and makes replacements (but doesn't commit)
6. You can review the changes before committing

### Step 2: Review Changes

After the dry-run completes:
1. Check the working directory (shown in output, typically `/tmp/trufflehog-rotate-YYYYMMDD-HHMMSS`)
2. Review the branches created in each repository
3. Verify that both Access Key ID and Secret Access Key were replaced correctly

### Step 3: Commit Changes

Once you've verified the changes are correct, commit them:

```bash
./trufflehog/scripts/trufflehog-rotate-aws-key.py \
    --resume \
    -i RAW_c25c34ee_bb9c4917 \
    --paired-secret \
    --mode commit
```

**Note:** The new secrets are not required in resume mode since they were already used to make the changes. The script will verify hashes if you provide them.

### Alternative: Using Environment Variables (for automation)

If you're automating this process, you can use environment variables:

```bash
# Set environment variables
export TRUFFLEHOG_NEW_AWS_KEY="AKIANEWKEYEXAMPLE123"
export TRUFFLEHOG_NEW_AWS_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYNEWKEY"

# Run dry-run
./trufflehog/scripts/trufflehog-rotate-aws-key.py \
    -r /path/to/tokenized_analysis_20251217_180420.md \
    -i RAW_c25c34ee_bb9c4917 \
    --paired-secret \
    --mode dry-run
```

**Security Note:** Environment variables are visible in process lists. Use interactive prompts (`-p` and `--prompt-paired-secret`) for maximum security.

### What the Script Does

1. **Parses the report** to find all occurrences of `RAW_c25c34ee_bb9c4917`
2. **Clones repositories** that contain this identifier
3. **Creates branches** with names like `rotate-aws-key-c25c34ee-20251224-143000`
4. **Finds paired secrets** automatically by searching for AWS Secret Access Key patterns near the Access Key ID
5. **Replaces both secrets** atomically (if in same file) or separately (if in different files)
6. **Creates backups** of modified files in `~/.secure/trufflehog-rotate/backups/`
7. **Saves state** to `~/.secure/trufflehog-rotate/RAW_c25c34ee_bb9c4917-*.json`

### Expected Output

```
Parsing report: /path/to/tokenized_analysis_20251217_180420.md
──────────────────────────────────────────────────────────────────────
Configuration:
  Working directory: /tmp/trufflehog-rotate-20251224-143000
  Repositories will be cloned to: /tmp/trufflehog-rotate-20251224-143000/repos
  Backup directory: /Users/username/.secure/trufflehog-rotate/backups
──────────────────────────────────────────────────────────────────────
Processing paired secret rotation for identifier: RAW_c25c34ee_bb9c4917
Old primary key: AKIA3RZ4... (hidden)
New primary key: ******** (hidden)
Old paired secret: (will be discovered per-file)
New paired secret: ******** (hidden)
Repositories to process: 5
──────────────────────────────────────────────────────────────────────

[1/5] Processing skaivision/devops-config-secure_parameters-gitops...
  ✓ Status: completed
  ✓ Files modified: 38

[2/5] Processing skaivision/another-repo...
  ✓ Status: completed
  ✓ Files modified: 12

...

──────────────────────────────────────────────────────────────────────
Summary:
  Total repositories: 5
  Completed: 5
  Failed: 0
  Skipped: 0

State saved to: /Users/username/.secure/trufflehog-rotate/RAW_c25c34ee_bb9c4917-2025-12-24T14:30:00.json

To commit changes, run:
  ./trufflehog/scripts/trufflehog-rotate-aws-key.py --resume -i RAW_c25c34ee_bb9c4917 --paired-secret --mode commit
```

### Troubleshooting

**If automatic discovery fails:**
- The script will skip files where it can't find the paired secret
- Use `--verbose` to see detailed information about what was searched
- If the Secret Access Key is in a different file, you'll need to use explicit mode with `--paired-secret-identifier` (if the paired secret has its own identifier in the report)

**If you see warnings:**
- `WARNING: Paired secret not found for file:line` - The script couldn't find the Secret Access Key near the Access Key ID. Check if it's in a different location or file.

### Next Steps

After committing:
1. Review the changes in the created branches
2. Push branches if needed: `--resume -i RAW_c25c34ee_bb9c4917 --paired-secret --push`
3. Create pull requests if needed: `--resume -i RAW_c25c34ee_bb9c4917 --paired-secret --create-pr`
