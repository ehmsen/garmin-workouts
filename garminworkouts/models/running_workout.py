import json
import datetime

from garminworkouts.models.duration import Duration
from garminworkouts.utils import functional

SPORT_TYPES = {
    "running": 1,
}

STEP_TYPES = {
    "warmup": 1,
    "cooldown": 2,
    "interval": 3,
    "recovery": 4,
    "run": 5,
    "repeat": 6
}

END_CONDITIONS = {
    "lap.button": 1,
    "time": 2,
    "distance": 3,
}

TARGET_TYPES = {
    "no.target": 1,
    "power.zone": 2,
    "cadence.zone": 3,
    "heart.rate.zone": 4,
    "speed.zone": 5,
    "pace.zone": 6,  # meters per second
}


class RunningWorkout(object):
    _WORKOUT_ID_FIELD = "workoutId"
    _WORKOUT_NAME_FIELD = "workoutName"
    _WORKOUT_DESCRIPTION_FIELD = "description"
    _WORKOUT_OWNER_ID_FIELD = "ownerId"

    def __init__(self, sport_type, config, target, vVO2, fmin, fmax, plan, duration=None):
        self.sport_type = sport_type,
        self.config = config
        self.target = target
        self.vVO2 = vVO2
        self.fmin = fmin
        self.fmax = fmax
        self.plan = plan

        flatten_steps = functional.flatten(self.config["steps"])

        sec = 0
        meters = 0

        for step in flatten_steps:
            duration = self._get_duration(step)
            t2 = self._target_value_two(step)
            t1 = self._target_value_one(step)

            try:
                if 'ZONE' in step['target']:
                    t2 = round((t2 - fmin) / (fmax - fmin), 2) / vVO2 * 1000
                    t1 = round((t1 - fmin) / (fmax - fmin), 2) / vVO2 * 1000
            except ValueError:
                t2 = 0
                t1 = 0

            t0 = min(t1, t2)  # type: ignore
            duration_secs = 0

            if duration:
                if self._end_condition(step)['conditionTypeKey'] == 'time':
                    duration_secs = self._end_condition_value(step)
                    duration_meters = round(duration_secs * t0)
                if self._end_condition(step)['conditionTypeKey'] == 'distance':
                    duration_meters = self._end_condition_value(step)
                    duration_secs = round(duration_meters / t0)

            sec = sec + duration_secs  # type: ignore
            meters = meters + duration_meters  # type: ignore

        try:
            self.ratio = round(self.vVO2 / (sec / meters * 1000) * 100)
        except ValueError:
            self.ratio = 0

        self.duration = datetime.timedelta(seconds=(sec//60)*60)
        self.mileage = round(meters/1000, 2)
        self.tss = round(sec/3600 * (self.ratio * 0.89) ** 2 / 100)

    def create_workout(self, workout_id=None, workout_owner_id=None):
        return {
            self._WORKOUT_ID_FIELD: workout_id,
            self._WORKOUT_OWNER_ID_FIELD: workout_owner_id,
            self._WORKOUT_NAME_FIELD: self.get_workout_name(),
            self._WORKOUT_DESCRIPTION_FIELD: self._generate_description(),
            "sportType": self.get_sport_type(self.sport_type[0]),
            "workoutSegments": [
                {
                    "segmentOrder": 1,
                    "sportType": self.get_sport_type(self.sport_type[0]),
                    "workoutSteps": self._steps(self.config["steps"])
                }
            ]
        }

    def get_workout_name(self):
        return self.config["name"]

    @staticmethod
    def extract_workout_id(running_workout):
        return running_workout[RunningWorkout._WORKOUT_ID_FIELD]

    @staticmethod
    def extract_workout_name(running_workout):
        return running_workout[RunningWorkout._WORKOUT_NAME_FIELD]

    @staticmethod
    def extract_workout_description(running_workout):
        return running_workout[RunningWorkout._WORKOUT_DESCRIPTION_FIELD]

    @staticmethod
    def extract_workout_owner_id(running_workout):
        return running_workout[RunningWorkout._WORKOUT_OWNER_ID_FIELD]

    @staticmethod
    def print_workout_json(running_workout):
        print(json.dumps(functional.filter_empty(running_workout)))

    @staticmethod
    def print_workout_summary(running_workout):
        workout_id = RunningWorkout.extract_workout_id(running_workout)
        workout_name = RunningWorkout.extract_workout_name(running_workout)
        workout_description = RunningWorkout.extract_workout_description(running_workout)
        print("{0} {1:20} {2}".format(workout_id, workout_name, workout_description))

    def get_sport_type(self, sport_type):
        return {
                "sportTypeId": SPORT_TYPES[sport_type],
                "sportTypeKey": sport_type,
            }

    def get_step_type(self, step_type):
        return {
                "stepTypeId": STEP_TYPES[step_type],
                "stepTypeKey": step_type,
            }

    def get_end_condition(self, end_condition):
        return {
                "conditionTypeId": END_CONDITIONS[end_condition],
                "conditionTypeKey": end_condition,
            }

    def get_target_type(self, target_type):
        return {
                "workoutTargetTypeId": TARGET_TYPES[target_type],
                "workoutTargetTypeKey": target_type,
            }

    def _get_step_description(self, step_config):
        step_description = step_config.get('description')
        if step_description:
            return step_description
        return None

    def _steps(self, steps_config):
        steps, step_order, child_step_id = self._steps_recursive(steps_config, 0, None)
        return steps

    def _steps_recursive(self, steps_config, step_order, child_step_id):
        if not steps_config:
            return [], step_order, child_step_id

        steps_config_agg = [(1, steps_config[0])]

        for step_config in steps_config[1:]:
            (repeats, prev_step_config) = steps_config_agg[-1]
            if prev_step_config == step_config:  # repeated step
                steps_config_agg[-1] = (repeats + 1, step_config)  # type: ignore
            else:
                steps_config_agg.append((1, step_config))

        steps = []
        for repeats, step_config in steps_config_agg:
            step_order = step_order + 1
            if isinstance(step_config, list):
                child_step_id = child_step_id + 1 if child_step_id else 1

                repeat_step_order = step_order
                repeat_child_step_id = child_step_id

                nested_steps, step_order, child_step_id = self._steps_recursive(step_config, step_order, child_step_id)
                steps.append(self._repeat_step(repeat_step_order, repeat_child_step_id, repeats, nested_steps))
            else:
                steps.append(self._interval_step(step_config, child_step_id, step_order))

        return steps, step_order, child_step_id

    def _repeat_step(self, step_order, child_step_id, repeats, nested_steps):
        return {
            "type": "RepeatGroupDTO",
            "stepOrder": step_order,
            "stepType": self.get_step_type("repeat"),
            "childStepId": child_step_id,
            "numberOfIterations": repeats,
            "workoutSteps": nested_steps,
            "smartRepeat": False
        }

    def _interval_step(self, step_config, child_step_id, step_order):
        return {
            "type": "ExecutableStepDTO",
            "stepId": None,
            "stepOrder": step_order,
            "stepType": self._get_step_type(step_config),
            "childStepId": child_step_id,
            "endCondition": self._end_condition(step_config),
            "endConditionValue": self._end_condition_value(step_config),
            "targetType": self._target_type(step_config),
            "targetValueOne": self._target_value_one(step_config),
            "targetValueTwo": self._target_value_two(step_config)
        }

    @staticmethod
    def _get_duration(step_config):
        duration = step_config.get("duration")
        return Duration(str(duration)) if duration else None

    def _get_step_type(self, step_config):
        step_type = step_config.get('type')
        return self.get_step_type(step_type.lower())

    def _str_is_time(self, string):
        if ':' in string:
            return True
        return False

    def _str_to_seconds(self, time_string):
        if self._str_is_time(time_string):
            return Duration(str(time_string)).to_seconds()
        else:
            return self.vVO2/float(time_string)

    def _str_to_minutes(self, time_string):
        return self._str_to_seconds(time_string) / 60.0

    def _str_is_distance(self, string):
        if 'm' in string.lower():
            return True
        return False

    def _str_to_meters(self, distance_string):
        if 'km' in distance_string.lower():
            return float(distance_string.lower().split('km')[0])*1000.0
        return float(distance_string.lower().split('m')[0])

    def _end_condition(self, step_config):
        duration = step_config.get("duration")
        if duration:
            if self._str_is_time(duration):
                return self.get_end_condition("time")
            if self._str_is_distance(duration):
                return self.get_end_condition("distance")
        return self.get_end_condition("lap.button")

    def _end_condition_value(self, step_config):
        duration = step_config.get("duration")
        if duration:
            if self._str_is_time(duration):
                return self._str_to_seconds(duration)
            if self._str_is_distance(duration):
                return self._str_to_meters(duration)
        return None

    def _get_target_value(self, target, key):
        target_type = self.target[target]['type']
        target_value = self.target[target][key]
        if target_type.lower() == 'pace':
            return 1000.0 / self._str_to_seconds(target_value)
        if target_type.lower() == 'heartrate':
            return round(self.fmin + float(target_value) * (self.fmax-self.fmin))

    def _target_type(self, step_config):
        target = step_config.get("target")
        if ">" in target:
            d, target = target.split(">")
        elif "<" in target:
            d, target = target.split("<")

        if not target:
            return self.get_target_type("no.target")
        if target not in self.target:
            return self.get_target_type("no.target")
        if 'zone' in target.lower():
            return self.get_target_type("heart.rate.zone")
        return self.get_target_type("pace.zone")

    def _target_value_one(self, step_config):
        target = step_config.get("target")
        if not target:
            return None
        if target not in self.target:
            if ">" in target:
                d, target = target.split(">")
                return 1000.0/(1000.0/self._get_target_value(target, key='min') - float(d))  # type: ignore
            elif "<" in target:
                d, target = target.split("<")
                return 1000.0/(1000.0/self._get_target_value(target, key='min') + float(d))  # type: ignore
            else:
                return None
        return self._get_target_value(target, key='min')

    def _target_value_two(self, step_config):
        target = step_config.get("target")
        if not target:
            return None
        if target not in self.target:
            if ">" in target:
                d, target = target.split(">")
                return 1000.0/(1000.0/self._get_target_value(target, key='max') - float(d))  # type: ignore
            elif "<" in target:
                d, target = target.split("<")
                return 1000.0/(1000.0/self._get_target_value(target, key='max') + float(d))  # type: ignore
            else:
                return None
        return self._get_target_value(target, key='max')

    def _generate_description(self):
        description = (self.config.get('description')
                       + '. Plan: ' + self.plan
                       + '. Estimated Duration: ' + str(self.duration) + '; '
                       + str(self.mileage).format('2:2f') + ' km. '
                       + str(round(self.ratio, 2)).format('2:2f') + '% vVO2. rTSS: '
                       + str(self.tss).format('2:2f'))  # type: ignore

        if description:
            return description
        return ''
