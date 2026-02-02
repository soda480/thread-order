import time
import random
from faker import Faker
from thread_order import mark, configure_logging, ThreadProxyLogger

logger = ThreadProxyLogger()


def setup_state(state):
    state.update({
        'faker': Faker()
    })

def run(name, state, deps=None, fail=False):
    with state['_state_lock']:
        last_name = state['faker'].last_name()
    sleep = random.uniform(.8, 6.0)
    logger.debug(f'{name} "{last_name}" running - sleeping {sleep:.2f}s')
    time.sleep(sleep)
    if fail:
        assert False, 'Intentional Failure'
    else:
        results = []
        for dep in (deps or []):
            dep_result = state.get(dep, '--no-result--')
            results.append(f'{name}.{dep_result}')
        if not results:
            results.append(name)
        state[name] = '|'.join(results)


# Layer 1 - 20 root tests

@mark(tags='layer1')
def test_01_01(state): return run('test_01_01', state)


@mark(tags='layer1')
def test_01_02(state): return run('test_01_02', state)


@mark(tags='layer1')
def test_01_03(state): return run('test_01_03', state)


@mark(tags='layer1')
def test_01_04(state): return run('test_01_04', state)


@mark(tags='layer1')
def test_01_05(state): return run('test_01_05', state)


@mark(tags='layer1')
def test_01_06(state): return run('test_01_06', state)


@mark(tags='layer1')
def test_01_07(state): return run('test_01_07', state)


@mark(tags='layer1')
def test_01_08(state): return run('test_01_08', state)


@mark(tags='layer1')
def test_01_09(state): return run('test_01_09', state)


@mark(tags='layer1')
def test_01_10(state): return run('test_01_10', state)


@mark(tags='layer1')
def test_01_11(state): return run('test_01_11', state)


@mark(tags='layer1')
def test_01_12(state): return run('test_01_12', state)


@mark(tags='layer1')
def test_01_13(state): return run('test_01_13', state)


@mark(tags='layer1')
def test_01_14(state): return run('test_01_14', state)


@mark(tags='layer1')
def test_01_15(state): return run('test_01_15', state)


@mark(tags='layer1')
def test_01_16(state): return run('test_01_16', state)


@mark(tags='layer1')
def test_01_17(state): return run('test_01_17', state)


@mark(tags='layer1')
def test_01_18(state): return run('test_01_18', state)


@mark(tags='layer1')
def test_01_19(state): return run('test_01_19', state)


@mark(tags='layer1')
def test_01_20(state): return run('test_01_20', state)


# Layer 2 - 20 tests, depending on layer 1

@mark(after=['test_01_01'], tags='layer2')
def test_02_01(state): return run('test_02_01', state, deps=['test_01_01'], fail=False)


@mark(after=['test_01_02', 'test_01_01'], tags='layer2')
def test_02_02(state): return run('test_02_02', state, deps=['test_01_02', 'test_01_01'], fail=False)


@mark(after=['test_01_03', 'test_01_02', 'test_01_04'], tags='layer2')
def test_02_03(state): return run('test_02_03', state, deps=['test_01_03', 'test_01_02', 'test_01_04'], fail=True)


@mark(after=['test_01_04', 'test_01_03'], tags='layer2')
def test_02_04(state): return run('test_02_04', state, deps=['test_01_04', 'test_01_03'], fail=False)


@mark(after=['test_01_05', 'test_01_04'], tags='layer2')
def test_02_05(state): return run('test_02_05', state, deps=['test_01_05', 'test_01_04'], fail=False)


@mark(after=['test_01_06', 'test_01_05', 'test_01_07'], tags='layer2')
def test_02_06(state): return run('test_02_06', state, deps=['test_01_06', 'test_01_05', 'test_01_07'], fail=False)


@mark(after=['test_01_07', 'test_01_06'], tags='layer2')
def test_02_07(state): return run('test_02_07', state, deps=['test_01_07', 'test_01_06'], fail=True)


@mark(after=['test_01_08', 'test_01_07'], tags='layer2')
def test_02_08(state): return run('test_02_08', state, deps=['test_01_08', 'test_01_07'], fail=False)


@mark(after=['test_01_09', 'test_01_08', 'test_01_10'], tags='layer2')
def test_02_09(state): return run('test_02_09', state, deps=['test_01_09', 'test_01_08', 'test_01_10'], fail=False)


@mark(after=['test_01_10', 'test_01_09'], tags='layer2')
def test_02_10(state): return run('test_02_10', state, deps=['test_01_10', 'test_01_09'], fail=False)


@mark(after=['test_01_11', 'test_01_10'], tags='layer2')
def test_02_11(state): return run('test_02_11', state, deps=['test_01_11', 'test_01_10'], fail=True)


@mark(after=['test_01_12', 'test_01_11', 'test_01_13'], tags='layer2')
def test_02_12(state): return run('test_02_12', state, deps=['test_01_12', 'test_01_11', 'test_01_13'], fail=False)


@mark(after=['test_01_13', 'test_01_12'], tags='layer2')
def test_02_13(state): return run('test_02_13', state, deps=['test_01_13', 'test_01_12'], fail=False)


@mark(after=['test_01_14', 'test_01_13'], tags='layer2')
def test_02_14(state): return run('test_02_14', state, deps=['test_01_14', 'test_01_13'], fail=False)


@mark(after=['test_01_15', 'test_01_14', 'test_01_16'], tags='layer2')
def test_02_15(state): return run('test_02_15', state, deps=['test_01_15', 'test_01_14', 'test_01_16'], fail=True)


@mark(after=['test_01_16', 'test_01_15'], tags='layer2')
def test_02_16(state): return run('test_02_16', state, deps=['test_01_16', 'test_01_15'], fail=False)


@mark(after=['test_01_17', 'test_01_16'], tags='layer2')
def test_02_17(state): return run('test_02_17', state, deps=['test_01_17', 'test_01_16'], fail=False)


@mark(after=['test_01_18', 'test_01_17', 'test_01_19'], tags='layer2')
def test_02_18(state): return run('test_02_18', state, deps=['test_01_18', 'test_01_17', 'test_01_19'], fail=False)


@mark(after=['test_01_19', 'test_01_18'], tags='layer2')
def test_02_19(state): return run('test_02_19', state, deps=['test_01_19', 'test_01_18'], fail=True)


@mark(after=['test_01_20', 'test_01_19'], tags='layer2')
def test_02_20(state): return run('test_02_20', state, deps=['test_01_20', 'test_01_19'], fail=False)


# Layer 3 - 20 tests, depending on layer 2

@mark(after=['test_02_01'], tags='layer3')
def test_03_01(state): return run('test_03_01', state, deps=['test_02_01'], fail=False)


@mark(after=['test_02_02', 'test_02_01'], tags='layer3')
def test_03_02(state): return run('test_03_02', state, deps=['test_02_02', 'test_02_01'], fail=False)


@mark(after=['test_02_03', 'test_02_02', 'test_02_04'], tags='layer3')
def test_03_03(state): return run('test_03_03', state, deps=['test_02_03', 'test_02_02', 'test_02_04'], fail=True)


@mark(after=['test_02_04', 'test_02_03'], tags='layer3')
def test_03_04(state): return run('test_03_04', state, deps=['test_02_04', 'test_02_03'], fail=False)


@mark(after=['test_02_05', 'test_02_04'], tags='layer3')
def test_03_05(state): return run('test_03_05', state, deps=['test_02_05', 'test_02_04'], fail=False)


@mark(after=['test_02_06', 'test_02_05', 'test_02_07'], tags='layer3')
def test_03_06(state): return run('test_03_06', state, deps=['test_02_06', 'test_02_05', 'test_02_07'], fail=False)


@mark(after=['test_02_07', 'test_02_06'], tags='layer3')
def test_03_07(state): return run('test_03_07', state, deps=['test_02_07', 'test_02_06'], fail=True)


@mark(after=['test_02_08', 'test_02_07'], tags='layer3')
def test_03_08(state): return run('test_03_08', state, deps=['test_02_08', 'test_02_07'], fail=False)


@mark(after=['test_02_09', 'test_02_08', 'test_02_10'], tags='layer3')
def test_03_09(state): return run('test_03_09', state, deps=['test_02_09', 'test_02_08', 'test_02_10'], fail=False)


@mark(after=['test_02_10', 'test_02_09'], tags='layer3')
def test_03_10(state): return run('test_03_10', state, deps=['test_02_10', 'test_02_09'], fail=False)


@mark(after=['test_02_11', 'test_02_10'], tags='layer3')
def test_03_11(state): return run('test_03_11', state, deps=['test_02_11', 'test_02_10'], fail=True)


@mark(after=['test_02_12', 'test_02_11', 'test_02_13'], tags='layer3')
def test_03_12(state): return run('test_03_12', state, deps=['test_02_12', 'test_02_11', 'test_02_13'], fail=False)


@mark(after=['test_02_13', 'test_02_12'], tags='layer3')
def test_03_13(state): return run('test_03_13', state, deps=['test_02_13', 'test_02_12'], fail=False)


@mark(after=['test_02_14', 'test_02_13'], tags='layer3')
def test_03_14(state): return run('test_03_14', state, deps=['test_02_14', 'test_02_13'], fail=False)


@mark(after=['test_02_15', 'test_02_14', 'test_02_16'], tags='layer3')
def test_03_15(state): return run('test_03_15', state, deps=['test_02_15', 'test_02_14', 'test_02_16'], fail=True)


@mark(after=['test_02_16', 'test_02_15'], tags='layer3')
def test_03_16(state): return run('test_03_16', state, deps=['test_02_16', 'test_02_15'], fail=False)


@mark(after=['test_02_17', 'test_02_16'], tags='layer3')
def test_03_17(state): return run('test_03_17', state, deps=['test_02_17', 'test_02_16'], fail=False)


@mark(after=['test_02_18', 'test_02_17', 'test_02_19'], tags='layer3')
def test_03_18(state): return run('test_03_18', state, deps=['test_02_18', 'test_02_17', 'test_02_19'], fail=False)


@mark(after=['test_02_19', 'test_02_18'], tags='layer3')
def test_03_19(state): return run('test_03_19', state, deps=['test_02_19', 'test_02_18'], fail=True)


@mark(after=['test_02_20', 'test_02_19'], tags='layer3')
def test_03_20(state): return run('test_03_20', state, deps=['test_02_20', 'test_02_19'], fail=False)


# Layer 4 - 20 tests, depending on layer 3

@mark(after=['test_03_01'], tags='layer4')
def test_04_01(state): return run('test_04_01', state, deps=['test_03_01'], fail=False)


@mark(after=['test_03_02', 'test_03_01'], tags='layer4')
def test_04_02(state): return run('test_04_02', state, deps=['test_03_02', 'test_03_01'], fail=False)


@mark(after=['test_03_03', 'test_03_02', 'test_03_04'], tags='layer4')
def test_04_03(state): return run('test_04_03', state, deps=['test_03_03', 'test_03_02', 'test_03_04'], fail=True)


@mark(after=['test_03_04', 'test_03_03'], tags='layer4')
def test_04_04(state): return run('test_04_04', state, deps=['test_03_04', 'test_03_03'], fail=False)


@mark(after=['test_03_05', 'test_03_04'], tags='layer4')
def test_04_05(state): return run('test_04_05', state, deps=['test_03_05', 'test_03_04'], fail=False)


@mark(after=['test_03_06', 'test_03_05', 'test_03_07'], tags='layer4')
def test_04_06(state): return run('test_04_06', state, deps=['test_03_06', 'test_03_05', 'test_03_07'], fail=False)


@mark(after=['test_03_07', 'test_03_06'], tags='layer4')
def test_04_07(state): return run('test_04_07', state, deps=['test_03_07', 'test_03_06'], fail=True)


@mark(after=['test_03_08', 'test_03_07'], tags='layer4')
def test_04_08(state): return run('test_04_08', state, deps=['test_03_08', 'test_03_07'], fail=False)


@mark(after=['test_03_09', 'test_03_08', 'test_03_10'], tags='layer4')
def test_04_09(state): return run('test_04_09', state, deps=['test_03_09', 'test_03_08', 'test_03_10'], fail=False)


@mark(after=['test_03_10', 'test_03_09'], tags='layer4')
def test_04_10(state): return run('test_04_10', state, deps=['test_03_10', 'test_03_09'], fail=False)


@mark(after=['test_03_11', 'test_03_10'], tags='layer4')
def test_04_11(state): return run('test_04_11', state, deps=['test_03_11', 'test_03_10'], fail=True)


@mark(after=['test_03_12', 'test_03_11', 'test_03_13'], tags='layer4')
def test_04_12(state): return run('test_04_12', state, deps=['test_03_12', 'test_03_11', 'test_03_13'], fail=False)


@mark(after=['test_03_13', 'test_03_12'], tags='layer4')
def test_04_13(state): return run('test_04_13', state, deps=['test_03_13', 'test_03_12'], fail=False)


@mark(after=['test_03_14', 'test_03_13'], tags='layer4')
def test_04_14(state): return run('test_04_14', state, deps=['test_03_14', 'test_03_13'], fail=False)


@mark(after=['test_03_15', 'test_03_14', 'test_03_16'], tags='layer4')
def test_04_15(state): return run('test_04_15', state, deps=['test_03_15', 'test_03_14', 'test_03_16'], fail=True)


@mark(after=['test_03_16', 'test_03_15'], tags='layer4')
def test_04_16(state): return run('test_04_16', state, deps=['test_03_16', 'test_03_15'], fail=False)


@mark(after=['test_03_17', 'test_03_16'], tags='layer4')
def test_04_17(state): return run('test_04_17', state, deps=['test_03_17', 'test_03_16'], fail=False)


@mark(after=['test_03_18', 'test_03_17', 'test_03_19'], tags='layer4')
def test_04_18(state): return run('test_04_18', state, deps=['test_03_18', 'test_03_17', 'test_03_19'], fail=False)


@mark(after=['test_03_19', 'test_03_18'], tags='layer4')
def test_04_19(state): return run('test_04_19', state, deps=['test_03_19', 'test_03_18'], fail=True)


@mark(after=['test_03_20', 'test_03_19'], tags='layer4')
def test_04_20(state): return run('test_04_20', state, deps=['test_03_20', 'test_03_19'], fail=False)


# Layer 5 - 20 tests, depending on layer 4

@mark(after=['test_04_01'], tags='layer5')
def test_05_01(state): return run('test_05_01', state, deps=['test_04_01'], fail=False)


@mark(after=['test_04_02', 'test_04_01'], tags='layer5')
def test_05_02(state): return run('test_05_02', state, deps=['test_04_02', 'test_04_01'], fail=False)


@mark(after=['test_04_03', 'test_04_02', 'test_04_04'], tags='layer5')
def test_05_03(state): return run('test_05_03', state, deps=['test_04_03', 'test_04_02', 'test_04_04'], fail=False)


@mark(after=['test_04_04', 'test_04_03'], tags='layer5')
def test_05_04(state): return run('test_05_04', state, deps=['test_04_04', 'test_04_03'], fail=False)


@mark(after=['test_04_05', 'test_04_04'], tags='layer5')
def test_05_05(state): return run('test_05_05', state, deps=['test_04_05', 'test_04_04'], fail=False)


@mark(after=['test_04_06', 'test_04_05', 'test_04_07'], tags='layer5')
def test_05_06(state): return run('test_05_06', state, deps=['test_04_06', 'test_04_05', 'test_04_07'], fail=False)


@mark(after=['test_04_07', 'test_04_06'], tags='layer5')
def test_05_07(state): return run('test_05_07', state, deps=['test_04_07', 'test_04_06'], fail=False)


@mark(after=['test_04_08', 'test_04_07'], tags='layer5')
def test_05_08(state): return run('test_05_08', state, deps=['test_04_08', 'test_04_07'], fail=False)


@mark(after=['test_04_09', 'test_04_08', 'test_04_10'], tags='layer5')
def test_05_09(state): return run('test_05_09', state, deps=['test_04_09', 'test_04_08', 'test_04_10'], fail=False)


@mark(after=['test_04_10', 'test_04_09'], tags='layer5')
def test_05_10(state): return run('test_05_10', state, deps=['test_04_10', 'test_04_09'], fail=False)


@mark(after=['test_04_11', 'test_04_10'], tags='layer5')
def test_05_11(state): return run('test_05_11', state, deps=['test_04_11', 'test_04_10'], fail=False)


@mark(after=['test_04_12', 'test_04_11', 'test_04_13'], tags='layer5')
def test_05_12(state): return run('test_05_12', state, deps=['test_04_12', 'test_04_11', 'test_04_13'], fail=False)


@mark(after=['test_04_13', 'test_04_12'], tags='layer5')
def test_05_13(state): return run('test_05_13', state, deps=['test_04_13', 'test_04_12'], fail=False)


@mark(after=['test_04_14', 'test_04_13'], tags='layer5')
def test_05_14(state): return run('test_05_14', state, deps=['test_04_14', 'test_04_13'], fail=False)


@mark(after=['test_04_15', 'test_04_14', 'test_04_16'], tags='layer5')
def test_05_15(state): return run('test_05_15', state, deps=['test_04_15', 'test_04_14', 'test_04_16'], fail=False)


@mark(after=['test_04_16', 'test_04_15'], tags='layer5')
def test_05_16(state): return run('test_05_16', state, deps=['test_04_16', 'test_04_15'], fail=False)


@mark(after=['test_04_17', 'test_04_16'], tags='layer5')
def test_05_17(state): return run('test_05_17', state, deps=['test_04_17', 'test_04_16'], fail=False)


@mark(after=['test_04_18', 'test_04_17', 'test_04_19'], tags='layer5')
def test_05_18(state): return run('test_05_18', state, deps=['test_04_18', 'test_04_17', 'test_04_19'], fail=False)


@mark(after=['test_04_19', 'test_04_18'], tags='layer5')
def test_05_19(state): return run('test_05_19', state, deps=['test_04_19', 'test_04_18'], fail=False)


@mark(after=['test_04_20', 'test_04_19'], tags='layer5')
def test_05_20(state): return run('test_05_20', state, deps=['test_04_20', 'test_04_19'], fail=False)
