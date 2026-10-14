# ece298a-counter goals

This repository is the first project of ECE 298A (Integrated Circuit Design and Tapeout) at the University of Waterloo: an 8-bit programmable binary counter with an asynchronous reset, a synchronous parallel load, a count enable and a tri-state bidirectional bus, built for Tiny Tapeout on one GF180 tile and tested with cocotb. The counter is finished and its Tiny Tapeout workflows pass. Runs for the course's two later designs start here too, though each design lives in its own repository: the term project, a charge-pump PLL, in [ece298a-pll](https://github.com/ihsan-sa/ece298a-pll), and an R-2R DAC on an analog tile in [ece298a-r2r-dac](https://github.com/ihsan-sa/ece298a-r2r-dac). This is coursework, so runs never submit anything to a course system.

## Proposed goals

Filed by runs. Each says what done looks like as something a run can check, and keeps its status (open, done, failed, dropped) with the pull requests that moved it. At most three are open at once.

### Sign off the PLL's analog half and close what it carries into layout

- **Status:** open, waiting on the owner's sign-off
- **What:** The PLL's analog half (the charge pump, the loop filter, the ring VCO and their bias) has passed every pre-layout check over 29 simulation corners, and it waits on the owner's sign-off before its layout starts. That sign-off decides whether the analog netlist, the spec it is checked against and those simulation results are frozen as the reference that layout has to match. It also accepts two changes made since the proposal: wider charge-pump current windows, and a phase-margin floor of 30 degrees scored at every corner. The [review](https://github.com/ihsan-sa/ece298a/blob/main/docs/pll-h1-review.md) sets out the results, the thin margins and the open items. A run asks the owner for his answer and waits for it; it never approves the sign-off itself, and it changes nothing in the analog design until the answer is recorded. If he approves, the run then closes the open items in [ece298a-pll](https://github.com/ihsan-sa/ece298a-pll): it puts the two resistor-skew corners back into the spec, scores the VCO's 333 MHz ceiling at every corner (the VCO reaches about 363 MHz at fast, cold, low supply with its control voltage at the rail), corrects the frequency that the spec's sign-off note mislabels, reruns the analog checks, and reruns the digital timing with the VCO clock at about 2.7 ns. If he rejects it, the run reworks the design against his reason and asks again.
- **Done when:** the owner's answer is recorded as the analog sign-off in ece298a-pll. If he approved, the spec there also scores both skew corners and the VCO ceiling at every corner, the analog spec lint, PVT simulation and bench-strength checks pass on that spec, and the digital timing check passes with the VCO clock at about 2.7 ns.

### Release the R-2R DAC and write its design document

- **Status:** open, waiting on the owner's sign-offs
- **What:** Every check on the R-2R DAC passes, including hardening, DRC, LVS and the Tiny Tapeout precheck. Its release waits on three sign-offs from the owner, one each for the whole tile, its analog half and its digital half, and the design document comes only after them. A run asks for the three and waits; it never records one he hasn't given. Once they are in, the run records them in [ece298a-r2r-dac](https://github.com/ihsan-sa/ece298a-r2r-dac) and writes the design document.
- **Done when:** the three sign-offs are recorded in ece298a-r2r-dac, its design document is on its main branch, and its Tiny Tapeout workflows pass there.

## Later

Goals waiting for an open slot. When a proposed goal closes, the run that closed it moves the top one here up into Proposed goals as open.

### Test the whole PLL loop in co-simulation

- **Status:** later
- **What:** The course grades a system verification of the term project. The proposal's plan tests the loop as a whole in three layers: a linear model of the loop, the real digital logic in cocotb with Python models of the pump, filter and VCO calibrated from the VCO bench, and a mixed-signal co-simulation. Build those benches in ece298a-pll and run them.
- **Done when:** the three layers run from one command in ece298a-pll, the co-simulation shows the loop locking at the 100 MHz nominal point, and the result is written up next to the benches.

### Publish the in-class adder exercise

- **Status:** later, paused by the owner
- **What:** The course's first in-class exercise, an 8-bit adder on the Tiny Tapeout template, was built but never pushed, so [ece298a-init-session](https://github.com/ihsan-sa/ece298a-init-session) is still empty. The owner paused it; it moves up only when he resumes it. Then push the exercise and check that its Tiny Tapeout workflows run.
- **Done when:** ece298a-init-session's main holds the adder project and its gds, docs and test workflows pass.

## Closed

What has landed, from the git history (a line per PR).

- [#1](https://github.com/ihsan-sa/ece298a-counter/pull/1) The 8-bit counter and its README
- [#2](https://github.com/ihsan-sa/ece298a-counter/pull/2) Add the project write-up PDF
- [#3](https://github.com/ihsan-sa/ece298a-counter/pull/3) Show the write-up PDF pages in the README
