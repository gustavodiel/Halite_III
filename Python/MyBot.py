#!/usr/bin/env python3
# Python 3.6

import hlt

from hlt import constants
from hlt.positionals import Direction
from hlt.entity import Ship

import random
import logging


game = hlt.Game()
game.ready("DielBot")

logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

class Bot:
    def __init__(self):
        self.should_drop_dict = {}

    def run(self):
        while True:
            game.update_frame()

            self.game = game
            self.game_map = game.game_map
            self.me = game.me

            command_queue = []

            for ship in self.me.get_ships():

                if self.game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
                    command = self.process_ship(ship)
                    world_pos = ship.position.directional_offset(command)
                    self.game_map[world_pos].mark_unsafe(ship)

                    command_queue.append(ship.move(command))
                else:
                    command_queue.append(ship.stay_still())

            if game.turn_number <= 200 and self.me.halite_amount >= constants.SHIP_COST and not self.game_map[self.me.shipyard].is_occupied:
                command_queue.append(self.me.shipyard.spawn())

            game.end_turn(command_queue)

    def process_ship(self, ship):
        if ship.is_full or self.should_drop(ship):
            return self.process_full_ship(ship)

        return self.process_normal_ship(ship)

    def process_normal_ship(self, ship):
        # {(direction) -> (amount of halite)}
        halites_on_dir = {}

        for direction in direction_order:
            world_pos = ship.position.directional_offset(direction)
            amount = self.game_map[world_pos].halite_amount
            if direction is Direction.Still or self.is_pos_valid(world_pos):
                halites_on_dir[direction] = amount

        ship_command = max(halites_on_dir, key=halites_on_dir.get)

        # if self.is_not_worth(ship_command, ship):
        #     return self.random_safe(ship)

        return ship_command

    def random_safe(self, ship):
        for direction in direction_order:
            world_pos = ship.position.directional_offset(direction)
            if self.is_pos_valid(world_pos):
                return direction

        return Direction.Still

    def process_full_ship(self, ship):
        self.set_should_drop(ship.id, True)

        if self.game_map.calculate_distance(ship.position, self.me.shipyard.position) == 0:
            self.set_should_drop(ship.id, False)
            return self.process_normal_ship(ship)

        return self.game_map.naive_navigate(ship, self.me.shipyard.position)

    def is_pos_valid(self, position):
        cell = self.game_map[position]

        empty = cell.is_empty

        return empty

    # TODO: use ship instead of id
    def set_should_drop(self, id, status):
        ship_id = id
        if isinstance(id, Ship):
            ship_id = id.id

        self.should_drop_dict[ship_id] = status

    # TODO: use ship instead of id
    def should_drop(self, id):
        ship_id = id
        if isinstance(id, Ship):
            ship_id = id.id

        if not self.should_drop_dict.__contains__(ship_id):
            return False

        return self.should_drop_dict[ship_id]

    def is_not_worth(self, command, ship):
        world_pos = ship.position.directional_offset(command)
        amount = self.game_map[world_pos].halite_amount
        return amount < constants.MAX_HALITE / 10


my_bot = Bot()
my_bot.run()
