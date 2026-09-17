# SPDX-FileCopyrightText: © 2026 Ihsan Salari
# SPDX-License-Identifier: Apache-2.0
#
# CocoTB testbench for tt_um_ece298a_counter, the ECE 298A 8-bit programmable
# binary counter.
#
# Pin map under test:
#   ui[0] = LOAD, ui[1] = ENABLE, ui[2] = OE, ui[7:3] unused
#   uio[7:0] = bidirectional bus: D[7:0] in when OE=0, Q[7:0] out when OE=1
#   uo[7:0]  = Q[7:0] mirror, always driven
#   rst_n    = asynchronous active-low reset

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer

CLK_PERIOD_NS = 100  # 10 MHz, keeps the arithmetic in the test easy to read

LOAD = 0b001
ENABLE = 0b010
OE = 0b100

# A short settle delay used after a clock edge so non-blocking assignments have
# been committed before the test samples an output.
SETTLE_NS = 1


def ctrl(load=False, enable=False, oe=False):
    """Pack the three control bits into the ui_in byte (ui[7:3] tied low)."""
    return (LOAD if load else 0) | (ENABLE if enable else 0) | (OE if oe else 0)


async def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, unit="ns").start())


async def reset(dut, ui=0, uio=0):
    """Bring the DUT up in a known state: count = 0, controls per arguments."""
    dut.ena.value = 1
    dut.ui_in.value = ui
    dut.uio_in.value = uio
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await Timer(SETTLE_NS, unit="ns")


async def step(dut):
    """Advance one rising clock edge and let the result settle."""
    await RisingEdge(dut.clk)
    await Timer(SETTLE_NS, unit="ns")


def q(dut):
    """The count as seen on the always-driven uo mirror."""
    return int(dut.uo_out.value)


# ---------------------------------------------------------------------------
# 1. Asynchronous reset
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_async_reset(dut):
    """rst_n clears the counter immediately, between clock edges."""
    await start_clock(dut)
    await reset(dut)

    # Count up to a non-zero value so the clear is visible.
    dut.ui_in.value = ctrl(enable=True)
    for _ in range(5):
        await step(dut)
    assert q(dut) == 5, f"expected 5 after 5 counts, got {q(dut)}"

    # Land squarely between two rising edges: wait for the falling edge, then
    # move a further quarter period so we are nowhere near a clock event.
    await FallingEdge(dut.clk)
    await Timer(CLK_PERIOD_NS // 4, unit="ns")
    assert q(dut) == 5, "count changed on its own between edges"

    # Drop rst_n here. No clock edge happens until the next rising edge, so if
    # the count clears it can only be because the reset is asynchronous.
    dut.rst_n.value = 0
    await Timer(SETTLE_NS, unit="ns")
    assert q(dut) == 0, (
        f"async reset failed: count is {q(dut)} after rst_n fell mid-cycle "
        "(a synchronous reset would still show 5 here)"
    )

    # It also stays cleared while held low, even with counting enabled.
    await ClockCycles(dut.clk, 3)
    await Timer(SETTLE_NS, unit="ns")
    assert q(dut) == 0, f"count moved while rst_n held low: {q(dut)}"

    # Release and confirm counting resumes from 0.
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await step(dut)
    assert q(dut) == 1, f"expected 1 on the first edge after reset, got {q(dut)}"


# ---------------------------------------------------------------------------
# 2. Synchronous load
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_sync_load(dut):
    """Load takes effect on the rising clock edge and not before it."""
    await start_clock(dut)
    await reset(dut)

    # Present the data on the bidirectional bus. OE must be low for this: the
    # pads can only be inputs while the design is not driving them.
    await FallingEdge(dut.clk)
    dut.uio_in.value = 0xA5
    dut.ui_in.value = ctrl(load=True, oe=False)
    assert int(dut.uio_oe.value) == 0x00, "bus must be released for a load"

    # Still mid-cycle: nothing should have happened yet.
    await Timer(CLK_PERIOD_NS // 4, unit="ns")
    assert q(dut) == 0, (
        f"load was not synchronous: count became {q(dut)} with no clock edge"
    )

    # Now the edge.
    await step(dut)
    assert q(dut) == 0xA5, f"load failed: expected 0xA5, got 0x{q(dut):02X}"

    # Deassert load; the value must be held (enable is low too).
    dut.ui_in.value = ctrl()
    await step(dut)
    assert q(dut) == 0xA5, f"value not held after load: 0x{q(dut):02X}"

    # A second load overwrites it.
    await FallingEdge(dut.clk)
    dut.uio_in.value = 0x3C
    dut.ui_in.value = ctrl(load=True)
    await step(dut)
    assert q(dut) == 0x3C, f"second load failed: 0x{q(dut):02X}"


# ---------------------------------------------------------------------------
# 3. Counting up from a loaded value
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_count_up_from_loaded_value(dut):
    """After a load the counter increments by one per rising edge."""
    await start_clock(dut)
    await reset(dut)

    start = 0x40
    await FallingEdge(dut.clk)
    dut.uio_in.value = start
    dut.ui_in.value = ctrl(load=True)
    await step(dut)
    assert q(dut) == start

    dut.ui_in.value = ctrl(enable=True)
    for i in range(1, 17):
        await step(dut)
        expected = (start + i) & 0xFF
        assert q(dut) == expected, (
            f"count step {i}: expected 0x{expected:02X}, got 0x{q(dut):02X}"
        )


# ---------------------------------------------------------------------------
# 4. Count enable deasserted -> hold
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_count_enable_holds(dut):
    """With ENABLE low the count is unchanged across many clock edges."""
    await start_clock(dut)
    await reset(dut)

    dut.ui_in.value = ctrl(enable=True)
    for _ in range(7):
        await step(dut)
    held = q(dut)
    assert held == 7, f"expected 7, got {held}"

    # Drop the enable and clock it hard.
    dut.ui_in.value = ctrl(enable=False)
    for cycle in range(10):
        await step(dut)
        assert q(dut) == held, (
            f"counter moved with ENABLE low on cycle {cycle}: "
            f"0x{q(dut):02X} != 0x{held:02X}"
        )

    # Re-enable and confirm it picks up from where it stopped.
    dut.ui_in.value = ctrl(enable=True)
    await step(dut)
    assert q(dut) == held + 1, f"expected {held + 1}, got {q(dut)}"


# ---------------------------------------------------------------------------
# 5. Wrap-around 255 -> 0
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_wraparound(dut):
    """255 + 1 rolls over to 0 without any carry out."""
    await start_clock(dut)
    await reset(dut)

    await FallingEdge(dut.clk)
    dut.uio_in.value = 0xFE
    dut.ui_in.value = ctrl(load=True)
    await step(dut)
    assert q(dut) == 0xFE

    dut.ui_in.value = ctrl(enable=True)
    await step(dut)
    assert q(dut) == 0xFF, f"expected 0xFF, got 0x{q(dut):02X}"

    await step(dut)
    assert q(dut) == 0x00, f"wrap failed: expected 0x00, got 0x{q(dut):02X}"

    await step(dut)
    assert q(dut) == 0x01, f"expected 0x01 after wrap, got 0x{q(dut):02X}"


# ---------------------------------------------------------------------------
# 6. Tri-state output bus
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_tristate_bus(dut):
    """OE controls uio_oe; the uo mirror tracks the count regardless."""
    await start_clock(dut)
    await reset(dut)

    # Load a recognisable pattern with the bus released.
    await FallingEdge(dut.clk)
    dut.uio_in.value = 0x5A
    dut.ui_in.value = ctrl(load=True, oe=False)
    await step(dut)
    assert q(dut) == 0x5A

    # OE low: the pads are inputs, so the whole enable bus is 0x00.
    dut.ui_in.value = ctrl(oe=False)
    await Timer(SETTLE_NS, unit="ns")
    assert int(dut.uio_oe.value) == 0x00, (
        f"OE low should release the bus, uio_oe = 0x{int(dut.uio_oe.value):02X}"
    )
    # The mirror still shows the count while the bus is in Hi-Z.
    assert q(dut) == 0x5A, "uo mirror lost the count while the bus was released"

    # OE high: all eight pads drive, and they carry Q.
    dut.ui_in.value = ctrl(oe=True)
    await Timer(SETTLE_NS, unit="ns")
    assert int(dut.uio_oe.value) == 0xFF, (
        f"OE high should drive the whole bus, uio_oe = 0x{int(dut.uio_oe.value):02X}"
    )
    assert int(dut.uio_out.value) == 0x5A, (
        f"bus should carry Q: expected 0x5A, got 0x{int(dut.uio_out.value):02X}"
    )
    assert int(dut.uio_out.value) == q(dut), "bus and uo mirror disagree"

    # While counting with the bus driven, both views must track together and
    # the enable must stay at 0xFF the whole time.
    dut.ui_in.value = ctrl(enable=True, oe=True)
    for _ in range(6):
        await step(dut)
        assert int(dut.uio_oe.value) == 0xFF, "bus dropped out of drive while counting"
        assert int(dut.uio_out.value) == q(dut), (
            f"bus 0x{int(dut.uio_out.value):02X} != mirror 0x{q(dut):02X}"
        )

    # Release it again mid-count: the count carries on, visible only on uo.
    dut.ui_in.value = ctrl(enable=True, oe=False)
    await Timer(SETTLE_NS, unit="ns")
    assert int(dut.uio_oe.value) == 0x00
    before = q(dut)
    # uio_in is whatever the outside world drives while we are in Hi-Z; it must
    # not disturb the count as long as LOAD is low.
    dut.uio_in.value = 0xFF
    for i in range(1, 4):
        await step(dut)
        assert q(dut) == (before + i) & 0xFF, (
            "count disturbed by bus traffic while released"
        )
        assert int(dut.uio_oe.value) == 0x00, "bus re-enabled itself"


# ---------------------------------------------------------------------------
# 7. Load priority over count
# ---------------------------------------------------------------------------
@cocotb.test()
async def test_load_beats_count(dut):
    """With LOAD and ENABLE both high the loaded value wins, with no +1."""
    await start_clock(dut)
    await reset(dut)

    dut.ui_in.value = ctrl(enable=True)
    for _ in range(3):
        await step(dut)
    assert q(dut) == 3

    await FallingEdge(dut.clk)
    dut.uio_in.value = 0x77
    dut.ui_in.value = ctrl(load=True, enable=True)
    await step(dut)
    assert q(dut) == 0x77, (
        f"load must beat count: expected 0x77, got 0x{q(dut):02X} "
        "(0x78 would mean the increment was applied on top of the load)"
    )

    # Holding both asserted keeps reloading the same value: no counting.
    for _ in range(3):
        await step(dut)
        assert q(dut) == 0x77, f"count leaked past a held load: 0x{q(dut):02X}"

    # Reset also beats load: assert rst_n while LOAD and ENABLE are both high.
    await FallingEdge(dut.clk)
    dut.rst_n.value = 0
    await Timer(SETTLE_NS, unit="ns")
    assert q(dut) == 0, f"reset must beat load, got 0x{q(dut):02X}"
    await step(dut)
    assert q(dut) == 0, f"reset must hold the count at 0, got 0x{q(dut):02X}"
    dut.rst_n.value = 1
