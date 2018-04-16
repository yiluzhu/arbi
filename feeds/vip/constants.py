HOSTS = ['110.173.53.154', '183.60.204.26', '14.17.93.54', '122.224.35.65']
PORTS = [8090, 8091]

ACCOUNT_MAP = {
    0: ('ss9010', 'aaa333'),  # for testing
    1: ('ss1313', 'qaz123'),  # for prod
    99: '',  # this is dummy account that used in tests
}

TC_TOOL_ACCOUNT = 'ss9003', 'aaa333'
OH_TOOL_ACCOUNT = 'ss2010', 'aaa111'

BACKUP_ACCOUNT = 'ss0016', 'aaa111'

TIME_THRESHOLD_TO_GET_ONE_PACKET = 2
READ_BLOCK_SIZE = 4096
SOCKET_TIMEOUT_IN_SECONDS = 30
RECONNECT_DELAY = 15
