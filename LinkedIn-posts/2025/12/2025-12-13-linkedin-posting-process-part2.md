# December 13, 2025

**LinkedIn Posting Automation Part 2: Testing and Automation**

**Status:** ⏳ Publication pending - LinkedIn URL will be added after posting

---

LinkedIn Posting Automation Part 2: Testing and Automation

After building a style guide for AI-assisted LinkedIn posts, I needed automation: a reliable way to post without manual copy-paste, and tests to verify it works.

I built post-to-linkedin.py to handle OAuth, credential management, and posting. But automation needs tests. So I created a comprehensive test suite with 36 tests covering unit functions, mocked API interactions, and optional real API verification.

𝐖𝐡𝐚𝐭 𝐈 𝐛𝐮𝐢𝐥𝐭:  

▶ Automated posting script (post-to-linkedin.py) with OAuth flow and credential management  
▶ Complete test suite (36 tests) with unit, integration (mocked), and real API tests  
▶ Makefile wrapper for test execution, coverage, and code quality checks  
▶ Testing strategy documentation and README for test usage  

The test suite ensures the posting automation works reliably, with fast mocked tests for development (~0.1s execution) and optional real API tests for final verification.

𝐖𝐡𝐲 𝐈 𝐛𝐮𝐢𝐥𝐭 𝐢𝐭:  

Automation without tests is risky. I needed confidence that the posting script works correctly before using it for real posts. The test suite provides that confidence through comprehensive coverage of all functionality.

The Makefile makes it easy: `make test` for fast feedback, `make test-coverage` for detailed analysis, `make lint` for code quality. It follows the same pattern I use in other projects, ensuring consistency across my tooling.

𝐓𝐡𝐞 𝐭𝐞𝐬𝐭 𝐬𝐭𝐫𝐮𝐜𝐭𝐮𝐫𝐞:  

Unit tests verify pure functions (validate_content, read_post_file, get_post_url, update_markdown_archive). Integration tests with mocked API verify OAuth flow, post creation, and person URN retrieval without real API calls. Optional real API tests provide final verification when needed.

The test suite uses pytest with responses for HTTP mocking, making tests fast and reliable. Test markers (`@pytest.mark.integration`, `@pytest.mark.integration_real`) allow running specific test categories.

𝐓𝐡𝐞 𝐥𝐞𝐬𝐬𝐨𝐧:  

Automation needs testing. The test suite (36 tests, ~0.1s execution) ensures the posting script works correctly. Unit tests verify pure functions, mocked integration tests verify API interactions without real calls, and optional real API tests provide final verification.

The Makefile makes it easy: `make test` for fast feedback, `make test-coverage` for detailed analysis. It's the same principle I use for code: document standards, provide examples, verify compliance. But here, the "code" is automation scripts, and tests are the verification.

Test suite: https://github.com/glblackburn/pub-bin/tree/main/LinkedIn-posts/tests  
Part 1 (Style Guide): https://www.linkedin.com/feed/update/[POST_URL]

#Testing #Automation #Python #Pytest #LinkedIn #OpenSource #QualityAssurance
