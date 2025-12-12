## [December 12, 2025](https://www.linkedin.com/posts/activity-XXXXX)

[LinkedIn](https://www.linkedin.com/posts/activity-XXXXX)

---

A Basic Tool for Analyzing tcpdump Output

Built a simple Python tool to parse tcpdump output and extract basic statistics. Nothing fancy, but it solves a common problem. 🛠️

𝐖𝐡𝐚𝐭 𝐢𝐭 𝐝𝐨𝐞𝐬:  

`analyze-tcpdump​.py` - A basic parser that extracts:  
▶ IP addresses (source, destination, unique counts)  
▶ Connection pairs  
▶ Port usage statistics  
▶ Protocol breakdown (TCP, UDP, ICMP, QUIC)  
▶ Basic filtering by protocol, IP, or port  

It's essentially a structured way to get summary statistics from tcpdump text output. Handles decent-sized captures (tested with 100K+ packets) and outputs in multiple formats including CSV.

𝐖𝐡𝐲 𝐈 𝐛𝐮𝐢𝐥𝐭 𝐢𝐭:  

Sometimes you just need a quick summary of what's in a tcpdump file—top IPs, protocol distribution, port usage. Instead of manually parsing or writing one-off scripts, this provides a reusable tool with consistent output.

The `sanitize-analysis-ipmask​.py` script masks private IPs when sharing examples publicly. It replaces the 2nd and 3rd octets with random two-letter combinations (G-Z, uppercase) while preserving relationships—useful for documentation or blog posts. It can auto-discover the latest analysis file, so you can just run it without specifying input.

𝐓𝐡𝐞 𝐭𝐞𝐜𝐡𝐧𝐢𝐜𝐚𝐥 𝐬𝐢𝐝𝐞:  

▶ 94% test coverage - Comprehensive test suite (95 tests) covering unit, integration, and CLI scenarios  

▶ Clean code structure - Separated parsing, analysis, and output formatting  

▶ Developer-friendly - Auto-installing dependencies, clear error messages  

▶ Automatic file management - Both tools save output files automatically while displaying results  

▶ Smart file discovery - Sanitize script auto-finds latest analysis files  

It's a basic tool, but built with attention to quality: good test coverage, type hints, proper error handling, and a smooth workflow.

𝐔𝐬𝐚𝐠𝐞:  

```bash
# Capture network traffic (runs continuously until stopped)
./record-tcpdump​.sh
# Saves to log/record-tcpdump_YYYY-MM-DD_HHMMSS.txt

# Analyze the capture (auto-saves to log/record-tcpdump_YYYY-MM-DD_HHMMSS_analysis.txt)
./analyze-tcpdump​.py

# Filter TCP only, exclude local IPs
./analyze-tcpdump​.py -p tcp -l

# Sanitize for public sharing (auto-finds latest analysis file)
./sanitize-analysis-ipmask​.py
# Output saved to log/record-tcpdump_YYYY-MM-DD_HHMMSS_analysis.ipmasked.txt
```

The tools automatically save output files while still displaying results, making it easy to review output immediately and keep a record for later. The sanitize script can auto-discover the latest analysis file, so the workflow is: capture → analyze → sanitize, all with minimal typing.

Nothing revolutionary, just a useful tool for quickly understanding what's in a tcpdump capture file.

#NetworkAnalysis #NetworkSecurity #Python #OpenSource #DevTools #NetworkEngineering #Cybersecurity #Tcpdump #NetworkMonitoring
