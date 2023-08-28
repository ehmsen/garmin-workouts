def recovery_step_generator(duration, pace=False) -> dict:
    step: dict = {}
    step['type'] = 'recovery'
    step['duration'] = duration
    if pace:
        step['target'] = 'RECOVERY_PACE'
    else:
        step['target'] = 'RECOVERY_HEART_RATE'
    step['description'] = 'Recovery pace'

    return step


def aerobic_step_generator(duration, pace=False) -> dict:
    step: dict = {}
    step['type'] = 'interval'
    step['duration'] = duration
    if pace:
        step['target'] = 'AEROBIC_PACE'
    else:
        step['target'] = 'AEROBIC_HEART_RATE'
    step['description'] = 'Aerobic pace'

    return step


def lt_step_generator(target: str, duration, pace=False) -> dict:
    if '>' in target:
        d, target = target.split('>')
        s: str = d + 's quicker than '
        d: str = d + '>'
    elif '<' in target:
        d, target = target.split('<')
        s = d + 's slower than '
        d = d + '<'
    else:
        d = ''
        s = ''
    step: dict = {}
    step['type'] = 'interval'
    step['duration'] = duration
    step['target'] = d + 'THRESHOLD_PACE'
    step['description'] = s + 'Threshold pace'

    return step


def lr_step_generator(duration, pace=False) -> dict:
    step: dict = {}
    step['type'] = 'interval'
    step['duration'] = duration
    if pace:
        step['target'] = 'LONG_RUN_PACE'
    else:
        step['target'] = 'LONG_RUN_HEART_RATE'
    step['description'] = 'Long run pace'

    return step


def marathon_step_generator(target: str, duration, pace=False) -> dict:
    if '>' in target:
        d, target = target.split('>')
        s: str = d + 's quicker than '
        d: str = d + '>'
    elif '<' in target:
        d, target = target.split('<')
        s = d + 's slower than '
        d = d + '<'
    else:
        d = ''
        s = ''
    step: dict = {}
    step['type'] = 'interval'
    step['duration'] = duration
    step['target'] = d + 'MARATHON_PACE'
    step['description'] = s + 'Marathon pace run'

    return step


def hm_step_generator(target: str, duration, pace=False) -> dict:
    if '>' in target:
        d, target = target.split('>')
        s: str = d + 's quicker than '
        d: str = d + '>'
    elif '<' in target:
        d, target = target.split('<')
        s = d + 's slower than '
        d = d + '<'
    else:
        d = ''
        s = ''
    step: dict = {}
    step['type'] = 'interval'
    step['duration'] = duration
    step['target'] = d + 'HALF_MARATHON_PACE'
    step['description'] = s + 'Half Marathon pace'

    return step


def tuneup_step_generator(duration) -> dict:
    step: dict = {}
    step['type'] = 'interval'
    step['duration'] = duration
    step['target'] = '10KM_PACE'
    step['description'] = '10K pace run'

    return step


def cooldown_step_generator(duration, pace=False) -> dict:
    step: dict = {}
    step['type'] = 'cooldown'
    step['duration'] = duration
    if pace:
        step['target'] = 'AEROBIC_PACE'
    else:
        step['target'] = 'AEROBIC_HEART_RATE'
    step['description'] = 'Aerobic pace'

    return step


def walk_step_generator(duration) -> dict:
    step: dict = {}
    step['type'] = 'recovery'
    step['duration'] = duration
    step['target'] = 'WALK'
    step['description'] = 'Walk'

    return step
