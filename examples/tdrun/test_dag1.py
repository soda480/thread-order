import time
import random
from faker import Faker
from thread_order import mark, ThreadProxyLogger

logger = ThreadProxyLogger()

def setup_state(state):
    state.update({'faker': Faker()})

def run(name, state, deps=None, fail=False):
    with state['_state_lock']:
        last_name = state['faker'].last_name()
    sleep = random.uniform(.5, 2.5)
    logger.debug(f'{name} \"{last_name}\" running - sleeping {sleep:.2f}s')
    time.sleep(sleep)
    if fail:
        assert False, 'Intentional Failure'
    else:
        results = []
        for dep in (deps or []):
            dep_result = state['results'].get(dep, '--no-result--')
            results.append(f'{name}.{dep_result}')
        if not results:
            results.append(name)
        logger.debug(f'{name} PASSED')
        return '|'.join(results)

@mark()
def pre_op_assessment_A(state): return run('pre_op_assessment_A', state)

@mark(after=['pre_op_assessment_A'])
def assign_surgical_staff_B(state): return run('assign_surgical_staff_B', state, deps=['pre_op_assessment_A'])

@mark(after=['pre_op_assessment_A'])
def prepare_operating_room_C(state): return run('prepare_operating_room_C', state, deps=['pre_op_assessment_A'])

@mark(after=['prepare_operating_room_C'])
def sterilize_instruments_D(state): return run('sterilize_instruments_D', state, deps=['prepare_operating_room_C'], fail=True)
    
@mark(after=['prepare_operating_room_C'])
def equipment_safety_checks_E(state): return run('equipment_safety_checks_E', state, deps=['prepare_operating_room_C'])

@mark(after=['assign_surgical_staff_B', 'sterilize_instruments_D'])
def perform_surgery_F(state): return run('perform_surgery_F', state, deps=['assign_surgical_staff_B', 'sterilize_instruments_D'])
