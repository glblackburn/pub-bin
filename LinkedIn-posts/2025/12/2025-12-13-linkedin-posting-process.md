# December 13, 2025

**LinkedIn Posting Automation: Building a Test Suite and Workflow**

**Status:** ⏳ Publication pending - LinkedIn URL will be added after posting

---

LinkedIn Posting Automation: Building a Test Suite and Workflow

What happens when you want an AI coding assistant to help craft LinkedIn posts about your code, but it needs context and consistency?

I've been using Cursor to help write LinkedIn posts about my open-source projects. The challenge: Cursor needs to understand the codebase, commit history, and project context to craft meaningful posts. But without clear guidelines, each post came out differently—inconsistent formatting, varying tone, different structures.

So I built a style guide that lets Cursor leverage the codebase and commit history to create consistent, context-aware posts. Then I automated the posting process and built a comprehensive test suite.

𝐖𝐡𝐚𝐭 𝐈 𝐛𝐮𝐢𝐥𝐭:  

▶ Comprehensive style guide covering formatting rules, workflow, and tone  
▶ Automated posting script (post-to-linkedin.py) with OAuth flow and credential management  
▶ Complete test suite (36 tests) with unit, integration (mocked), and real API tests  
▶ Makefile wrapper for test execution, coverage, and code quality checks  
▶ Example posts (both .txt and .md formats) demonstrating proper formatting  
▶ Workflow documentation from draft to published post  
▶ Testing strategy documentation and README for test usage  

The style guide covers formatting rules, tone guidelines, workflow documentation, and example posts that Cursor can reference. The test suite ensures the posting automation works reliably, with fast mocked tests for development and optional real API tests for verification.

𝐖𝐡𝐲 𝐈 𝐛𝐮𝐢𝐥𝐭 𝐢𝐭:  

I started using Cursor for posts back in November. It could read scripts, understand commit messages, and pull context from the codebase—perfect for technical posts. But without standards, Cursor formatted things differently each time.

I needed a contract: clear rules so Cursor could craft consistent, properly formatted posts that leverage codebase context. The style guide became that contract. Then I needed automation: a reliable way to post without manual copy-paste, and tests to verify it works.

𝐓𝐡𝐞 𝐩𝐫𝐨𝐜𝐞𝐬𝐬:  

The style guide evolved over a dozen posts, starting with basic formatting rules in early December, then expanding to include tone and writing style. Each post revealed new requirements: Unicode bold headers work, markdown code blocks don't. LinkedIn auto-links file names, so zero-width spaces prevent that.

The December 12 post went through full validation—that's when I realized Cursor needed example files. So I created both .txt (for LinkedIn) and .md (for git history) examples. Now Cursor can reference actual working examples and leverage commit history to craft context-aware posts.

Then came automation: I built post-to-linkedin.py to handle OAuth, credential management, and posting. But automation needs tests. So I created a comprehensive test suite with 36 tests covering unit functions, mocked API interactions, and optional real API verification. The Makefile makes it easy to run tests, check coverage, and maintain code quality.

𝐓𝐡𝐞 𝐥𝐞𝐬𝐬𝐨𝐧:  

When you want AI to help with content creation, give it clear contracts. The style guide lets Cursor read codebase and commit history, follow consistent formatting rules, and reference working examples when crafting posts.

It's the same principle I use for code: document standards, provide examples, verify compliance. But here, the "developer" is Cursor, and the "code" is LinkedIn posts. The style guide is the contract that makes AI-assisted content creation reliable.

Automation needs testing. The test suite (36 tests, ~0.1s execution) ensures the posting script works correctly. Unit tests verify pure functions, mocked integration tests verify API interactions without real calls, and optional real API tests provide final verification. The Makefile makes it easy: `make test` for fast feedback, `make test-coverage` for detailed analysis.

The style guide: https://github.com/glblackburn/pub-bin/blob/main/LinkedIn-posts/LinkedIn-style-guide.md  
Test suite: https://github.com/glblackburn/pub-bin/tree/main/LinkedIn-posts/tests

#ContentCreation #Documentation #Workflow #LinkedIn #OpenSource #TechnicalWriting #Testing #Automation
