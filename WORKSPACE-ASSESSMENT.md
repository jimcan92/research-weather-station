# Workspace Assessment — research-weather-station

**Date:** 2026-09-29
**Scope:** Full repository — firmware, gateway, server, database, dashboard, hardware, docs, infra
**Method:** Static read-only analysis + git/toolchain inspection. Nothing was modified.
**Verdict:** A well-organized **research prototype**, not an operating station and not fabrication-ready.
The architecture is sound and honestly documented, but the end-to-end chain has **never been run**,
and three defects break it outright.

---

## 1. Snapshot

| Metric | Value |
|---|---|
| Tracked files | 129 |
| Tracked size | 3.39 MB |
| On-disk size | 415 MB (`.pio` 333 MB, `webui/node_modules` 78 MB — both correctly gitignored) |
| Commits / branch | 3 on `main`, last 0.8 days ago |
| Remote | `github.com/jimcan92/research-weather-station` |
| Uncommitted | 752 insertions across 7 firmware files; untracked `webui/`, `data/`, `partitions_16mb.csv`, `.gitignore`, `.vscode/` |
| CI / tests / lint | **None** anywhere |
| Toolchain present | node, npm, pnpm, docker, git |
| Toolchain missing | `pio` (PlatformIO) — **firmware cannot be built here** |
| Deps installed | `webui/node_modules` only. `server/` and `dashboard/` have **no** `node_modules` → never installed |

**Hygiene — genuinely clean.** No secrets committed (`.env` absent and ignored per `.gitignore:13-15`),
zero BOMs, zero mixed line endings, dependency and build output correctly excluded, 20 of 21 doc path
references resolve. This is better hygiene than most projects at this stage.

**Two frontends exist**, which the README does not make obvious:
`dashboard/` (SvelteKit + Drizzle ops dashboard) and `firmware/weather-node/webui/`
(ESP32 config portal, built into `data/` as a LittleFS image).

---

## 2. Critical findings

### C1. The battery divider has FOUR mutually incompatible values — and the firmware disagrees with all its docs

| Value | Where |
|---|---|
| **5.70** (47k/10k) | `firmware/weather-node/src/config.h:79-84`, printed at `sensors.cpp:249` — **what the code actually does** |
| **4.90** (390k/100k) | `docs/session-progress.md:26-28`, `docs/power-bom-solar-lifepo4.md:85-96`, `hardware/node-pcb/weather-node-complete.kicad_sch:5350` |
| **4.30** (330k/100k) | `docs/pin-configuration-guide.md:218-227`, `docs/power-configuration.md:360`, `docs/sensor-wiring.md:161`, `hardware/power-pcb/README.md:56` |
| **1.45** (100k/220k) | `docs/pin-configuration-guide.md:309` — stale value inside the same file that says 4.30 at line 227 |

`docs/session-progress.md:28` asserts `Firmware: #define BAT_DIVIDER 4.90`. **That is false** —
`config.h` computes 5.70.

**Impact.** A 390k board under a 5.70 constant over-reports pack voltage by ~16%; a 330k board by ~33%.
A healthy 12.8 V LiFePO4 pack reads as ~14.9 V ⇒ the node always believes it is at full charge and
**can over-discharge the pack**, which permanently damages LiFePO4 cells. Separately, the 4.30 design
puts 14.6 V × 100/430 = **3.40 V on GPIO14, above the 3.3 V ADC maximum** — and the doc's own safety
check at `power-configuration.md:360` only computes it at 12.6 V, hiding the overvoltage.

**This is the single highest-priority item.** It cannot be resolved from the repo — the physical board
must be measured, then one value propagated to code, docs, and schematic.

### C2. `battery_v NUMERIC(3,2)` cannot store a pack voltage — silently discards every real reading

`NUMERIC(3,2)` has a maximum of **9.99**. The system reports 4S LiFePO4 pack voltage (12.8 V nominal,
14.6 V full — `docs/power-bom-solar-lifepo4.md:5`), computed in whole volts at `packet.cpp:18`.

The overflow raises an error that `server/src/ingest.ts:94-96` catches and reduces to a log line,
returning `null`. **Every packet from real hardware is dropped.**

Present identically in **both** schema definitions:
- `database/migrations/001_initial_schema.sql:30`
- `server/src/db.ts:46`

It has never been caught because the only test packet in the repo uses `"b":3.8` (`README.md:79`) —
which fits. The bug appears only with real hardware.

Same class of over-precision bug: `humidity` and `soil_moisture` are `NUMERIC(4,1)`, so a legitimate
reading of exactly `100.0` is 5 digits and also overflows.

### C3. Grafana datasource reference mismatch — all ~24 panels are dead

`grafana/datasources/postgres.yml:7-8` provisions `name: WeatherStation` with `type: postgres` and
**no `uid`**. Grafana generates a random UID when `uid` is omitted.

Every panel target references `"uid": "WeatherStation"` with
`"type": "grafana-postgresql-datasource"` (e.g. `weather-station.json:48-49,101-102,159-160` — 88 matches).

Combined with the unpinned `grafana/grafana:latest` image (`docker-compose.yml:44`) against a
`schemaVersion: 39` dashboard, the datasource reference and plugin type must be verified against
whatever version actually pulls. Fix: add `uid: WeatherStation` to `postgres.yml` and align `type`.

---

## 2b. CONFIRMED ON HARDWARE (2026-09-29): GPIO14 over-voltage from a wrong resistor

This section supersedes the theory in C1 and is the highest-priority item in the report. It is a
confirmed physical defect, not a code review finding.

### What was measured

Bench test with the tester board connected to a 12 V battery, divider intended as 47k/10k:

| Measurement | Value |
|---|---|
| GPIO14 → GND | **4.26 V** |
| ESP32-S3 ADC maximum | 3.3 V |
| Absolute maximum (GPIO) | ~3.6 V |
| Battery-side report on `weather.local` | **28.48 V** |

### Root cause

The **top resistor is 4.7 kΩ, not 47 kΩ** — a 10× error. Colour bands differ by one stripe:
`4.7k = yellow·violet·RED` vs `47k = yellow·violet·ORANGE`.

```
Intended ratio:  (47 + 10) / 10 = 5.70
Actual ratio:    (4.7 + 10) / 10 = 1.47
```

| Input | Pin voltage at 1.47 ratio | Correct at 5.70 |
|---|---|---|
| 12.0 V | **8.16 V** | 2.11 V |
| 14.6 V (4S full) | **9.93 V** | 2.56 V |

### Why 4.26 V was measured instead of 8.16 V

The ESP32's input protection diode **clamped** the pin — 4.26 V is the clamp voltage, not the divider
output. This proves current has been **injected into the GPIO**:

```
I_R1 = (12.0 − 4.26) / 4.7k  = 1.65 mA
I_R2 = 4.26 / 10k            = 0.43 mA
I_diode into the 3.3 V rail  = 1.22 mA     (≈1.8 mA at 14.6 V)
```

That is outside the datasheet specification. The clamp is the only reason the pin did not see 8–10 V —
the ESD diode absorbed the fault. The clamped, over-range pin also explains the impossible 28.48 V
report: the ADC saturated above its ~3.1 V range and the calibration curve extrapolated.

### Impact on finding C1

**The firmware is correct and the docs are wrong.** `config.h:84` computes
`(BAT_R1 + BAT_R2) / BAT_R2 = (47 + 10) / 10 = 5.70`, which is the right and safe ratio for a 4S
LiFePO4 pack. The 4.30 (330k/100k) value still present in `pin-configuration-guide.md:227`,
`power-configuration.md:360` and `sensor-wiring.md:161` would put **3.40 V** on GPIO14 at 14.6 V —
also an over-voltage. The 4.90 (390k/100k) in `session-progress.md:26-28` and the canonical schematic
is safe but does not match the code. **Only 5.70 (47k/10k) is both safe and consistent with the
firmware.**

### Fix

1. **Replace the top resistor 4.7 kΩ → 47 kΩ.** No code change required — `BAT_DIVIDER` already
   evaluates to 5.70.
2. Verify the bottom resistor is genuinely 10 kΩ (if the top was misread, the bottom may be too).
3. Confirm GPIO14 ≈ **2.11 V** at 12 V in, and ≈ 2.56 V at 14.6 V.
4. **Verify the pin survived.** Sweep a known input (6/9/12/14 V) and confirm the serial readings are
   linear. Non-linear, offset, or stuck readings mean the pin is damaged and battery sensing must move
   to an **ADC1** pin (GPIO1–GPIO10; GPIO9 appears free). Moving to ADC1 also removes the ADC2/WiFi
   conflict described in H-notes below.
5. **Add protection, now clearly warranted:** a 1 kΩ series resistor between the divider midpoint and
   GPIO14 to bound future diode current, plus a 100 nF cap from GPIO14 to GND for ADC sampling
   (schematic `C6`).

### Follow-up: sense tap moved, and the reading now needs filtering (all applied and verified)

Two further problems showed up once the divider was correct, and both are fixed and flashed.

**1. The tap sat after the Schottky, so the pack read ~0.33 V low.**

`gen_node_complete.py:156-158` puts the sense tap on the **cathode** of D1 (`12V_BUS`) — i.e. after
the PTC fuse *and* after the 1N5822. Measured on the bench: **12.94 V at the battery, 12.61 V at the
tap.** On LiFePO4's flat curve that 0.33 V is worth roughly **20 percentage points** of state of charge
(12.61 V ⇒ 15 %, 12.94 V ⇒ 35 %).

The tap was moved to the anode side — **after the fuse, before the diode** — keeping the sense line
fused while dropping the error from 330 mV to **~13 mV** (the residual is the PTC fuse drop at
~150 mA), plus the recommended 1 kΩ series resistor.

**2. A single ADC sample made the gauge flicker.**

`readBatteryVoltage()` took **one** `analogReadMilliVolts()` reading, and `main.cpp` converted the ADC
**three times** per cycle, so `battery_v` and `battery_raw_mv` came from unrelated samples. Measured
spread was **28 mV** at the pack — and because 12 mV is already 1 % of SoC on this chemistry, the gauge
visibly flickered.

Implemented in `sensors.cpp` / `config.h`:

- **Oversample** `BAT_ADC_SAMPLES` (32) times, discard the extreme samples, average.
- **Cache** the averaged sample for `BAT_ADC_CACHE_MS` (500 ms) so every caller in one cycle — the
  LoRa payload, the telemetry cache, and the raw-mV readout — reports the *same* conversion.
- **EMA** across cycles (`BAT_ADC_EMA_ALPHA` 0.25) for the residual variation, which is real load sag
  from WiFi bursts rather than ADC noise. A step larger than `BAT_ADC_EMA_SNAP_V` (0.5 V) snaps
  instead of slewing, so reconnecting a battery is not lagged.
- `battery_raw_mv` deliberately stays **unsmoothed** for debugging.

Measured after flashing, 14 cycles:

| Metric | Before | After |
|---|---|---|
| Pack voltage spread | 28 mV | **10 mV** |
| Raw ADC spread | 5 mV | **2 mV** |
| Sequence | 12.92 ↔ 12.93 flicker | **monotonic drift** 12.920 → 12.930 |
| Accuracy vs 12.94 V battery | −330 mV | **−13 mV** |

### NEW: the MOSFET switch never turns on if R2 is missing — and the UI cannot tell

The node reports `12V_SW MOSFET: ON` while the multimeter reads **0 V** at J2. The UI flag is not a
measurement: `getMosfetState()` returns the `mosfetActive` software flag set by `digitalWrite()`
(`sensors.cpp:62-64`), so it reads ON regardless of what the hardware is doing. There is no feedback path.

The reported cause was the **1 kΩ gate resistor (R2) not yet connected** between GPIO15 and the 2N7000
gate (`gen_node_complete.py:182-184`). With the gate floating, Q2 never conducts, R1 (10 kΩ) holds the
IRF4905 gate at 12 V, Vgs = 0, and the P-FET stays off.

Also found: **`gen_node_complete.py:118` documents the wrong IRF4905 pin map** — it says
`1=D 2=G 3=S`, but the real TO-220 IRF4905 is **1=Gate, 2=Drain, 3=Source**. The wiring code on lines
179-186 correctly assumes the real pinout, so the comment is what is wrong — but hand-wiring to it
would swap Gate and Drain and the switch would never work.

**Two additions recommended:**

1. Connect **R2 (1 kΩ): GPIO15 → 2N7000 gate (pin 2)**.
2. Add a **10 kΩ pulldown from the 2N7000 gate to GND**. In deep sleep GPIO15 goes high-impedance, so
   without it the Q2 gate floats and the sensor rail state is undefined — it can partially turn on Q1
   (heat, wasted current) or fail to release the rail, draining the battery. A pulldown guarantees the
   rail is off during boot, reset, and sleep.

Verification order: GPIO15 3.3 V → 2N7000 gate 3.3 V → **IRF4905 gate 12 V falling to ~0 V** → 12 V at J2.

---

## 2c. CONFIRMED ON HARDWARE (2026-09-29): I2C never detected — RESOLVED

**Status: RESOLVED and verified on hardware.** After tying `CS` → 3.3 V, `SDO` → GND, and applying
the firmware fix below, the node reports live values: **29.3 °C / 37.5 % RH / 1009.3 hPa**, drifting
normally between samples. Battery simultaneously reads **12.62 V from 2219 mV ADC** — i.e.
`2219 × 5.70 / 1000 = 12.65 V`, a 0.2 % error, confirming the 2b divider fix as well.

Attribution is shared and cannot be separated: the `CS` → 3.3 V change (which takes the chip out of
SPI mode) is almost certainly what made the device ACK, while the firmware fix removed a latent defect
that would have re-broken the bus on every web-triggered scan and every 3 s retry.

Bench symptom (before the fix): **BME280 never appears on the I2C bus**; reversing SDA and SCL did not help.

### Root cause: the wiring doc is wrong, and it is wrong in the one way that matters

| Source | Assignment |
|---|---|
| **`config.h:44-45` — what the firmware compiles with** | `PIN_I2C_SDA = 1`, `PIN_I2C_SCL = 2` |
| `docs/sensor-wiring.md:37-38` | `SCL → GPIO1`, `SDA → GPIO2` — **swapped** |
| `docs/pin-configuration-guide.md:17-18,298-299` | `SDA = GPIO1`, `SCL = GPIO2` — agrees with the code |

Wiring to the documentation therefore **inverts the bus**, and no device will ACK. The firmware is
correct; `sensor-wiring.md:37-38` must be fixed.

**Correct wiring: SDA → GPIO1, SCL → GPIO2.**

### Second suspect: the switched 3.3 V sensor rail

The BME280 is not on permanent 3.3 V — `VIN` sits on the MOSFET-switched rail (`config.h:69`,
`sensors.cpp:4-5`). `sensorsInit()` does power it on (`sensors.cpp:188`), but:

- pressing **`m`** in the serial console toggles the rail **off** (`main.cpp:149-157`), killing the sensor;
- if the MOSFET stage is not yet built (this was an incremental bench build), the sensor may have no
  supply at all.

### Built-in diagnostics the firmware already provides

| Message | Location | Meaning |
|---|---|---|
| `[I2C] Bus lines are held LOW! (Check 3.3V power). Skipping BME280.` | `sensors.cpp:195` | SDA/SCL held LOW — rail dead or line shorted to GND |
| `-> No I2C devices found!` | `sensors.cpp:116` | Bus idles HIGH but nothing ACKs — swapped lines, wrong address, or dead sensor |
| `-> Found I2C device at 0x76 (BME280 / BMP280)` | `sensors.cpp:92-94` | Device detected |

### SPI-labelled module used in I2C mode (added 2026-09-29)

The bench module exposes **SPI labels** — `3Vo, SCK, SDO, SDI, CS`. The BME280 supports I2C, but
**only when `CSB` is tied HIGH**; otherwise the chip stays in SPI mode and never ACKs an I2C scan.

Correct I2C mapping for this module:

| Module pin | I2C role | Connect to |
|---|---|---|
| `3Vo` | supply | 3.3 V |
| `GND` | ground | GND |
| `SCK` | **SCL** | GPIO2 (`PIN_I2C_SCL`) |
| `SDI` | **SDA** | GPIO1 (`PIN_I2C_SDA`) |
| `CS` | interface select | **3.3 V — required for I2C** |
| `SDO` | address select | GND → `0x76`, 3Vo → `0x77` |

Two common mistakes with this exact board:

1. **`CS` left floating or grounded** → chip remains in SPI mode → no I2C device ever appears.
2. **`SDO` wired to SDA instead of `SDI`** — the "Data Out" label is misleading; in I2C mode the data
   line is `SDI` and `SDO` only selects the address.

Also expect: these SPI-style boards are frequently **BMP280, not BME280** (no humidity). The firmware
handles this and prints `[BMP280] Connected at 0x76 (No Humidity)` (`sensors.cpp:212-219`). Many of
these boards also have **no onboard I2C pull-ups** — add 4.7 kΩ from SDA→3.3 V and SCL→3.3 V if
SDA→3Vo / SCL→3Vo measures open.

### Fix / verification steps

1. Rewire **SDA → GPIO1, SCL → GPIO2** (trust the code, not `sensor-wiring.md`).
2. **Tie `CS` → 3.3 V** and wire the module's **`SDI` → GPIO1, `SCK` → GPIO2, `SDO` → GND**.
3. Power the BME280 **directly from 3.3 V** while bench-testing, bypassing the MOSFET rail.
4. Measure VCC at the module (expect 3.3 V) and the pull-ups SDA→VCC and SCL→VCC (expect 4.7–10 kΩ).
5. Press **`s`** for a manual rescan (`main.cpp:142-145`) and read which of the three messages appears.
6. Fix `docs/sensor-wiring.md:37-38` and add this module's SPI→I2C mapping so the next person does not
   repeat this.

### Code defect found in the I2C path: `sensorsScanI2C()` clobbers its own bus

This is a genuine firmware bug and it can plausibly explain *persistent* detection failure.

```cpp
sensorsInit():
  197:  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);   // peripheral now owns GPIO1/GPIO2
  199:  sensorsScanI2C();                        // ...which then does:

sensorsScanI2C():
   75:  pinMode(PIN_I2C_SDA, INPUT_PULLUP);      // demotes the pins to plain GPIO
   76:  pinMode(PIN_I2C_SCL, INPUT_PULLUP);
   84:  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);    // re-begin on an already-begun bus
```

`sensorsScanI2C()` reconfigures the I2C pins as plain GPIO **after** the caller has already attached
them to the I2C peripheral, then calls `Wire.begin()` a second time. On Arduino-ESP32 a `begin()` on an
already-initialised `Wire` does not reliably re-establish the pin routing, so the peripheral can be left
talking to pins it no longer drives — nothing ACKs.

Worse, this function is re-entered **every 3 s** from the retry loop (`main.cpp:168-174`) and on **every
"Scan I2C Bus" click** (`config_server.cpp:143`), so a bus that gets clobbered this way never recovers
on its own.

**Recommended fix:** let one place own the I2C pins.

```cpp
static bool i2cStarted = false;

void sensorsScanI2C() {
  Serial.println("[I2C] Scanning bus (SDA=GPIO1, SCL=GPIO2)...");

  if (!i2cStarted) {                       // probe the lines only BEFORE the peripheral owns them
    pinMode(PIN_I2C_SDA, INPUT_PULLUP);
    pinMode(PIN_I2C_SCL, INPUT_PULLUP);
    delay(10);
    if (digitalRead(PIN_I2C_SDA) == LOW || digitalRead(PIN_I2C_SCL) == LOW) {
      Serial.println("  -> WARNING: I2C bus is stuck LOW!");
      return;
    }
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setTimeOut(50);
    i2cStarted = true;
  }
  /* ...scan loop unchanged... */
}
```

Then delete the duplicate `pinMode` (lines 191-192) and `Wire.begin`/`setTimeOut` (lines 197-198) from
`sensorsInit()`. Never call `pinMode()` on an I2C pin after `Wire.begin()`.

### Related: no I2C mutex between the two cores

The web server task runs on Core 0 (`config_server.cpp:310-318`) and the read loop on Core 1
(`main.cpp:180`); both use `Wire` with no shared lock. A "Scan I2C" click during a BME read corrupts
both transactions. Guard every `Wire` operation with a shared `SemaphoreHandle_t`.

### New observations after the fix (not blockers)

- **Soil moisture saturates at 100 %** and its ADC wanders: raw readings of 943 / 749 / 965 / 720 mV
  across consecutive samples. `sensors.cpp:134` maps anything `<= 1200 mV` to 100 %, so a disconnected
  or floating probe reads a permanent 100 %.
- **The ADC2-under-WiFi hypothesis was NOT confirmed.** The battery on GPIO14 (also ADC2, with WiFi
  active in TEST_MODE) is rock-steady at 2218–2221 mV. The soil swing is therefore more likely a probe
  or input-impedance issue than an ADC2 artefact. The earlier "both analog inputs are on ADC2" concern
  stands as a design smell, not a proven defect.
- **Wind sensors return 0.0 m/s and 0° but report success** (not timeout), so the Modbus slaves answer;
  the zero values need verifying against a known input.

### FIXED: battery state-of-charge was computed for the wrong chemistry

The node UI showed **100 %** on a **4S LiFePO4** pack reading 12.64 V. The gauge was hard-coded for
3S Li-Ion (`webui/src/routes/+page.svelte`: `if (v >= 12.6) return 100`), so a pack at ~3.16 V/cell —
roughly 15 % full — displayed as fully charged. LiFePO4 has a very flat discharge curve, so no linear
map is correct.

Replaced with a per-cell rest-voltage lookup table interpolated across 13 points
(`10.00 V → 0 %` … `13.80 V → 100 %`). 12.64 V now yields **15 %**. The card also shows **V/cell**,
which makes cell imbalance visible. Rebuilt with `pnpm build` and flashed via `pio run -t uploadfs`.

### NEW: `ds18b20_temp` is a duplicate of `bme_temp`, not a second sensor

Confirmed from live telemetry — both fields return the identical value:

```json
{"bme_temp":29.37, ..., "ds18b20_temp":29.37, ...}
```

They are the same number by construction, not by coincidence:

1. `sensorsRead()` overwrites the BME280 temperature with the DS18B20 reading when one is present
   (`sensors.cpp:289`: `data.temperature = dsTemp;`).
2. `updateTelemetryCache()` then assigns `cachedTelem.ds18b20_temp = data.temperature;`
   (`config_server.cpp:47`) — the **already-overwritten** field.
3. The JSON emits both `bme_temp` and `ds18b20_temp` from that one value
   (`config_server.cpp:111,114`).

So the UI's "DS18B20 Probe" readout is meaningless, and the "BME280 / BMP280" label under the main
temperature card is wrong whenever a DS18B20 is connected. The separate accessors
`readBmeTemp()` / `readDS18B20Temp()` (`sensors.cpp:327-359`) exist but are never used by the telemetry
cache. Fix: read both sensors into distinct `SensorData` fields.

---

## 3. High-severity findings

| # | Finding | Evidence | Impact |
|---|---|---|---|
| H1 | **Shipped state is test mode.** `TEST_MODE true`, `SLEEP_INTERVAL_S 5` | `config.h:24,26` | Node never deep-sleeps, never calls `loraInit()`/`loraSend()`. Production path is unreachable and untested by this build. |
| H2 | **The manual rain reset silently does nothing** | `getRainTips()` (`sensors.cpp:319-325`) is a pure getter, yet `sensors.h:45-46` documents it as "(resets counter)"; `main.cpp:147` prints "reset to 0" and the web handler returns `{"success":true}` | The **automatic** reset in `sensorsRead()` (`sensors.cpp:298-299`) does work, so normal cycles are fine — but the `r` serial command and the UI "Reset Rain" button report success while changing nothing. |
| H2b | **`sensorsScanI2C()` clobbers its own I2C bus** | `sensors.cpp:75-76,84` re-run `pinMode(INPUT_PULLUP)` and `Wire.begin()` *after* the caller already attached the peripheral (`:197`) | Pins can be left demoted to plain GPIO with the peripheral still driving nothing ⇒ `No I2C devices found` that **never recovers**, because the same clobber re-runs every 3 s (`main.cpp:168-174`) and on every web scan (`config_server.cpp:143`). Fix in 2c. |
| H3 | **Dashboard weather data is mock by default** | `dashboard/src/lib/server/db.ts:16` defaults to password literally `***`, while compose uses `changeme` (`docker-compose.yml:19`) | Auth fails, `markDBFailed()` latches permanently (`db.ts:29-36`), every page renders `Math.random()` sinusoids (`mock-data.ts:12-30`) **with no "demo data" badge**. A stakeholder demo can present invented data as live. |
| H4 | **Unauthenticated host recon + shell-out** | `api/system/+server.ts:22-54`, `api/docker/+server.ts:16-19` | Any client reaching the dashboard gets hostname, distro, CPU, RAM, disk, and container inventory. `execSync` is a command-execution sink, blocks the event loop up to 5 s, spawns a process per request, and is Linux-only. No injection exists today (no user input interpolated) but it is one string-concat away. |
| H5 | **Unauthenticated MQTT on all interfaces** | `mosquitto.conf:5` `allow_anonymous true`; ports 5432/1883/3000/8081 published on 0.0.0.0 (`docker-compose.yml:21,37,48,63`) | Any LAN host can read/write all telemetry or forge packets. Postgres password `changeme`, Grafana `admin` — shipped defaults. |
| H6 | **Two competing schema definitions** | `server/src/db.ts:21-68` vs `database/migrations/001_initial_schema.sql` | `node_id` is `NOT NULL` only in the SQL; `sensor_daily` exists **only** in the SQL. Whichever runs first wins via `IF NOT EXISTS`. Guaranteed drift. |
| H7 | **`server/src/migrate.ts` does not exist** but `package.json:10` advertises `npm run db:migrate` | — | Documented command fails immediately. README `:43` points at the wrong entry point. |
| H8 | **`sensor_daily` is never populated** | Defined at `001_initial_schema.sql:49-66`; no writer exists anywhere | The "fast Grafana dashboards" table is dead weight. |
| H9 | **RSSI/SNR are computed then discarded** | `lora_gateway.py:133` computes `rssi`; `:136` publishes only the payload | `ingest.ts:44` accepts them but `index.ts:36` never passes them ⇒ columns always NULL, LoRa signal panels permanently empty. |
| H10 | **OTA partitions provisioned, no OTA code** | `partitions_16mb.csv:3-5` (otadata + app0/app1, 3 MB each) | 3 MB reserved and unused; updates require USB. |
| H11 | **Sensor faults are indistinguishable from real zeros** | `sensors.cpp:267` zero-init, no validity flags; `:304,:309` collapse errors to 0 | NaN serializes to JSON `null`, and the UI calls `.toFixed()` unconditionally (`+page.svelte:247,265,280,317,343`) ⇒ render-time TypeError when a sensor drops out. Error branches at `main.cpp:198-206` are dead code. |
| H12 | **No I2C or MOSFET-rail locking** | Core-0 web task `config_server.cpp:310-318` → `sensorsScanI2C` → `Wire.begin()`; Core-1 reads BME280 at `main.cpp:180` | Concurrent bus access; GPIO15 written from two cores with no mutex. |
| H13 | **Default PlatformIO env cannot compile** | `platformio.ini:6-16` `[env:wroom32]` omits ArduinoJson, FastLED, NeoPixel, ModbusMaster — all `#include`d by `src/` | Only `[env:s3]` is viable. |
| H14 | **`pin-configuration-guide.md` contradicts itself** | E22 UART on GPIO4-8 (`:48-57`) vs SX1276 SPI NSS/SCK/MOSI/MISO/RST/DIO0 on GPIO4-9 (`:301-306`) | Stale SPI section never removed. |
| H15 | **Mixed radio families, unverified interop** | Gateway: SX1276/SX1278 SPI via `SX127x` lib (`lora_gateway.py:25`). Firmware: Ebyte E22-900T22D UART transparent mode. | Air parameters (frequency, SF9, BW125, sync word, preamble) exist **only in the E22 module's flash** and are absent from the repo. A replaced module or new node silently fails to link. |
| H16 | **Canonical schematic has never passed ERC** | `konnect-trial/verification.json:4` → `"kicad_erc": "unavailable"` | The only full-board ERC on record is the **archived v2** board, and it **fails: 62 errors, 139 warnings** (`weather-power-pcb-erc.rpt:618`). The 0/0 reports (`minimal_sch-erc.rpt`, `test_direct-erc.rpt`) are for throwaway test schematics whose inputs are not in the repo — they prove nothing about any real board. |
| H17 | **"Zero overlaps" claim is contradicted by its own committed report** | `konnect-trial/README.md:7` vs `overlaps-after.json` → `overlap_count: 3` (U1/#PWR33, U1/#PWR44, U3/#PWR40) | The verification narrative overstates what was proven. |
| H18 | **Canonical node sheet has no battery front end** | `gen_node_complete.py:55-58` — input is barrel jack + PTC + 1N5822 + 100 µF | No BMS, charge controller, UVLO, or low-temperature cutoff on the schematic. BMS/UVLO exist only in prose. |
| H19 | **Hardware is unreproducible here** | `gen_node_complete.py:12,17` require `kicad-sch-api` + Linux paths; absent (`installation.json:33-36`) | Generated artifacts are committed beside their generators, so drift is *visible* in git but not *detectable*. No node `.kicad_pcb` exists at all; only 4 of 22 components have footprints. |

---

## 4. Medium and low findings

- **`wroom32`↔schema drift in the node detail page:** `api/nodes/[id]/+server.ts:23-26` returns Drizzle camelCase keys while the UI reads snake_case (`nodes/[id]/+page.svelte:22-24`) ⇒ "SF" and "Sleep" render blank in real mode.
- **Any malformed id permanently disables the DB:** only `NaN` is rejected (`nodes/[id]/+server.ts:9-12`), so `/api/nodes/1.5` throws → `markDBFailed()` latches mock forever.
- **Mock pagination is broken:** `readings/+server.ts:15-17` hardcodes `limit: 5, total: 500`, so `/readings` shows 5 rows while claiming "1–20 of 500".
- **`idx_daily_node_date` collision:** Drizzle declares it `uniqueIndex` (`dashboard/.../schema.ts:53`) but the SQL creates it **non-unique** with the same name (`001:65-66`); real uniqueness is an unnamed `UNIQUE(node_id, date)`.
- **No graceful shutdown:** `index.ts:45-49` never awaits `client.end()`, never closes the pool, `process.exit(0)` kills in-flight inserts; the async MQTT handler (`:32-38`) has no `.catch`.
- **No retry if Postgres is down at start** (`index.ts:12,54-57`). FK on `node_id` silently drops unseeded nodes; seeds create ids 1–2 (`sample_nodes.sql:3-5`) while dashboards query node 3.
- **`drizzle-orm`/`drizzle-kit` declared in `server/package.json:16-17` but never imported** — contradicting the commit message "SvelteKit dashboard with sidebar layout + Drizzle ORM".
- **No `drizzle.config.ts`** anywhere, so `drizzle-kit` cannot run and the Drizzle schema is decorative.
- **`config.ts:6` fallback DSN omits the password**; `LOG_LEVEL` is read (`:12`) and never used.
- **`adapter-auto` with no adapter-node** (`dashboard/svelte.config.js`) leaves the production build target undefined; `pg`/`drizzle-orm` are runtime imports in `devDependencies` (`package.json:20-24`), breaking `npm ci --omit=dev`.
- **Schema design:** `wind_dir_avg NUMERIC(4,1)` (`001:60`) is a linear mean of a **circular** quantity (350° and 10° average to 180°); no CHECK constraints; no `ON DELETE` on the FK; no TimescaleDB, partitioning, or **retention policy**; `measured_at` exists but is never written; `sample_nodes.sql:6` `ON CONFLICT DO NOTHING` has no conflict target so reruns duplicate rows.
- **Lockfile/tooling split:** `dashboard/` uses npm (`package-lock.json`), `webui/` uses pnpm.
- **Dead links:** `/settings` (`Sidebar.svelte:42`) and four `/charts/*` pages (`charts/+page.svelte:36-55`) 404; `/charts` is not in the sidebar; `favicon.png` referenced (`app.html:6`) but `static/` holds only `robots.txt`.
- **`dashboard/README.md` is untouched `sv create` boilerplate.**
- **`docs/troubleshooting.md` referenced from `docs/deployment.md:214` but does not exist** (the only dead doc reference in the repo).
- **BOM totals do not reconcile:** ₱9,860 (`session-progress.md:35`, no line items) vs ₱4,195 (`power-configuration.md:533`) vs ₱3,380–6,200 (`power-bom-solar-lifepo4.md:150`) vs ₱2,312–3,581 (`power-bom-shopee-complete.md:90`). Arithmetic errors: Phase 1 sums to ₱824 but states ₱825 (`:487-510`); shopee section sums to ₱2,020/₱3,030 but states ₱1,480/₱2,280 (`:85-86`). No BOM exists for the canonical Mini560 + AMS1117 design.
- **`sensor-wiring.md` has SDA/SCL swapped relative to the firmware** — promoted from Low to **High** after it was confirmed as a bench blocker (see 2c). The docs disagree with each other as well as with the code.
- **Doc/banner incoherence:** the 2026-09-29 pass added "canonical" banners without deleting contradicting bodies, so `power-configuration.md` and `sensor-wiring.md` now contradict themselves (banner says Mini560/AMS1117, body still bills 2× Mini560 and headlines LM2596).

- **Repo clutter:** `output/schematic-review/` holds committed "before-final" snapshots (1.4 MB); `hardware/node-pcb/weather-node-complete.svg/` is a directory whose name ends in `.svg`; `hardware/power-supply/power-supply.kicad_sch` is a third, unreferenced variant; `weather-power-v3.kicad_sch` has 24 placements, **0 wires**, and 23 labels — it is a parts list, not a circuit.
- **`firmware/weather-node/data/`** ships 47 `.gz`/`.br` precompressed files that the ESP32 `WebServer` never negotiates — wasted LittleFS space.

---

## 5. What is genuinely good

- **Excellent git hygiene:** 129 files / 3.39 MB tracked, dependencies and build output ignored, no secrets, no BOMs, no mixed line endings.
- **The happy path is genuinely wired:** firmware JSON keys (`packet.cpp:14-22`) → gateway publishes verbatim → ingestor expects the identical key set (`ingest.ts:21-33`) → parameterized INSERT. **No field-name mismatch anywhere**, and the README example matches.
- **No SQL injection:** `ingest.ts:64-86` uses `$1..$13` placeholders; the only concatenated SQL is a hardcoded constant array (`db.ts:59-62`).
- **Correct timezone types:** `TIMESTAMPTZ` for both timestamps (`001:25-26`); `secureJsonData` used for the Grafana password.
- **TypeScript config is sound:** `strict` on, correct NodeNext `.js` import specifiers.
- **Firmware source is complete and honestly commented:** no TODO/FIXME/stub markers in `src/`, every declared function implemented, and `lora.h:27` openly acknowledges transparent mode has no ACK.
- **The konnect trial left real evidence** rather than prose: 0 shorts before and after, 0 orphans, 96/96 bounds resolved.
- **Doc links are 20/21 valid** — unusually disciplined.

---

## 6. Recommended remediation order

**Bench blockers — confirmed on hardware, do these first (2b, 2c):**

0a. **Replace the battery divider's top resistor 4.7 kΩ → 47 kΩ (2b).** GPIO14 has been running at 4.26 V against a 3.3 V limit, with ~1.2 mA injected through the ESD diode. Verify the pin still reads linearly before trusting it.
0b. **Rewire I2C as SDA → GPIO1, SCL → GPIO2 (2c)** — trust the firmware, not `sensor-wiring.md:37-38` — and power the BME280 from a permanent 3.3 V rail while bench-testing. Then fix the doc.

Nothing else can be validated until the sensor bus and the battery sense both work.

1. **Resolve the divider across the repo (C1).** After the hardware fix, set `config.h`, every doc, and the schematic to the single value 5.70 (47k/10k). Nothing about battery health is trustworthy until this is done.
2. **Widen `battery_v` to `NUMERIC(4,2)` (C2)** in `001_initial_schema.sql` and `db.ts`, then make the SQL migration the single source of truth and delete the duplicated DDL. Add 0–100 CHECKs on humidity/soil.
3. **Fix the Grafana datasource (C3):** add `uid: WeatherStation`, pin the Grafana image, align `type`. Confirm by loading the dashboard once.
4. **Turn off test mode and fix the rain reset (H1, H2)** — one-line changes with immediate correctness impact.
5. **Set a real `DATABASE_URL` for the dashboard (H3)** and badge the UI when serving mock data, so a demo can never silently show fabricated readings again.
6. **Add auth (H4, H5)** or at minimum bind the dashboard, MQTT, and Postgres to localhost and remove the shell-out endpoint.
7. **Then** the verification work: build the firmware (`pio` is not installed here), get the canonical schematic through a real ERC, and add a single end-to-end smoke test.

---

## 7. Honest summary

The design thinking is good and the intent is legible: a documented, well-commented, cleanly-versioned
solar weather station. The battery-monitoring path is nonetheless wrong in three independent ways at once
(wrong constant, wrong column type, contradicted by its own docs), the dashboard can present invented
data as real, and the canonical schematic has never been electrically checked while the one ERC report
that does exist fails with 62 errors.

The best single sentence: **this is a prototype whose documentation is better than its verification.**
Fix the divider and the numeric types first — those two changes alone turn a pipeline that discards
every real reading into one that stores them.
