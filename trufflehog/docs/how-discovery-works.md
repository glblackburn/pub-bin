# How Automatic Discovery Works

## Overview

Automatic discovery is a feature that attempts to find the **paired secret** (e.g., AWS Secret Access Key) near the **primary secret** (e.g., AWS Access Key ID) in the same file, without requiring you to explicitly identify it in the trufflehog report.

## When Discovery Runs

Discovery is attempted when:
1. `--paired-secret` flag is enabled
2. `--paired-secret-identifier` is **NOT** provided (no explicit identifier)
3. `TRUFFLEHOG_OLD_AWS_SECRET_KEY` environment variable is **NOT** set
4. Processing a file that contains a primary secret occurrence

## Discovery Process

### Step 1: Determine Search Range

The script searches **±50 lines** around the primary secret's line number:

```python
search_range = 50  # lines before and after
start_line = max(0, primary_secret_line - search_range - 1)
end_line = min(len(lines), primary_secret_line + search_range)
```

**Example:**
- Primary secret found at line 52
- Search range: lines 2 to 102 (50 lines before and after)

### Step 2: Load Pattern Library

The script uses a set of regex patterns designed to match common AWS Secret Access Key formats:

```python
AWS_SECRET_KEY_PATTERNS = [
    r'(AWS_SECRET_ACCESS_KEY\s*[=:]\s*["\']?)',           # Environment variable
    r'("secretAccessKey"\s*:\s*["\']?)',                  # JSON camelCase
    r'("secret_key"\s*:\s*["\']?)',                       # JSON snake_case
    r'(secret_key\s*[=:]\s*["\']?)',                      # Config file
    r'(AWS_SECRET_KEY\s*[=:]\s*["\']?)',                  # Alternative env var
    r'("[^"]*\.secretKey"\s*:\s*["\']?)',                 # Nested JSON: "aws.sqs.secretKey"
    r'("[^"]*\.awsSecretKey"\s*:\s*["\']?)',             # Nested JSON: "aws.s3.awsSecretKey"
    r'("[^"]*secretKey[^"]*"\s*:\s*["\']?)',              # Any JSON key containing "secretKey"
]
```

### Step 3: Search Each Line

For each line in the search range, the script:

1. **Tries each pattern** against the line
2. **Builds a complete regex** by combining the pattern with a value matcher:
   ```python
   pattern = pattern_prefix + r'(["\']?)([A-Za-z0-9+/=]{30,50})(["\']?)'
   ```
   - Matches optional quotes
   - Matches 30-50 character base64-like strings (AWS Secret Access Keys are typically 40 chars)
   - Matches optional closing quotes

3. **Validates the match**:
   - Length must be between 30-50 characters
   - Must NOT start with "AKIA" (Access Key IDs start with AKIA, not Secret Keys)
   - Must match base64-like pattern (A-Za-z0-9+/=)

### Step 4: Select Best Match

If multiple matches are found, the script selects the one **closest to the primary secret**:

```python
distance = abs(line_num - primary_secret_line)
if distance < best_distance:
    best_match = (line_num, secret_value)
```

**Example:**
- Primary secret at line 52
- Match 1 at line 53 (distance: 1) ✓ Selected
- Match 2 at line 100 (distance: 48)

## Example Discovery Scenario

### File Content (`config.json`):
```json
{
  "aws": {
    "sqs": {
      "automotive_que": {
        "accessKey": "AKIA3RZ4EXAMPLE123",
        "secretKey": "wJalrXUtEXAMPLEKEY1234567890"
      }
    }
  }
}
```

### Discovery Process:

1. **Primary secret found:** Line 4, `"AKIA3RZ4EXAMPLE123"`
2. **Search range:** Lines 1-54 (assuming file has more content)
3. **Pattern matching:**
   - Line 5: Matches pattern `r'("secretKey"\s*:\s*["\']?)'`
   - Extracts value: `wJalrXUtEXAMPLEKEY1234567890`
   - Validates: ✓ 40 chars, ✓ doesn't start with AKIA, ✓ base64-like
4. **Result:** Found at line 5, distance = 1 (closest match)

## Why Discovery Might Fail

Discovery can fail for several reasons:

### 1. **Pattern Mismatch**
The paired secret doesn't match any of the known patterns:
- Custom key names not in the pattern library
- Different format (e.g., encrypted, encoded differently)
- Non-standard structure

**Example failure:**
```json
{
  "credentials": {
    "aws_secret": "wJalrXUt..."  // Pattern doesn't match "aws_secret"
  }
}
```

### 2. **Out of Range**
The paired secret is more than 50 lines away from the primary secret:
- Large configuration files
- Secrets in different sections
- Comments or documentation between secrets

### 3. **Invalid Format**
The value doesn't meet validation criteria:
- Too short (< 30 chars) or too long (> 50 chars)
- Starts with "AKIA" (looks like an Access Key ID)
- Contains invalid characters

### 4. **File Format Issues**
- Binary files
- Encoding issues
- Malformed JSON/configuration

## Debug Mode

With `--debug` flag, you can see exactly what discovery is doing:

```
======================================================================
DEBUG: Processing qa/skai-microservice-automotive_services.json at line 52
======================================================================
Primary secret (old): AKIA3RZ4...5G (length: 20)
Primary secret (new): AKIANEWK...123 (length: 20)
Paired secret (old): Not provided - will attempt automatic discovery
Paired secret (new): wJalrXUt...KEY (length: 40)

Searching for paired secret using 8 pattern(s):
  Pattern 1: (AWS_SECRET_ACCESS_KEY\s*[=:]\s*["\']?)...
  Pattern 2: ("secretAccessKey"\s*:\s*["\']?)...
  Pattern 3: ("secret_key"\s*:\s*["\']?)...

Attempting automatic discovery (searching ±50 lines from line 52)...
  Searching lines 2 to 102 (range: ±50 from line 52)
  Using 8 pattern(s) for paired secret detection
  Found 1 potential paired secret(s):
    Line 53: wJalrXU...7890 (pattern 2, distance 1)
  Selected best match: line 53
  ✓ Found paired secret at line 53
```

## Improving Discovery Success

If discovery fails, you can:

1. **Use explicit mode:** Provide `--paired-secret-identifier` if the paired secret has its own identifier in the report
2. **Set environment variable:** Use `TRUFFLEHOG_OLD_AWS_SECRET_KEY` to provide the old paired secret directly
3. **Interactive prompt:** The script will automatically prompt you if discovery fails
4. **Add patterns:** Extend `AWS_SECRET_KEY_PATTERNS` to match your specific format

## Pattern Examples

### Environment Variables
```bash
AWS_SECRET_ACCESS_KEY=wJalrXUt...
AWS_SECRET_KEY=wJalrXUt...
```

### JSON Files
```json
{
  "secretAccessKey": "wJalrXUt...",
  "secret_key": "wJalrXUt...",
  "aws.sqs.secretKey": "wJalrXUt...",
  "aws.s3.awsSecretKey": "wJalrXUt..."
}
```

### Config Files
```ini
secret_key = wJalrXUt...
secret_key: wJalrXUt...
```

## Limitations

1. **Single file only:** Discovery only works within the same file
2. **Proximity required:** Secrets must be within 50 lines of each other
3. **Pattern-dependent:** Only matches known patterns
4. **No validation of relationship:** Doesn't verify the paired secret actually belongs to the primary secret (just finds the closest match)

## Future Enhancements

Potential improvements:
- Configurable search range
- Support for other secret types (not just AWS)
- Cross-file discovery (for secrets in related files)
- Relationship validation (verify paired secret belongs to primary secret)
- Machine learning pattern detection
- Custom pattern configuration file
