#!/usr/bin/env python3
# Python 3.6

import hlt

from hlt import constants
from hlt.positionals import Direction, Position
from hlt.entity import Ship

import random
import math
import logging


game = hlt.Game()
game.ready("DielBot")

logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

class Bot:
    def __init__(self):
        self.should_drop_dict = {}
        self.ship_target_dict = []
        self.ship_vision = 5
        self.game = None
        self.game_map = None
        self.me = None
        self.block_convert_to_dropzone = False

    def run(self):
        while True:
            game.update_frame()

            self.game = game
            self.game_map = game.game_map
            self.me = game.me



            self.block_convert_to_dropzone = False

            command_queue = []

            for ship in self.me.get_ships():

                if self.game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
                    command = self.process_ship(ship)
                    if isinstance(command, str):
                        command_queue.append(command)

                    else:
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

        if self.should_become_dropzone(ship) and self.me.halite_amount >= constants.DROPOFF_COST * 1.5:
            self.block_convert_to_dropzone = True
            return self.convert_ship_to_dropzone(ship)

        return self.process_normal_ship(ship)

    def process_normal_ship_v1(self, ship):

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

    def process_normal_ship(self, ship):

        # {(direction) -> (amount of halite)}
        halites_on_pos = {}

        for i in range(-self.ship_vision, self.ship_vision):
            for j in range(-self.ship_vision, self.ship_vision):
                target_local = Position(i, j)
                pos_on_map = self.game_map.normalize(ship.position + target_local)
                amount = self.game_map[pos_on_map].halite_amount
                if pos_on_map == ship.position or (self.is_pos_valid(pos_on_map) and not (i, j) in self.ship_target_dict):
                    halites_on_pos[(i, j)] = amount

        target = max(halites_on_pos, key=halites_on_pos.get)
        target_pos = self.game_map.normalize(ship.position + Position(target[0], target[1]))

        self.ship_target_dict.append(target)

        # if self.is_not_worth(ship_command, ship):
        #     return self.random_safe(ship)

        return self.game_map.naive_navigate(ship, target_pos)

    def should_become_dropzone(self, ship):
        if self.block_convert_to_dropzone:
            return False

        nearest_dropzone = self.get_nearest_dropzone(ship)
        distance = self.game_map.calculate_distance(ship.position, nearest_dropzone.position)

        return distance > self.game_map.width * 0.4 or distance > self.game_map.height * 0.4

    def convert_ship_to_dropzone(self, ship):
        return ship.make_dropoff()

    def random_safe(self, ship):
        for direction in direction_order:
            world_pos = ship.position.directional_offset(direction)
            if self.is_pos_valid(world_pos):
                return direction

        return Direction.Still

    def process_full_ship(self, ship):
        self.set_should_drop(ship.id, True)

        dropzone = self.get_nearest_dropzone(ship)

        if self.game_map.calculate_distance(ship.position, dropzone.position) == 0:
            self.set_should_drop(ship.id, False)
            return self.process_normal_ship(ship)

        return self.game_map.naive_navigate(ship, dropzone.position)

    def get_nearest_dropzone(self, ship):
        entities = [self.me.shipyard] + self.me.get_dropoffs()
        nearest = None
        nearest_dist = math.inf

        for entity in entities:
            distance = self.game_map.calculate_distance(ship.position, entity.position)
            if distance < nearest_dist:
                nearest = entity
                nearest_dist = distance

        return nearest

    def is_pos_valid(self, position):
        cell = self.game_map[position]

        empty = cell.is_empty

        return empty

    def set_should_drop(self, id, status):
        ship_id = id
        if isinstance(id, Ship):
            ship_id = id.id

        self.should_drop_dict[ship_id] = status

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
