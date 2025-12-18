# Draft Posts Organization Proposal

**Date:** December 18, 2025
**Issue:** Draft posts are currently stored in dated folders with date headers, which is misleading since they haven't been published yet.

## Current Problem

- Drafts are mixed with published posts in `2025/12/`
- Drafts have dates in headers (e.g., `# December 18, 2025`), which implies publication dates
- Hard to distinguish drafts from published content
- No clear separation between work-in-progress and published content

## Proposed Solution

### 1. **Folder Structure Reorganization**

**Current Structure:**
```
LinkedIn-posts/
├── 2025/
│   └── 12/
│       ├── 2025-12-13-linkedin-posting-process-part2.md (DRAFT)
│       ├── 2025-12-09-react2shell-server-part3.txt (DRAFT)
│       └── 2025-12-15-react2shell-server-part2.md (PUBLISHED)
```

**Proposed Structure:**
```
LinkedIn-posts/
├── drafts/                          # All draft posts
│   ├── linkedin-posting-process-part2.md
│   ├── linkedin-posting-process-part2.txt
│   ├── react2shell-server-part3.txt
│   └── react2shell-server-part4.txt
├── 2025/                            # Published posts only
│   ├── 12/
│   │   ├── 18/                      # Published on specific day
│   │   │   ├── 2025-12-18-linkedin-posting-process-part1.md
│   │   │   └── 2025-12-18-linkedin-posting-process-part1.txt
│   │   └── 2025-12-15-react2shell-server-part2.md
│   └── 11/
└── LinkedIn-posts.md                # Index file
```

### 2. **Draft Post Header Format**

**Current (Problematic):**
```markdown
# December 18, 2025

**LinkedIn Posting Automation Part 2: Testing and Automation**

**Status:** ⏳ Publication pending - LinkedIn URL will be added after posting
```

**Proposed:**
```markdown
# LinkedIn Posting Automation Part 2: Testing and Automation

**Status:** ⏳ Publication pending - LinkedIn URL will be added after posting
```

**Alternative (if you want to mark as draft):**
```markdown
# Draft: LinkedIn Posting Automation Part 2: Testing and Automation

**Status:** ⏳ Publication pending - LinkedIn URL will be added after posting
```

**Key Changes:**
- Remove publication date from header (drafts don't have publication dates yet)
- Keep status line to indicate it's a draft
- Title becomes the primary header

### 3. **Publication Workflow**

When a draft is published:

1. **Move files** from `drafts/` to appropriate `YYYY/MM/DD/` folder
2. **Add date header** with LinkedIn URL: `## [December 18, 2025](URL)`
3. **Update `LinkedIn-posts.md` index** (move from Draft to Published section)
4. **Update any cross-references** (e.g., Part 2 referencing Part 1)

**Example:**
```
Before (Draft):
drafts/linkedin-posting-process-part2.md
  → # LinkedIn Posting Automation Part 2: Testing and Automation

After (Published):
2025/12/18/linkedin-posting-process-part2.md
  → ## [December 18, 2025](https://www.linkedin.com/posts/...)
```

### 4. **Index File Updates**

**Draft Posts section:**
```markdown
### Draft Posts

- ⏳ [LinkedIn Posting Automation Part 2: Testing and Automation](drafts/linkedin-posting-process-part2.md) - After building a style guide, I needed automation and tests to verify it works.
- ⏳ [React2Shell Server Part 3: Performance Optimization](drafts/react2shell-server-part3.txt)
- ⏳ [React2Shell Server Part 4: Lessons Learned](drafts/react2shell-server-part4.txt)
```

**Published Posts section:**
```markdown
### Published Posts

#### December 2025

- ✅ [December 18, 2025](2025/12/18/2025-12-18-linkedin-posting-process-part1.md) - LinkedIn Posting Automation Part 1: Building a Style Guide for AI-Assisted Content
```

### 5. **Benefits**

✅ **Clear separation:** Drafts vs published content
✅ **No date confusion:** Drafts don't imply publication dates
✅ **Easier to find:** All drafts in one place
✅ **Cleaner published folders:** Only published content in date folders
✅ **Better workflow:** Clear path from draft → published
✅ **Accurate representation:** Draft headers reflect actual status

### 6. **Migration Steps** (if approved)

1. Create `LinkedIn-posts/drafts/` directory
2. Move draft files from `2025/12/` to `drafts/`
   - `2025-12-13-linkedin-posting-process-part2.md` → `drafts/linkedin-posting-process-part2.md`
   - `2025-12-13-linkedin-posting-process-part2.txt` → `drafts/linkedin-posting-process-part2.txt`
   - `2025-12-09-react2shell-server-part3.txt` → `drafts/react2shell-server-part3.txt`
   - `2025-12-09-react2shell-server-part4.txt` → `drafts/react2shell-server-part4.txt`
3. Remove date headers from draft markdown files
4. Update `LinkedIn-posts.md` index with new paths
5. Update any cross-references (like Part 2 referencing Part 1)
6. Update style guide if needed to reflect new structure

### 7. **Alternative: Keep Current Structure**

If you prefer to keep drafts in dated folders:

**Option A: Drafts subfolder within months**
```
LinkedIn-posts/
├── 2025/
│   └── 12/
│       ├── drafts/
│       │   ├── linkedin-posting-process-part2.md
│       │   └── react2shell-server-part3.txt
│       └── 2025-12-15-react2shell-server-part2.md (published)
```

**Option B: Keep in month folder, remove date headers**
- Keep files in `2025/12/` but remove date headers
- Use creation date in filename only (for organization)
- No date in markdown header until published

## Questions to Consider

1. **Folder structure preference:**
   - Separate `drafts/` folder at root? (Recommended)
   - Or `2025/12/drafts/` subfolder?
   - Or keep in month folder, just remove date headers?

2. **Draft header format:**
   - Title only? (Recommended)
   - Or "Draft: Title"?
   - Or keep creation date for reference?

3. **Filename convention:**
   - Remove dates from draft filenames? (e.g., `linkedin-posting-process-part2.md`)
   - Or keep dates for organization? (e.g., `2025-12-13-linkedin-posting-process-part2.md`)

4. **Style guide updates:**
   - Update `LinkedIn-style-guide.md` to document new draft structure?
   - Update directory structure diagram?

## Recommendation

**Preferred approach:** Separate `drafts/` folder with title-only headers

- Cleanest separation
- No date confusion
- Easy to find all drafts
- Clear publication workflow
- Matches common content management patterns
