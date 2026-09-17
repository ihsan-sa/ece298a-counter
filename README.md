![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# ECE 298A Tiny Tapeout Project: 8-bit Programmable Counter

An 8-bit programmable binary counter with an **asynchronous reset**, a **synchronous parallel
load**, a **count enable**, and **tri-state outputs**, built for the GF180MCU (gf180mcuD) PDK
on a single Tiny Tapeout tile.

- [Read the documentation for this project](docs/info.md)

## The design at a glance

Top module: `tt_um_ece298a_counter` (`src/project.v`).

| pin | direction | meaning |
| --- | --- | --- |
| `uio[7:0]` | bidirectional | `OE = 1`: `uio_oe = 0xFF`, the bus drives the count Q[7:0]. `OE = 0`: `uio_oe = 0x00`, the bus is Hi-Z and is sampled as the parallel load data D[7:0]. |
| `ui[0]` | input | `LOAD` — synchronous parallel load, active high |
| `ui[1]` | input | `ENABLE` — count enable, active high |
| `ui[2]` | input | `OE` — tri-state output enable, active high |
| `ui[7:3]` | input | unused; tie low |
| `uo[7:0]` | output | Q[7:0] mirror, always driven |
| `clk` | input | clock |
| `rst_n` | input | asynchronous reset, active low |

Behaviour priority: **reset > load > count > hold.** The reset is asynchronous (`always
@(posedge clk or negedge rst_n)`), so it clears the count the instant `rst_n` falls; everything
else happens only on a rising clock edge. The count wraps 255 → 0.

Only the `uio` pins on a Tiny Tapeout tile can go high-impedance, so the tri-state output must
live there — which uses all eight of them and leaves no pins for a separate data-input port.
The bus is therefore bidirectional, exactly like a 74-series bus counter. **A load consequently
requires `OE` to be low**, because the pads can only be inputs while the design is not driving
them. `uo[7:0]` carries an always-driven copy of the count so it stays observable while the bus
is released. See [docs/info.md](docs/info.md) for the full reasoning and a test sequence.

## Testing

The testbench is CocoTB, in `test/`. Seven separate tests cover asynchronous reset,
synchronous load, counting from a loaded value, holding with the enable deasserted, 255 → 0
wrap-around, the tri-state bus, and load priority over count.

```sh
cd test
make -B            # RTL simulation with Icarus Verilog
make -B GATES=yes  # gate-level, after the GDS action has produced a netlist
```

See [test/README.md](test/README.md) for the prerequisites.

## What is Tiny Tapeout?

Tiny Tapeout is an educational project that aims to make it easier and cheaper than ever to get
your digital and analog designs manufactured on a real chip.

To learn more and get started, visit https://tinytapeout.com.

The GitHub action builds the ASIC files using [LibreLane](https://www.zerotoasiccourse.com/terminology/librelane/).

## Enable GitHub actions to build the results page

- [Enabling GitHub Pages](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)

## Resources

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Learn how semiconductors work](https://tinytapeout.com/siliwiz/)
- [Join the community](https://tinytapeout.com/discord)
- [Build your design locally](https://www.tinytapeout.com/guides/local-hardening/)
