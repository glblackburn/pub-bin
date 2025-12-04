# LinkedIn Post Style Guide

**Related:** [LinkedIn Posts Archive](LinkedIn-posts.md)

This guide documents the formatting rules, workflow, and style guidelines for creating LinkedIn posts.

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
- **Date Heading Format**: `## [Month Day, Year](LinkedIn-URL)`
- **LinkedIn Link**: `[LinkedIn](LinkedIn-URL)` on the line immediately after the date heading
- **Separator**: Use `---` between posts
- **Paragraph Spacing**: 
  - Blank line after section headings
  - Blank line between major sections
  - No blank lines between consecutive bullet points (they use trailing spaces instead)

**Section Heading Format:**
- Use Unicode bold characters
- End with `:` or `?`
- Add two trailing spaces after the colon/question mark
- Example: `𝐖𝐡𝐚𝐭 𝐈 𝐝𝐢𝐝:  ` or `𝐖𝐡𝐲 𝐭𝐡𝐞 𝐜𝐨𝐧𝐯𝐞𝐫𝐬𝐢𝐨𝐧?  `

**Bullet Point Format:**
- Use `▶` character
- Add two trailing spaces after each bullet line
- Example: `▶ Converted all 8 Ruby scripts to Python  `

**URL Handling:**
- **In Markdown File**: GitHub URLs should NOT have zero-width spaces (for clean, clickable links)
- **In LinkedIn Post Text**: 
  - **File Names**: Add zero-width spaces to file names (e.g., `load-ssh-key​.sh`) to prevent LinkedIn from auto-linking them
  - **URLs**: URLs should NOT have zero-width spaces - they should remain clean and clickable (e.g., `https://github.com/glblackburn/pub-bin/blob/main/load-ssh-key.sh`)
  - **Rationale**: LinkedIn auto-links file names with extensions like `.sh`, `.py`, `.md`, etc. Zero-width spaces prevent this auto-linking for file name references in text, but URLs should remain clean to function as clickable links

**Workflow:**
1. **Draft Post**: Write post content in markdown format
2. **Format for LinkedIn**: 
   - Convert `**text**` to Unicode bold characters
   - Replace bullet points with ▶
   - Add two trailing spaces to all section headings and bullet points
   - Add zero-width spaces to file names (e.g., `script​.sh`) to prevent LinkedIn auto-linking
   - Keep URLs clean (no zero-width spaces) so they remain clickable
3. **Save Temporary File**: Save as plain text file (e.g., `linkedin-post-topic.txt`) for clean copy-paste into LinkedIn
4. **Post to LinkedIn**: Copy-paste from the temporary .txt file and publish on LinkedIn
5. **Get LinkedIn URL**: After posting, copy the direct LinkedIn post URL
6. **Convert to Markdown**: 
   - Add the post to `LinkedIn-posts.md` with proper markdown formatting
   - Use date heading format: `## [Month Day, Year](LinkedIn-URL)`
   - Add `[LinkedIn](LinkedIn-URL)` link below the heading
   - Remove zero-width spaces from GitHub URLs (keep markdown file URLs clean)
   - Ensure all section headings and bullet points have trailing spaces for proper markdown rendering
7. **Clean Up**: Delete the temporary .txt file after the post is added to `LinkedIn-posts.md`

**Verification Checklist:**
- ✅ All section headings have trailing spaces
- ✅ All bullet points have trailing spaces
- ✅ Rendered markdown matches LinkedIn format (each item on its own line)
- ✅ File names in text have zero-width spaces (e.g., `script​.sh`) to prevent auto-linking
- ✅ URLs are clean (no zero-width spaces) and remain clickable
- ✅ Date format is consistent: `[Month Day, Year]`
- ✅ LinkedIn link appears immediately after date heading

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
