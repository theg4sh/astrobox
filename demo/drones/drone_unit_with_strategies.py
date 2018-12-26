#!/usr/bin/env python
# -*- coding: utf-8 -*-

from astrobox.units import DroneUnit, Unit

class DroneUnitWithStrategies(DroneUnit):
    def __init__(self, **kwargs):
        super(DroneUnitWithStrategies, self).__init__(**kwargs)
        self.__strategies = []

    @property
    def current_strategy(self):
        return self.__strategies[0] if not self.is_strategy_finished() else None

    def append_strategy(self, strategy):
        if strategy.is_group_unique:
            for s in self.__strategies:
                if s.group == strategy.group:
                    self.__strategies.remove(s)
        self.__strategies.append( strategy )

    def clear_strategies(self):
        self.__strategies = []

    def is_strategy_finished(self):
        return len(self.__strategies) == 0

    def game_step(self):
        self.native_game_step()
        for s in self.__strategies:
            if s.is_finished:
                self.__strategies.remove(s)
                continue
            s.game_step()
            break;

    # @brief elerium_stocks возвращает все объекты мира из которых можно добывать ресурсы
    @property
    def elerium_stocks(self):
        return [es for es in self.scene.get_objects_by_type(Unit) if hasattr(es, 'cargo') and not es.is_alive]
    
    # Позволяет обращаться к чистому обработчику из стратегий
    def native_game_step(self):
        super(DroneUnitWithStrategies, self).game_step()

