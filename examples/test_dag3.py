import time
import random
from faker import Faker
from thread_order import dmark, configure_logging, ThreadProxyLogger

logger = ThreadProxyLogger()

def setup_state(state):
    state.update({
        "faker": Faker(),
    })

def run(name, state, deps=None, fail=False):
    # Example of safe shared-state usage (faker + lock)
    with state["_state_lock"]:
        last_name = state["faker"].last_name()
    sleep = random.uniform(1, 4)
    logger.debug(f'{name} "{last_name}" running - sleeping {sleep:.2f}s')
    time.sleep(sleep)

    if fail:
        assert False, "Intentional Failure"

    results = []
    for dep in (deps or []):
        dep_result = state.get(dep, "--no-result--")
        results.append(f"{name}.{dep_result}")
    if not results:
        results.append(name)

    state[name] = "|".join(results)

# ---------------------------------------------------------------------------
# Layer 1 (7 tests)
#   - test_01_03 has 7 children (layer2)
#   - test_01_04 has 3 children (layer2)
#   - test_01_07 has 1 child (layer2)
# ---------------------------------------------------------------------------
@dmark(with_state=True, tags="layer1")
def test_01_01(state): return run("test_01_01", state)

@dmark(with_state=True, tags="layer1")
def test_01_02(state): return run("test_01_02", state)

# parent of 7 children in layer2
@dmark(with_state=True, tags="layer1")
def test_01_03(state): return run("test_01_03", state)

# parent of 3 children in layer2
@dmark(with_state=True, tags="layer1")
def test_01_04(state): return run("test_01_04", state)

@dmark(with_state=True, tags="layer1")
def test_01_05(state): return run("test_01_05", state)

@dmark(with_state=True, tags="layer1")
def test_01_06(state): return run("test_01_06", state)

# parent of 1 child in layer2
@dmark(with_state=True, tags="layer1")
def test_01_07(state): return run("test_01_07", state)

# ---------------------------------------------------------------------------
# Layer 2 (11 tests total)
#   - children of test_01_03: 02_01, 02_02, 02_03, 02_04, 02_05, 02_06, 02_07
#   - children of test_01_04: 02_08, 02_09, 02_10
#   - child of   test_01_07: 02_11
#
# Additional fan-out from layer2:
#   - test_02_07 has 4 children (layer3)
#   - test_02_10 has 1 child (layer3)
#   - test_02_11 has 1 child (layer3)
# ---------------------------------------------------------------------------
@dmark(with_state=True, after=["test_01_03"], tags="layer2")
def test_02_01(state): return run("test_02_01", state, deps=["test_01_03"])

@dmark(with_state=True, after=["test_01_03"], tags="layer2")
def test_02_02(state): return run("test_02_02", state, deps=["test_01_03"])

@dmark(with_state=True, after=["test_01_03"], tags="layer2")
def test_02_03(state): return run("test_02_03", state, deps=["test_01_03"])

@dmark(with_state=True, after=["test_01_03"], tags="layer2")
def test_02_04(state): return run("test_02_04", state, deps=["test_01_03"])

@dmark(with_state=True, after=["test_01_03"], tags="layer2")
def test_02_05(state): return run("test_02_05", state, deps=["test_01_03"])

@dmark(with_state=True, after=["test_01_03"], tags="layer2")
def test_02_06(state): return run("test_02_06", state, deps=["test_01_03"])

# parent of 4 children in layer3
@dmark(with_state=True, after=["test_01_03"], tags="layer2")
def test_02_07(state): return run("test_02_07", state, deps=["test_01_03"])

@dmark(with_state=True, after=["test_01_04"], tags="layer2")
def test_02_08(state): return run("test_02_08", state, deps=["test_01_04"])

@dmark(with_state=True, after=["test_01_04"], tags="layer2")
def test_02_09(state): return run("test_02_09", state, deps=["test_01_04"])

# parent of 1 child in layer3
@dmark(with_state=True, after=["test_01_04"], tags="layer2")
def test_02_10(state): return run("test_02_10", state, deps=["test_01_04"])

# parent of 1 child in layer3
@dmark(with_state=True, after=["test_01_07"], tags="layer2")
def test_02_11(state): return run("test_02_11", state, deps=["test_01_07"])

# ---------------------------------------------------------------------------
# Layer 3 (6 tests)
#   - children of test_02_07: 03_01, 03_02, 03_03, 03_04
#   - child of   test_02_10: 03_05
#   - child of   test_02_11: 03_06
#
# Additional fan-out from layer3:
#   - test_03_04 has 4 children (layer4)
#   - test_03_06 has 1 child (layer4)
# ---------------------------------------------------------------------------
@dmark(with_state=True, after=["test_02_07"], tags="layer3")
def test_03_01(state): return run("test_03_01", state, deps=["test_02_07"])

@dmark(with_state=True, after=["test_02_07"], tags="layer3")
def test_03_02(state): return run("test_03_02", state, deps=["test_02_07"])

@dmark(with_state=True, after=["test_02_07"], tags="layer3")
def test_03_03(state): return run("test_03_03", state, deps=["test_02_07"])

# parent of 4 children in layer4
@dmark(with_state=True, after=["test_02_07"], tags="layer3")
def test_03_04(state): return run("test_03_04", state, deps=["test_02_07"])

@dmark(with_state=True, after=["test_02_10"], tags="layer3")
def test_03_05(state): return run("test_03_05", state, deps=["test_02_10"])

# parent of 1 child in layer4
@dmark(with_state=True, after=["test_02_11"], tags="layer3")
def test_03_06(state): return run("test_03_06", state, deps=["test_02_11"])

# ---------------------------------------------------------------------------
# Layer 4 (5 tests)
#   - children of test_03_04: 04_01, 04_02, 04_03, 04_04
#   - child of   test_03_06: 04_05
#
# Additional fan-out from layer4:
#   - test_04_04 has 4 children (layer5)
# ---------------------------------------------------------------------------
@dmark(with_state=True, after=["test_03_04"], tags="layer4")
def test_04_01(state): return run("test_04_01", state, deps=["test_03_04"])

@dmark(with_state=True, after=["test_03_04"], tags="layer4")
def test_04_02(state): return run("test_04_02", state, deps=["test_03_04"])

@dmark(with_state=True, after=["test_03_04"], tags="layer4")
def test_04_03(state): return run("test_04_03", state, deps=["test_03_04"])

# parent of 4 children in layer5
@dmark(with_state=True, after=["test_03_04"], tags="layer4")
def test_04_04(state): return run("test_04_04", state, deps=["test_03_04"])

@dmark(with_state=True, after=["test_03_06"], tags="layer4")
def test_04_05(state): return run("test_04_05", state, deps=["test_03_06"])

# ---------------------------------------------------------------------------
# Layer 5 (4 tests)
#   - children of test_04_04: 05_01, 05_02, 05_03, 05_04
# ---------------------------------------------------------------------------
@dmark(with_state=True, after=["test_04_04"], tags="layer5")
def test_05_01(state): return run("test_05_01", state, deps=["test_04_04"])

@dmark(with_state=True, after=["test_04_04"], tags="layer5")
def test_05_02(state): return run("test_05_02", state, deps=["test_04_04"])

@dmark(with_state=True, after=["test_04_04"], tags="layer5")
def test_05_03(state): return run("test_05_03", state, deps=["test_04_04"])

@dmark(with_state=True, after=["test_04_04"], tags="layer5")
def test_05_04(state): return run("test_05_04", state, deps=["test_04_04"])
