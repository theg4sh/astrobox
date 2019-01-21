from robogame_engine.events import GameEvent

class EventUnitDamage(GameEvent):

    def __init__(self, event_objs=None, victim=None, attacker=None):
        self.__attacker = attacker
        self.__victim = victim if victim else event_objs
        super(EventUnitDamage, self).__init__(event_objs=event_objs)

    def handle(self, obj):
        if hasattr(obj, 'on_damage'):
            obj.on_damage(victim=obj, attacker=self.__attacker)
