# Shim-gui-Teensy4.1-control

Teensy 4.1 firmware and a 64-channel PyQt5 GUI for the open-source MIT-MGH **Rev C** multi-coil B0 shim drivers, with optional 16-bit full-range current readback (LTC1867).

The original Rev C system was controlled by a Teensy 3.5, which is now discontinued, and operated by typing commands into the Arduino serial console. This repository provides:

- **Firmware** ported to the Teensy 4.1 (SPI routines rewritten on the standard Teensyduino `SPI` transaction interface), for up to 8 amplifier boards × 8 channels = 64 channels.
- **Two firmware builds**, one for each current-monitor ADC:
  - `LTC1863` (12-bit, original boards, partial readback range −0.63 … +1.42 A)
  - `LTC1867` (16-bit, modified boards, full readback range)
- **A desktop GUI** to initialise, calibrate, set and monitor all 64 channels, and to step through shim current plans.

The amplifier boards themselves are the unchanged Rev C design.

## Repository layout

```
Shim-gui-Teensy4.1-control/
├── Teensy41_firmware/
│   ├── README.md                                 Differences between the two builds
│   ├── LTC1863_PartialRange/Teensy41_64CH_1863/  Build for boards with the LTC1863 ADC
│   └── LTC1867_FullRange/Teensy41_64CH_1867/     Build for boards with the LTC1867 ADC
├── gui/                                          PyQt5 control program
├── examples/                                     Example current-plan text files
└── requirements.txt
```

## Firmware

1. Install the [Arduino IDE](https://www.arduino.cc/en/software) and [Teensyduino](https://www.pjrc.com/teensy/td_download.html).
2. Check the ADC part number on your amplifier boards and open the matching sketch:
   - LTC1863 → `Teensy41_firmware/LTC1863_PartialRange/Teensy41_64CH_1863/Teensy41_64CH_1863.ino`
   - LTC1867 → `Teensy41_firmware/LTC1867_FullRange/Teensy41_64CH_1867/Teensy41_64CH_1867.ino`
3. Select **Tools → Board → Teensy 4.1** and upload.

The two builds are **not interchangeable**: flashing the wrong one gives incorrectly scaled current readings. See [`Teensy41_firmware/README.md`](Teensy41_firmware/README.md) for details.

**Configuration** (in `hardware.h` / `util.h`):

| Setting | Default | Meaning |
|---|---|---|
| `NUM_B` | 8 | Number of amplifier boards |
| `NUM_C` | 8 | Channels per board |
| `boardMap` | `{6, 5, 4, 3, 2, 1, 0, 7}` | Logical board → fibre-optic board-select output |
| `channels` | 64 | Total channels (`NUM_B × NUM_C`) |
| `interruptPin` | 6 | Scanner TTL trigger input (falling edge) |

If you use fewer boards, change `NUM_B`, `boardMap`, `channels`, the `channels_used` table and the calibration loop in the `.ino` file together.

Serial: USB, 115200 baud.

## GUI

### Run from source

```bash
cd gui
pip install -r ../requirements.txt
python main.py
```

The GUI finds the Teensy automatically by its USB identifiers; you can also type the COM port.

`demo.py` starts the GUI with simulated data (no hardware needed).

### Windows executable

A stand-alone `.exe` is available under [Releases](../../releases). To build it yourself:

```bash
pip install pyinstaller
cd gui
pyinstaller ShimmingGUI.spec
```

### Current-plan files

Plain text, values in amperes separated by commas, spaces or line breaks. The GUI uses them in two ways:

- **Load Extra Plan** → **Next Group / Previous Group**: values are read in groups of 64 (board 0 channel 0 … board 7 channel 7). Each step writes all 64 channels from the PC and reads back the result. Suitable for static shimming.
- **Upload Current Plan**: the values are sent to the Teensy as its stored current table (up to 50,000 values), which the firmware steps through on each scanner trigger. Use this for slice-wise dynamic shimming.

See `examples/`.

## Serial commands

The firmware still accepts plain-text commands from the Arduino serial monitor, so it can also be scripted from MATLAB or Python. Each command ends with a newline.

| Command | Action |
|---|---|
| `E` | Re-initialise |
| `D` | Calibrate all channels |
| `Z` | Zero all channels |
| `I` / `Icurrentall` | Read back all channel currents |
| `Ichannel,<board>,<channel>` | Read back one channel |
| `Track,<board>,<channel>,<current_A>` | Set one channel (−4 … +4 A) and read it back |
| `M` | Go to the first entry of the stored current table |
| `T` | Step to the next entry of the stored current table |
| `uploadcoef` | Followed by a binary little-endian float32 array: replace the stored current table |

## Acknowledgements

This work builds on the open-source Rev C shim driver and controller firmware by N. Arango, J. P. Stockmann, T. Witzel, L. L. Wald and J. White (MIT / MGH Martinos Center):

- Arango N, et al. *Open-source, low-cost, flexible, current feedback-controlled driver circuit for local B0 shim coils and other applications.* Proc. ISMRM 2016; 1157.
- Arango N, et al. *Open-source acquisition-speed slice-by-slice controller for 32 coil B0 shimming.* Proc. ISMRM 2017; 2682.

## Citation

If you use this code, please cite:

> Yang Y, Liu Z, Hu P, Ren Z. Same boards, better control: open-source Teensy 4.1 controller and GUI with 16-bit full-range readback for MIT-MGH shim drivers. Submitted to ISMRM 2027.

## License

TBD
