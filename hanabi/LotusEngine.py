from swiplserver import PrologMQI
import GameData

class LotusEngine:

    def __init__(self, owner: str = None):
        self.owner = owner
        self.prolog = PrologMQI()
        with self.prolog.create_thread() as prolog_thread:
            with open("knowledge_base_core.txt") as file:
                for line in file:
                    if line[0] == '#':
                        continue
                    prolog_thread.query(f"assert({line}).")

    def first_set(self, data):
        with self.prolog.create_thread() as prolog_thread:
            for i in data.players:
                prolog_thread.query(f"assert(player({i.name})).")
                for j in range(5):
                    prolog_thread.query(f"assert(player_hand({i.name}, {j}, card({j.val}))).")

    def prolog_query(self, query: str):
        with self.prolog.create_thread() as prolog_thread:
            result = prolog_thread.query(query)
        return result
