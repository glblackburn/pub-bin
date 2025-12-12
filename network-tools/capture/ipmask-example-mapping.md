# IP Masking Example - Mapping Table

This document shows the IP masking approach used by `sanitize-analysis-ipmask.py`.

## Masking Strategy

Private IPs are masked by replacing the **2nd and 3rd octets** (middle two) with random two-letter combinations (G-Z, uppercase), while keeping the **1st and 4th octets unchanged**.

**Key Properties:**
- **Separate mappings**: 2nd and 3rd octets use independent random letter sets
  - Same value in 2nd position maps to different letters than the same value in 3rd position
  - Example: Value `0` in 2nd position → `HO`, but value `0` in 3rd position → `JV`
- **Consistent mapping**: Same octet value in the same position always maps to the same letters within a run
- **Unique IPs remain unique**: No collisions in masked output
- **IP format preserved**: Looks like a real IP address
- **Relationships maintained**: Same original IP = same masked IP in all contexts
- **Random per run**: Different runs produce different letter assignments
- **No hex values**: All letters are G-Z (excluding A-F to avoid hex confusion)

## Letter Mapping

- Values 0-255 map to random two-letter combinations (G-Z, uppercase)
- 20 available letters (G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z)
- 20 × 20 = 400 possible combinations (enough for 256 values)
- Each position (2nd vs 3rd) maintains its own independent mapping dictionary

## Example Mapping from Log File

Based on `log/record-tcpdump_2025-12-12_082910_analysis.txt`:

### Private IP Mappings (98 total)

#### 192.168.x.x Network (192.168.0.0/16)
```
192.168.0.128    -> 192.GS.JV.128     (2nd: 168 -> GS, 3rd: 0 -> JV)
192.168.0.137    -> 192.GS.JV.137
192.168.0.143    -> 192.GS.JV.143
192.168.0.239    -> 192.GS.JV.239
192.168.1.5      -> 192.GS.XX.5       (2nd: 168 -> GS, 3rd: 1 -> XX)
192.168.1.7      -> 192.GS.XX.7
192.168.1.61     -> 192.GS.XX.61
192.168.1.73     -> 192.GS.XX.73
192.168.1.74     -> 192.GS.XX.74
192.168.1.80     -> 192.GS.XX.80
192.168.1.101    -> 192.GS.XX.101
192.168.1.111    -> 192.GS.XX.111
192.168.1.138    -> 192.GS.XX.138
192.168.1.149    -> 192.GS.XX.149
192.168.1.211    -> 192.GS.XX.211
192.168.1.246    -> 192.GS.XX.246
192.168.1.254    -> 192.GS.XX.254
192.168.4.173    -> 192.GS.SL.173      (2nd: 168 -> GS, 3rd: 4 -> SL)
192.168.42.1     -> 192.GS.QS.1       (2nd: 168 -> GS, 3rd: 42 -> QS)
192.168.42.4     -> 192.GS.QS.4
192.168.42.5     -> 192.GS.QS.5
192.168.42.6     -> 192.GS.QS.6
192.168.42.7     -> 192.GS.QS.7       (most common IP in this log)
192.168.42.10    -> 192.GS.QS.10
192.168.42.11    -> 192.GS.QS.11
192.168.42.17    -> 192.GS.QS.17
192.168.42.18    -> 192.GS.QS.18
192.168.42.255   -> 192.GS.QS.255
192.168.50.235   -> 192.GS.TU.235     (2nd: 168 -> GS, 3rd: 50 -> TU)
192.168.68.60    -> 192.GS.KO.60      (2nd: 168 -> GS, 3rd: 68 -> KO)
192.168.87.254   -> 192.GS.OZ.254     (2nd: 168 -> GS, 3rd: 87 -> OZ)
```

**Note:** All IPs in the 192.168.x.x network share the same 2nd octet mapping (`168` → `GS`) because they all have `168` in the 2nd position.

#### 172.16-31.x.x Network (172.16.0.0/12)
```
172.16.10.1      -> 172.QH.WW.1        (2nd: 16 -> QH, 3rd: 10 -> WW)
172.17.0.1       -> 172.ZP.JV.1       (2nd: 17 -> ZP, 3rd: 0 -> JV)
172.17.70.232    -> 172.ZP.NH.232     (2nd: 17 -> ZP, 3rd: 70 -> NH)
172.18.0.1       -> 172.OP.JV.1       (2nd: 18 -> OP, 3rd: 0 -> JV)
172.18.96.1      -> 172.OP.NG.1       (2nd: 18 -> OP, 3rd: 96 -> NG)
172.24.65.0      -> 172.XW.WY.0       (2nd: 24 -> XW, 3rd: 65 -> WY)
172.24.84.234    -> 172.XW.VN.234     (2nd: 24 -> XW, 3rd: 84 -> VN)
172.24.91.246    -> 172.XW.MM.246     (2nd: 24 -> XW, 3rd: 91 -> MM)
172.24.123.78    -> 172.XW.JH.78      (2nd: 24 -> XW, 3rd: 123 -> JH)
172.24.127.75    -> 172.XW.KH.75      (2nd: 24 -> XW, 3rd: 127 -> KH)
172.24.132.183   -> 172.XW.HJ.183     (2nd: 24 -> XW, 3rd: 132 -> HJ)
172.24.147.10    -> 172.XW.JN.10      (2nd: 24 -> XW, 3rd: 147 -> JN)
172.24.147.124   -> 172.XW.JN.124
172.24.155.5     -> 172.XW.ZR.5       (2nd: 24 -> XW, 3rd: 155 -> ZR)
172.24.162.159   -> 172.XW.YI.159     (2nd: 24 -> XW, 3rd: 162 -> YI)
172.24.165.44    -> 172.XW.VM.44      (2nd: 24 -> XW, 3rd: 165 -> VM)
172.24.187.254   -> 172.XW.IY.254     (2nd: 24 -> XW, 3rd: 187 -> IY)
172.24.195.47    -> 172.XW.ZI.47      (2nd: 24 -> XW, 3rd: 195 -> ZI)
172.24.211.34    -> 172.XW.LK.34      (2nd: 24 -> XW, 3rd: 211 -> LK)
172.24.214.13    -> 172.XW.VU.13      (2nd: 24 -> XW, 3rd: 214 -> VU)
172.24.214.87    -> 172.XW.VU.87
172.24.219.106   -> 172.XW.PJ.106     (2nd: 24 -> XW, 3rd: 219 -> PJ)
172.24.219.24    -> 172.XW.PJ.24
172.24.255.255   -> 172.XW.NZ.255     (2nd: 24 -> XW, 3rd: 255 -> NZ)
172.25.127.75    -> 172.YP.KH.75      (2nd: 25 -> YP, 3rd: 127 -> KH)
172.25.132.183   -> 172.YP.HJ.183     (2nd: 25 -> YP, 3rd: 132 -> HJ)
172.25.147.124   -> 172.YP.JN.124     (2nd: 25 -> YP, 3rd: 147 -> JN)
172.25.155.5     -> 172.YP.ZR.5       (2nd: 25 -> YP, 3rd: 155 -> ZR)
172.25.195.47    -> 172.YP.ZI.47      (2nd: 25 -> YP, 3rd: 195 -> ZI)
172.25.219.106   -> 172.YP.PJ.106     (2nd: 25 -> YP, 3rd: 219 -> PJ)
172.25.255.255   -> 172.YP.NZ.255     (2nd: 25 -> YP, 3rd: 255 -> NZ)
172.30.127.75    -> 172.PY.KH.75      (2nd: 30 -> PY, 3rd: 127 -> KH)
172.30.132.183   -> 172.PY.HJ.183     (2nd: 30 -> PY, 3rd: 132 -> HJ)
172.30.147.124   -> 172.PY.JN.124     (2nd: 30 -> PY, 3rd: 147 -> JN)
172.30.155.5     -> 172.PY.ZR.5       (2nd: 30 -> PY, 3rd: 155 -> ZR)
172.30.158.99    -> 172.PY.ON.99      (2nd: 30 -> PY, 3rd: 158 -> ON)
172.30.162.159   -> 172.PY.YI.159     (2nd: 30 -> PY, 3rd: 162 -> YI)
172.30.165.44    -> 172.PY.VM.44      (2nd: 30 -> PY, 3rd: 165 -> VM)
172.30.171.233   -> 172.PY.RH.233     (2nd: 30 -> PY, 3rd: 171 -> RH)
172.30.187.254   -> 172.PY.IY.254     (2nd: 30 -> PY, 3rd: 187 -> IY)
172.30.195.47    -> 172.PY.ZI.47      (2nd: 30 -> PY, 3rd: 195 -> ZI)
172.30.211.34    -> 172.PY.LK.34      (2nd: 30 -> PY, 3rd: 211 -> LK)
172.30.214.13    -> 172.PY.VU.13      (2nd: 30 -> PY, 3rd: 214 -> VU)
172.30.214.87    -> 172.PY.VU.87
172.30.219.106   -> 172.PY.PJ.106     (2nd: 30 -> PY, 3rd: 219 -> PJ)
172.30.219.24    -> 172.PY.PJ.24
172.30.255.255   -> 172.PY.NZ.255     (2nd: 30 -> PY, 3rd: 255 -> NZ)
172.30.65.0      -> 172.PY.WY.0       (2nd: 30 -> PY, 3rd: 65 -> WY)
172.30.84.234    -> 172.PY.VN.234     (2nd: 30 -> PY, 3rd: 84 -> VN)
172.30.91.246    -> 172.PY.MM.246     (2nd: 30 -> PY, 3rd: 91 -> MM)
```

**Note:** All IPs in the 172.24.x.x network share the same 2nd octet mapping (`24` → `XW`), but different 3rd octet values map to different letters.

#### 10.x.x.x Network (10.0.0.0/8)
```
10.0.0.40        -> 10.HO.JV.40       (2nd: 0 -> HO, 3rd: 0 -> JV)
10.0.0.126       -> 10.HO.JV.126
10.1.76.59       -> 10.JV.SX.59       (2nd: 1 -> JV, 3rd: 76 -> SX)
10.2.0.2         -> 10.YN.JV.2        (2nd: 2 -> YN, 3rd: 0 -> JV)
10.20.38.254     -> 10.TY.PY.254      (2nd: 20 -> TY, 3rd: 38 -> PY)
10.20.63.250     -> 10.TY.MR.250      (2nd: 20 -> TY, 3rd: 63 -> MR)
10.30.0.169      -> 10.PY.JV.169      (2nd: 30 -> PY, 3rd: 0 -> JV)
10.30.48.167     -> 10.PY.KV.167      (2nd: 30 -> PY, 3rd: 48 -> KV)
10.80.14.189     -> 10.PW.ZX.189      (2nd: 80 -> PW, 3rd: 14 -> ZX)
10.82.141.140    -> 10.YS.OM.140      (2nd: 82 -> YS, 3rd: 141 -> OM)
10.82.141.146    -> 10.YS.OM.146
10.82.141.194    -> 10.YS.OM.194
```

**Key Observation:** Notice that value `0` appears in both 2nd and 3rd positions, but maps to different letters:
- Value `0` in 2nd position → `HO` (from `10.0.0.126`)
- Value `0` in 3rd position → `JV` (from `10.0.0.126`)

This demonstrates the independent mapping system.

#### Special Addresses
```
0.0.0.0          -> 0.HO.JV.0         (2nd: 0 -> HO, 3rd: 0 -> JV)
224.0.0.1        -> 224.RO.UZ.1      (multicast, 2nd: 0 -> RO, 3rd: 0 -> UZ)
224.0.0.22       -> 224.RO.UZ.22
224.0.0.251      -> 224.RO.UZ.251
255.255.255.255  -> 255.JJ.JJ.255    (broadcast, 2nd: 255 -> JJ, 3rd: 255 -> JJ)
```

**Note:** Even though `0.0.0.0` and `224.0.0.x` both have `0` in the 2nd and 3rd positions, they may map to different letters because the mappings are independent and random per run.

## Usage Example

```bash
# Basic masking (private IPs only)
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_082910_analysis.txt

# Show mapping table
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_082910_analysis.txt --show-mapping

# Also mask public IPs
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_082910_analysis.txt --mask-public

# Use specific seed for reproducible mappings
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_082910_analysis.txt --seed 12345
```

## Output Example

**Before:**
```
Top 10 Source IPs:
  192.168.42.7         31,520 packets
  172.24.147.10        992 packets
```

**After:**
```
Top 10 Source IPs:
  192.GS.QS.7         31,520 packets
  172.XW.JN.10        992 packets
```

Notice:
- IP format preserved (looks like IP address)
- First and last octets unchanged (`192` and `7` remain)
- Middle two octets masked with random letters
- Same IP appears consistently throughout (`192.168.42.7` always → `192.GS.QS.7`)
- Statistics unchanged (31,520 packets)
- Relationships maintained in connection pairs

## Mapping Statistics

From the example run:
- **Total IPs mapped:** 98
- **2nd octet mappings:** 14 unique values mapped
- **3rd octet mappings:** 34 unique values mapped
- **Letter combinations used:** G-Z only (no A-F hex values)

## Security Properties

1. **Non-reversible**: Random mapping means you cannot determine the original octet value from the letters
2. **Position-dependent**: Same value in different positions maps to different letters
3. **Run-dependent**: Different runs produce different mappings (unless `--seed` is used)
4. **Consistent within run**: Same value in same position always maps to same letters
5. **No collisions**: Unique IPs remain unique after masking
