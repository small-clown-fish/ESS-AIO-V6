# v4.15 SBMU Version Read

Added selectable SBMU version reading from the BMS Control page.

## Behavior

- `Read BMS Version` still reads MBMU/ETH version blocks.
- New `SBMU count` selector controls how many SBMU version blocks to read.
- SBMU01 version addresses are taken from the active BMS point table when available.
- SBMU02/SBMU03/... are derived by adding `0x400` per SBMU index:

```text
SBMU02 address = SBMU01 address + 0x400
SBMU03 address = SBMU01 address + 0x800
...
```

## Default CATL V22 fallback addresses

- SBMU Software: `0x07C0`
- SBMU Hardware: `0x07C8`
- CSC Software: `0x07D0`
- CSC Hardware: `0x07D8`
