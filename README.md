![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# ECE 298A Tiny Tapeout Project: 8-bit Programmable Counter

An 8-bit programmable binary counter with an **asynchronous reset**, a **synchronous parallel
load**, a **count enable**, and **tri-state outputs**, built for the GF180MCU (gf180mcuD) PDK
on a single Tiny Tapeout tile. ECE 298A (University of Waterloo), project 1 — Ihsan Salari.

> *"Write Verilog code describing an 8-bit programmable binary counter with asynchronous reset,
> synchronous load and tri-state outputs. Show that the Verilog code works (test it!). Build
> using github actions in Tiny Tapeout for the GF-180nm technology."*

## Status

**All three Tiny Tapeout workflows pass:** `gds` (hardening, precheck, gate-level test),
`docs` and `test`. The layout is live in the 3D viewer at
<https://ihsan-sa.github.io/ece298a-counter/>.

## What was done

1. **The counter** (`src/project.v`) — a single 8-bit register with priority
   reset > load > count > hold. The reset is asynchronous (it is in the sensitivity list);
   load and count happen only on a rising clock edge.
2. **The pin mapping** — a tri-state output has to go on `uio`, the only Tiny Tapeout pins that
   can go high-impedance. That takes all eight, so the load data shares the same bus, as on a
   74-series bus counter, and an always-driven copy of the count goes on `uo`.
3. **The tests** (`test/`) — seven CocoTB tests, all passing in CI: asynchronous reset,
   synchronous load, counting, enable-hold, 255 → 0 wrap-around, the tri-state bus, and load
   winning over count. To check the tests can actually catch bugs, they were also run against
   four deliberately broken counters (synchronous reset, count beating load, `uio_oe` stuck at
   `0xFF`, enable ignored); every one failed.
4. **Lint** — `verilator --lint-only -Wall` is clean, apart from the file-name warning that
   Tiny Tapeout's naming forces.
5. **The build** — the first `gds` run built the chip but failed at the GitHub Pages step,
   because Pages was not yet enabled on the repo. With Pages set to "GitHub Actions", a fresh
   run went green. *Tip:* don't re-run a failed `gds` run — it uploads a second `github-pages`
   artifact and the deploy refuses. Start a new run from Actions → gds → Run workflow.

Full design notes and a by-hand test sequence: [docs/info.md](docs/info.md).

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

## About Tiny Tapeout

[Tiny Tapeout](https://tinytapeout.com) is an educational project for getting digital and
analog designs manufactured on a real chip. The GitHub actions build the ASIC files with
[LibreLane](https://www.zerotoasiccourse.com/terminology/librelane/).
[FAQ](https://tinytapeout.com/faq/) ·
[build your design locally](https://www.tinytapeout.com/guides/local-hardening/).
