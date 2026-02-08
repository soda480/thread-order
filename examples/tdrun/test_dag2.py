import time
import random
from faker import Faker
from thread_order import mark, ThreadProxyLogger

logger = ThreadProxyLogger()

def setup_state(state):
    state.update({
        'faker': Faker()
    })

def run(name, state, deps=None, fail=False):
    with state['_state_lock']:
        last_name = state['faker'].last_name()
    sleep = random.uniform(1, 4.0)
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

# ---------------------------------------------------------------------------
# Layer 1 – Initial system + user setup
# ---------------------------------------------------------------------------
@mark(tags='layer1')
def test_init_platform(state): return run('test_init_platform', state)

@mark(tags='layer1')
def test_load_global_config(state): return run('test_load_global_config', state)

# parent of 4 children
@mark(tags='layer1')
def test_create_user_account(state): return run('test_create_user_account', state)

@mark(tags='layer1')
def test_validate_input_schema(state): return run('test_validate_input_schema', state)

@mark(tags='layer1')
def test_register_user_fails(state): return run('test_register_user_fails', state, fail=True)

# parent of 2 children
@mark(tags='layer1')
def test_initialize_org_context(state): return run('test_initialize_org_context', state)

@mark(tags='layer1')
def test_assign_default_roles(state): return run('test_assign_default_roles', state)

# parent of 3 children
@mark(tags='layer1')
def test_enable_feature_flags(state): return run('test_enable_feature_flags', state)

@mark(tags='layer1')
def test_finalize_bootstrap(state): return run('test_finalize_bootstrap', state)

# ---------------------------------------------------------------------------
# Layer 2 – Account & org wiring
# ---------------------------------------------------------------------------
@mark(after=['test_create_user_account'], tags='layer2')
def test_link_user_profile(state):
    return run('test_link_user_profile', state, deps=['test_create_user_account'])

# parent of 3 children
@mark(after=['test_create_user_account'], tags='layer2')
def test_provision_user_resources(state):
    return run('test_provision_user_resources', state, deps=['test_create_user_account'])

@mark(after=['test_create_user_account'], tags='layer2')
def test_user_provisioning_fails(state):
    return run('test_user_provisioning_fails', state, deps=['test_create_user_account'], fail=True)

@mark(after=['test_create_user_account'], tags='layer2')
def test_send_welcome_notification(state):
    return run('test_send_welcome_notification', state, deps=['test_create_user_account'])

@mark(after=['test_initialize_org_context'], tags='layer2')
def test_attach_user_to_org(state):
    return run('test_attach_user_to_org', state, deps=['test_initialize_org_context'])

# parent of 2 children
@mark(after=['test_initialize_org_context'], tags='layer2')
def test_apply_org_policies(state):
    return run('test_apply_org_policies', state, deps=['test_initialize_org_context'])

@mark(after=['test_enable_feature_flags'], tags='layer2')
def test_activate_beta_features(state):
    return run('test_activate_beta_features', state, deps=['test_enable_feature_flags'])

# parent of 2 children
@mark(after=['test_enable_feature_flags'], tags='layer2')
def test_sync_feature_matrix(state):
    return run('test_sync_feature_matrix', state, deps=['test_enable_feature_flags'])

@mark(after=['test_enable_feature_flags'], tags='layer2')
def test_log_feature_state(state):
    return run('test_log_feature_state', state, deps=['test_enable_feature_flags'])

# ---------------------------------------------------------------------------
# Layer 3 – Permissions & access
# ---------------------------------------------------------------------------
# parent of 3 children
@mark(after=['test_provision_user_resources'], tags='layer3')
def test_create_access_tokens(state):
    return run('test_create_access_tokens', state, deps=['test_provision_user_resources'])

@mark(after=['test_provision_user_resources'], tags='layer3')
def test_store_credentials(state):
    return run('test_store_credentials', state, deps=['test_provision_user_resources'])

@mark(after=['test_provision_user_resources'], tags='layer3')
def test_audit_user_creation(state):
    return run('test_audit_user_creation', state, deps=['test_provision_user_resources'])

# parent of 1 child
@mark(after=['test_apply_org_policies'], tags='layer3')
def test_enforce_policy_rules(state):
    return run('test_enforce_policy_rules', state, deps=['test_apply_org_policies'])

@mark(after=['test_apply_org_policies'], tags='layer3')
def test_cache_policy_snapshot(state):
    return run('test_cache_policy_snapshot', state, deps=['test_apply_org_policies'])

@mark(after=['test_sync_feature_matrix'], tags='layer3')
def test_update_runtime_flags(state):
    return run('test_update_runtime_flags', state, deps=['test_sync_feature_matrix'])

# parent of 1 child
@mark(after=['test_sync_feature_matrix'], tags='layer3')
def test_publish_feature_events(state):
    return run('test_publish_feature_events', state, deps=['test_sync_feature_matrix'])

@mark(after=['test_send_welcome_notification'], tags='layer3')
def test_verify_email_delivery(state):
    return run('test_verify_email_delivery', state, deps=['test_send_welcome_notification'])

# ---------------------------------------------------------------------------
# Layer 4 – Downstream capabilities
# ---------------------------------------------------------------------------
@mark(after=['test_create_access_tokens'], tags='layer4,capA')
def test_enable_api_access(state):
    return run('test_enable_api_access', state, deps=['test_create_access_tokens'])

# parent of 2 children
@mark(after=['test_create_access_tokens'], tags='layer4,capA')
def test_api_key_rotation_fails(state):
    return run('test_api_key_rotation_fails', state, deps=['test_create_access_tokens'], fail=True)

@mark(after=['test_create_access_tokens'], tags='layer4,capA')
def test_register_api_client(state):
    return run('test_register_api_client', state, deps=['test_create_access_tokens'])

@mark(after=['test_enforce_policy_rules'], tags='layer4,capB')
def test_block_unauthorized_access(state):
    return run('test_block_unauthorized_access', state, deps=['test_enforce_policy_rules'])

@mark(after=['test_publish_feature_events'], tags='layer4,capB')
def test_notify_integrations(state):
    return run('test_notify_integrations', state, deps=['test_publish_feature_events'])

# ---------------------------------------------------------------------------
# Layer 5 – Final provisioning
# ---------------------------------------------------------------------------
@mark(after=['test_api_key_rotation_fails'], tags='layer5')
def test_retry_key_rotation(state):
    return run('test_retry_key_rotation', state, deps=['test_api_key_rotation_fails'])

# parent of 1 child
@mark(after=['test_api_key_rotation_fails'], tags='layer5')
def test_escalate_rotation_failure(state):
    return run('test_escalate_rotation_failure', state, deps=['test_api_key_rotation_fails'])

@mark(after=['test_block_unauthorized_access'], tags='layer5')
def test_log_security_event(state):
    return run('test_log_security_event', state, deps=['test_block_unauthorized_access'])

# ---------------------------------------------------------------------------
# Layer 6 – Terminal outcome
# ---------------------------------------------------------------------------
@mark(after=['test_escalate_rotation_failure'], tags='layer6')
def test_close_incident_ticket(state):
    return run('test_close_incident_ticket', state, deps=['test_escalate_rotation_failure'])
