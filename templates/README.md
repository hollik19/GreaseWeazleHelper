# Template Files for Hollik's Greaseweazle Helper v1.0

This directory contains disk template files required for formatting operations. These templates provide properly formatted filesystem structures for each supported computer system.

## Currently Available Templates

### ✅ PC (IBM Compatible)
- `pc160.img` - 160KB (5.25" SS DD)
- `pc180.img` - 180KB (5.25" SS DD) 
- `pc320.img` - 320KB (5.25" DS DD)
- `pc360.img` - 360KB (5.25" DS DD)
- `pc720.img` - 720KB (3.5" DS DD)
- `pc1200.img` - 1.2MB (5.25" DS HD)
- `pc1440.img` - 1.44MB (3.5" DS HD)
- `pc2880.img` - 2.88MB (3.5" DS ED)

### ✅ Amiga
- `amiga880.adf` - 880KB (3.5" DD AmigaDOS)

### ✅ Apple Macintosh
- `apple800.dsk` - 800KB (3.5" DS Mac)
- `apple1440.dsk` - 1.44MB (3.5" HD Mac)

### ✅ Atari ST
- `atari360.st` - 360KB (3.5" SS)
- `atari400.st` - 400KB (3.5" SS)
- `atari720.st` - 720KB (3.5" DS)
- `atari800.st` - 800KB (3.5" DS)

### ✅ Commodore 64
- `c64170.d64` - 170KB (1541 Drive)

## Still Needed Templates

### ❌ Atari 8-bit
- `atari90.img` - 90KB (Atari 800 SS SD)

### ❌ ZX Spectrum
- `zx640.mgt` - 640KB (TR-DOS)
- `zx800.mgt` - 800KB (Quorum)

### ❌ Acorn BBC/Archimedes
- `acorn160.ads` - 160KB (ADFS SS)
- `acorn320.adm` - 320KB (ADFS DS) 
- `acorn640.adl` - 640KB (ADFS DS)
- `acorn800.adf` - 800KB (ADFS DS)
- `acorn1600.adf` - 1600KB (ADFS HD)

### ❌ MSX
- `msx180.dsk` - 180KB (1D)
- `msx360.dsk` - 360KB (2D)
- `msx360dd.dsk` - 360KB (1DD)
- `msx720.dsk` - 720KB (2DD)

### ❌ Additional C64 Formats
- `c64340.d71` - 340KB (1571 Drive)
- `c64800.d81` - 800KB (1581 Drive)

## File Size Verification

The application automatically verifies template files have the correct byte sizes:

| File | Expected Size (bytes) | Status |
|------|----------------------|---------|
| pc720.img | 737,280 | ✅ Present |
| pc1440.img | 1,474,560 | ✅ Present |
| amiga880.adf | 901,120 | ✅ Present |
| apple800.dsk | 819,200 | ✅ Present |
| apple1440.dsk | 1,474,560 | ✅ Present |
| atari720.st | 737,280 | ✅ Present |
| c64170.d64 | 174,848 | ✅ Present |

## How Template Files Work

1. **Format Selection**: When you choose "Format Disk" in the application, it uses these template files
2. **Verification**: The app checks file size matches exactly what's expected for each format
3. **Writing**: Template is written to floppy with `--no-verify` for maximum compatibility
4. **Result**: You get a properly formatted disk ready for use

## Creating Missing Templates

### Method 1: Original Hardware
1. Format blank disk on original computer
2. Create disk image using Greaseweazle
3. Save with exact filename from list above

### Method 2: Emulators
1. Use emulators (WinUAE, Hatari, VICE, etc.)
2. Format virtual disk with proper filesystem
3. Export disk image
4. Rename to match required filename

### Method 3: Disk Utilities
1. Use tools like HxC Floppy Emulator software
2. Create properly formatted disk images
3. Ensure correct size and filesystem structure

## Legal Notice

These template files contain only filesystem structures (boot sectors, FATs, directory tables) and no copyrighted content. They are equivalent to formatting a blank disk and are provided for convenience and compatibility testing.

## Contributing

If you have additional template files or can create missing ones:

1. Fork this repository
2. Add template files to this directory
3. Update this README with new entries
4. Submit pull request

Please ensure all contributed templates are legally created and properly sized.
