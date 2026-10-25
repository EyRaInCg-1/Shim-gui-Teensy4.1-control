# Shim Amplifier – Teensy 4.1 Firmware

This folder contains two versions of the Teensy 4.1 firmware, one for each hardware revision of the shim amplifier board. The two boards use different ADC chips from the same family, and the firmware must match the board.

**The two versions are not interchangeable. Before each experiment, flash the version that matches the board you are using.**

## Folder structure

```
Teensy41_firmware/
├── LTC1863_PartialRange/Teensy41_64CH_1863/   Firmware for boards with the LTC1863 ADC (12-bit)
└── LTC1867_FullRange/Teensy41_64CH_1867/      Firmware for boards with the LTC1867 ADC (16-bit)
```

| | LTC1863 board | LTC1867 board |
|---|---|---|
| ADC | LTC1863 | LTC1867 |
| ADC resolution | 12-bit | 16-bit |
| Measurement range | Partial range | Full range |

## Which version to flash

Check the part marking on the ADC chip on the amplifier board:

- **LTC1863** → flash the firmware in `LTC1863_PartialRange/`
- **LTC1867** → flash the firmware in `LTC1867_FullRange/`

If the wrong version is flashed, the voltage and current readings will be incorrectly scaled.

## Code differences

The differences between the two versions are in three functions: `LTC1863ReadSlow()` in `hardware.h`, and `computeOutV()` and `computeOutI()` in `util.h`.

### 1. `LTC1863ReadSlow()` — in `hardware.h`

The SPI transfer is the same in both versions. Only the return value differs: the LTC1863 returns a 12-bit result in the upper bits of the 16-bit word, so it is shifted right by 4 bits.

**LTC1863 version (12-bit):**

```cpp
return (data_rx[1]&0xFFFF)>>4;
```

**LTC1867 version (16-bit):**

```cpp
return (data_rx[1]&0xFFFF);
```

Note: the function keeps the name `LTC1863ReadSlow()` in both versions, including the LTC1867 version.

### 2. `computeOutV()` — in `util.h`

The ADC full-scale value differs (4096 for 12-bit, 65535 for 16-bit). Reference voltage is 4.096 V in both.

**LTC1863 version (12-bit):**

```cpp
float computeOutV(uint16_t dacVal) {
  return ((float(dacVal) * 4.096 / 4096.0));
}
```

**LTC1867 version (16-bit):**

```cpp
float computeOutV(uint16_t dacVal) {
  return ((float(dacVal) * 4.096 / 65535.0));
}
```

### 3. `computeOutI()` — in `util.h`

Two things differ: the ADC full-scale value (as above), and the current conversion gain factor (10 for the LTC1863 board, 1.8 for the LTC1867 board). The 1.25 V offset and the 0.2 factor are the same in both.

**LTC1863 version (12-bit):**

```cpp
float computeOutI(uint16_t dacVal) {
  return ((float(dacVal) * 4.096 / 4096.0) - 1.25) / 10 / 0.2;
}
```

**LTC1867 version (16-bit):**

```cpp
float computeOutI(uint16_t dacVal) {
  return ((float(dacVal) * 4.096 / 65535.0) - 1.25) / 1.8 / 0.2;
}
```

## Summary of differences

| Location | Item | LTC1863 version | LTC1867 version |
|---|---|---|---|
| `hardware.h` → `LTC1863ReadSlow()` | Return value | `>> 4` (12-bit) | no shift (16-bit) |
| `util.h` → `computeOutV()` | ADC full scale | 4096.0 | 65535.0 |
| `util.h` → `computeOutI()` | ADC full scale | 4096.0 | 65535.0 |
| `util.h` → `computeOutI()` | Gain factor | 10 | 1.8 |
