# LinkedIn Post Style Guide

**Related:** [LinkedIn Posts Archive](LinkedIn-posts.md)  
**Examples:** 
- [`examples/2025-12-12-network-capture-analysis-tools.txt`](examples/2025-12-12-network-capture-analysis-tools.txt) - LinkedIn-ready plain text format
- [`examples/2025-12-12-network-capture-analysis-tools.md`](examples/2025-12-12-network-capture-analysis-tools.md) - Markdown format for post history in git repo

This guide documents the formatting rules, workflow, and style guidelines for creating LinkedIn posts.

## Example Posts

See the example files in `examples/` for complete, properly formatted LinkedIn posts:

- **Plain Text Format** ([`2025-12-12-network-capture-analysis-tools.txt`](examples/2025-12-12-network-capture-analysis-tools.txt)) - Ready to post with `post-to-linkedin.py`, demonstrates:
- Unicode bold section headings with trailing spaces
- Bullet points with trailing spaces and no blank lines between them
- Zero-width spaces in file names
- Clean URLs
- Proper paragraph spacing
- Character count under 3,000 limit

- **Markdown Format** ([`2025-12-12-network-capture-analysis-tools.md`](examples/2025-12-12-network-capture-analysis-tools.md)) - Format for post history in git repo, demonstrates:
- Draft post structure with status message (no placeholder URLs)
- Proper markdown formatting for archive
- Date heading format for unpublished posts
- How to structure posts before adding LinkedIn URL

## Formatting Reference for LinkedIn Posts

**Formatting Style:**
- **Section Headers**: Use Unicode bold characters (𝐖𝐡𝐚𝐭, 𝐓𝐡𝐞, etc.) instead of markdown `**bold**`
- **Bullet Points**: Use ▶ (black right-pointing triangle) instead of • or *
- **File Names**: Include zero-width space (​) in file names (e.g., `script​.sh`) to prevent LinkedIn auto-linking
- **URLs**: Keep URLs clean (no zero-width spaces) so they remain clickable
- **Text File**: Generate posts as plain text files (no markdown code blocks) to avoid line numbers when copying

**Unicode Characters Used:**
- Bold text: Mathematical Bold Unicode (𝐀-𝐙, 𝐚-𝐳, 𝟎-𝟗)
- Bullets: ▶ (U+25B6 - Black Right-Pointing Triangle)

**Markdown Line Breaks:**
- **Section Headings**: Must end with two trailing spaces (`  `) after the colon/question mark to force line breaks in markdown rendering
  - Example: `𝐖𝐡𝐚𝐭 𝐈 𝐝𝐢𝐝:  ` (note the two spaces)
- **Bullet Points**: Must end with two trailing spaces (`  `) after each bullet line to ensure proper rendering
  - Example: `▶ Item text  ` (note the two spaces)
- This ensures each item renders on its own line, matching LinkedIn's format

**Post Structure:**
- **Date Heading Format**: 
  - **For Draft Posts**: `## December 12, 2025` (no URL placeholder)
  - **For Published Posts**: `## [December 12, 2025](LinkedIn-URL)` (with real URL)
- **Status for Draft Posts**: Use `**Status:** ⏳ Publication pending - LinkedIn URL will be added after posting` instead of placeholder URLs
- **LinkedIn Link**: `[LinkedIn](LinkedIn-URL)` on the line immediately after the date heading (only for published posts)
- **Separator**: Use `---` between posts
- **Paragraph Spacing**: 
  - Blank line after section headings
  - Blank line between major sections
  - **No blank lines between consecutive bullet points** - Bullet points must appear consecutively without blank lines between them (they use trailing spaces instead)
  - Example: See `examples/2025-12-12-network-capture-analysis-tools.txt` for correct formatting

**Section Heading Format:**
- Use Unicode bold characters
- End with `:` or `?`
- Add two trailing spaces after the colon/question mark
- Example: `𝐖𝐡𝐚𝐭 𝐈 𝐝𝐢𝐝:  ` or `𝐖𝐡𝐲 𝐭𝐡𝐞 𝐜𝐨𝐧𝐯𝐞𝐫𝐬𝐢𝐨𝐧?  `

**Bullet Point Format:**
- Use `▶` character
- Add two trailing spaces after each bullet line
- **No blank lines between consecutive bullet points** - They must appear consecutively
- Example: `▶ Converted all 8 Ruby scripts to Python  `
- See `examples/2025-12-12-network-capture-analysis-tools.txt` for complete example

**URL Handling:**
- **In Markdown File**: GitHub URLs should NOT have zero-width spaces (for clean, clickable links)
- **In LinkedIn Post Text**: 
  - **File Names**: Add zero-width spaces to file names (e.g., `load-ssh-key​.sh`) to prevent LinkedIn from auto-linking them
  - **URLs**: URLs should NOT have zero-width spaces - they should remain clean and clickable (e.g., `https://github.com/glblackburn/pub-bin/blob/main/load-ssh-key.sh`)
  - **Rationale**: LinkedIn auto-links file names with extensions like `.sh`, `.py`, `.md`, etc. Zero-width spaces prevent this auto-linking for file name references in text, but URLs should remain clean to function as clickable links

**Markdown Archive Index Formatting:**
- **File Names in Index**: Use backticks around file names with extensions (e.g., `` `load-ssh-key.sh` ``, `` `README.md` ``) in the archive index (`LinkedIn-posts.md`) to prevent markdown renderers from auto-linking them
- **Applies To**: Script filenames (`.sh`), documentation filenames (`.md`), and other file references in the Table of Contents and Quick Index table
- **Rationale**: Markdown renderers may auto-link file names with common extensions. Using backticks formats them as inline code and prevents unwanted auto-linking while maintaining readability

**Workflow:**
1. **Draft Post**: Write post content in markdown format
   - Use `## December 12, 2025` (no URL) for date heading
   - Add `**Status:** ⏳ Publication pending - LinkedIn URL will be added after posting` below date heading
   - **Do NOT use placeholder URLs** like `activity-XXXXX` - use status message instead
2. **Format for LinkedIn**: 
   - Convert `**text**` to Unicode bold characters
   - Replace bullet points with ▶
   - Add two trailing spaces to all section headings and bullet points
   - **Remove all blank lines between consecutive bullet points** - They must appear consecutively
   - Add zero-width spaces to file names (e.g., `script​.sh`) to prevent LinkedIn auto-linking
   - Keep URLs clean (no zero-width spaces) so they remain clickable
3. **Check Content Length**: Always verify the character count of the LinkedIn-formatted post text before finalizing. LinkedIn's character limit for regular posts is **3,000 characters**. Posts should be trimmed if they exceed this limit. Count characters in the plain text version (the .txt file content).
4. **Save as .txt File**: Save as plain text file (e.g., `2025-12-13-linkedin-posting-process.txt`) in the appropriate date directory
5. **Post to LinkedIn**: Use the posting script to post automatically:
   ```bash
   cd LinkedIn-posts
   python3 post-to-linkedin.py 2025/12/2025-12-13-linkedin-posting-process.txt
   ```
   - The script validates content length automatically
   - Posts to LinkedIn via API
   - Opens your LinkedIn activity page after successful posting
   - Shows post ID and any available URL information
6. **Get LinkedIn URL**: 
   - The script opens your LinkedIn activity page automatically
   - Find your post in the activity feed
   - Click on the post timestamp or '...' menu to copy the post URL
   - Alternatively, the script may show the post URL if available from the API
7. **Update Markdown File**: 
   - Update the markdown version of the post (e.g., `2025-12-13-linkedin-posting-process.md`)
   - Replace status message with date heading format: `## [December 13, 2025](LinkedIn-URL)`
   - Add `[LinkedIn](LinkedIn-URL)` link below the heading
   - Remove zero-width spaces from GitHub URLs (keep markdown file URLs clean)
   - Ensure all section headings and bullet points have trailing spaces for proper markdown rendering
   - Ensure no blank lines between consecutive bullet points
8. **Optional Clean Up**: The .txt file can be kept for reference or deleted if desired

**Verification Checklist:**
- ✅ Content length has been checked and is within LinkedIn's character limit (3,000 characters)
- ✅ All section headings have trailing spaces
- ✅ All bullet points have trailing spaces
- ✅ **No blank lines between consecutive bullet points**
- ✅ Rendered markdown matches LinkedIn format (each item on its own line)
- ✅ File names in LinkedIn post text have zero-width spaces (e.g., `script​.sh`) to prevent auto-linking
- ✅ File names in markdown archive index use backticks (e.g., `` `script.sh` ``, `` `README.md` ``) to prevent auto-linking
- ✅ URLs are clean (no zero-width spaces) and remain clickable
- ✅ Date format is consistent: `[Month Day, Year]` for published, `December 12, 2025` for drafts
- ✅ Draft posts use status message instead of placeholder URLs
- ✅ LinkedIn link appears immediately after date heading (published posts only)

**Tone and Writing Style Rules:**

- **Overall Tone:**
  - **Conversational and Direct**: Write as if talking to a colleague, not giving a formal presentation
  - **First-Person Perspective**: Use "I" and "my" - these are personal experiences and workflows
  - **Honest and Transparent**: Share both successes and failures, including AI coding assistant mistakes
  - **Practical and Pragmatic**: Focus on real-world constraints and what actually works
  - **Not Overly Promotional**: Avoid marketing speak; let the work speak for itself
  - **Technical but Accessible**: Use technical terms when appropriate, but explain context

- **Opening Styles:**
  - **Question Hooks**: Start with engaging questions (e.g., "Is Ruby Dead?", "What happens when you challenge...")
  - **Direct Statements**: Lead with what you just did or discovered (e.g., "Just finished...", "I've been using...")
  - **Personal Narrative**: Share the story or context (e.g., "So I've started a thing...", "So I did a different thing this morning...")
  - **Avoid**: Generic openings, overly formal introductions, or "I'm excited to share..."

- **Language Patterns:**
  - **Use Contractions**: "I've", "it's", "don't", "can't" - makes it conversational
  - **Casual Phrases When Appropriate**: "come on", "way longer than it should have", "ticked all the boxes"
  - **Direct Statements**: "The real reason...", "The reality is...", "Sometimes..."
  - **Avoid**: Corporate jargon, buzzwords, excessive enthusiasm, or overly formal language

- **Content Structure:**
  - **Provide Context**: Include specific details (dates, versions, project names, file paths)
  - **Share the Journey**: Explain what you tried, what worked, what didn't, and why
  - **Include Lessons**: Extract practical takeaways from experiences
  - **Be Honest About AI**: Discuss both benefits and limitations of AI coding assistants
  - **Link to Actual Work**: Always provide links to code, repos, or documentation

- **Section Organization:**
  - **Use Structured Sections**: Unicode bold headers (𝐖𝐡𝐚𝐭 𝐈 𝐝𝐢𝐝, 𝐓𝐡𝐞 𝐥𝐞𝐬𝐬𝐨𝐧, etc.)
  - **Bullet Points for Lists**: Break up dense information into scannable bullets
  - **Paragraph Length**: Keep paragraphs concise (2-4 sentences typically)
  - **Flow**: Hook → Context → Details → Lesson/Insight → Link

- **Ending Styles:**
  - **Practical Takeaways**: Summarize what others can learn or apply
  - **Engaging Questions**: Ask for audience experience or thoughts
  - **Brief Project Description**: One-line summary of what the project/tool does
  - **Links**: Always include relevant GitHub links or resources
  - **Avoid**: Call-to-actions that feel salesy, overly long conclusions

- **Specific Patterns:**
  - **AI Coding Assistant Posts**: 
    - Acknowledge both benefits and limitations
    - Share specific examples of issues encountered
    - Emphasize the importance of testing and verification
    - Be honest about what AI got wrong
  - **Technical Posts**:
    - Explain the "why" behind technical decisions
    - Share constraints and practical considerations
    - Avoid language wars or superiority claims
    - Focus on what works in your specific environment
  - **Workflow Posts**:
    - Describe the actual process, not just the outcome
    - Share what you learned along the way
    - Explain how it fits into your daily work
    - Be specific about tools and methods

- **What to Avoid:**
  - ❌ Overly enthusiastic language ("I'm thrilled!", "Amazing results!")
  - ❌ Generic advice without personal context
  - ❌ Hiding mistakes or failures
  - ❌ Overly technical jargon without explanation
  - ❌ Long, dense paragraphs without breaks
  - ❌ Promotional or sales-focused language
  - ❌ Making absolute claims about tools or methods
  - ❌ Ignoring or glossing over AI limitations

- **Length Guidelines:**
  - **Medium Length**: Enough to provide context and value, but not so long it's overwhelming
  - **Paragraphs**: 2-4 sentences typically
  - **Bullet Lists**: 3-7 items work well
  - **Overall**: Aim for scannable content that provides value without requiring deep focus
