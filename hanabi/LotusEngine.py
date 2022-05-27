from swiplserver import PrologMQI, PrologThread
import logging
import GameData


class LotusEngine:

    def __init__(self, owner: str = None):
        logging.basicConfig(filename=owner + "_log.txt", filemode="w", level=logging.INFO,
                            format='[%(levelname)s][%(asctime)s]  %(message)s')
        logging.info("Game Simulation Starting")
        logging.info(f"Setting lotus for player {owner.lower()}")
        self.owner = owner
        self.prolog = PrologMQI()
        with self.prolog.create_thread() as prolog_thread:
            with open("knowledge_base_core.txt") as file:
                logging.info("Inserting knowledge base core")
                for line in file:
                    if line[0] == '#':
                        continue
                    prolog_thread.query(f"assertz({line}).")
                for i in range(5):
                    prolog_thread.query(f"assertz(playerhand({self.owner.lower()},{i},card(0,unknown))).")

    def client_first_set(self, data: GameData.ServerGameStateData):
        """
        For the initial setup of the KB

        :param data: A GameData.ServerGameStateData object passed from the client
        """
        with self.prolog.create_thread() as prolog_thread:
            turn = 0
            for i in data.players:
                self.prolog_query(prolog_thread, f"assertz(player({i.name.lower()})).")
                self.prolog_query(prolog_thread, f"assertz(playerturn({i.name.lower()},{turn})).")
                turn = turn + 1

        for i in data.players:
            if i.name == self.owner:  # Skip if player is owner, since we don't know our hand
                continue
            for j in range(5):  # cycle over player's hand
                self.player_draws_card(i.name.lower(), j, i.hand[j].value, i.hand[j].color)

        with self.prolog.create_thread() as prolog_thread:
            for i in data.players:
                for j in range(5):
                    self.prolog_query(prolog_thread, f"assertz(playerknows({i.name.lower()},{j},card(0,unknown))).")

    def client_card_discard(self, dataAV: GameData.ServerActionValid, dataGSD: GameData.ServerGameStateData):
        """
        To be used when a player discards a card. What it does is:

        - Removes the card from the players hand
        - Adds the card from the discard pile
        - Adds a blue token
        - If lotus owner didn't know about the properties of the card, removes it from the deck too
        - Draws the next card for the player who discarded

        :param dataAV: A GameData.ServerActionValid object passed from the client
        :param dataGSD A GameData.ServerGameStateData object passed from the client after the card has been discarded
        """
        card_unknown = False
        with self.prolog.create_thread() as prolog_thread:
            if self.owner == dataAV.lastPlayer: #Checks if owner knew about the card he discarded
                result = list(self.prolog_query(prolog_thread, f"playerhand({dataAV.lastPlayer.lower()},{dataAV.cardHandIndex},card(X,Y))."))[0]
                value = result['X']
                color = result['Y']
                if value == 0 or color == 'unknown':
                    card_unknown = True
            self.prolog_query(prolog_thread, f"retract(playerhand({dataAV.lastPlayer.lower()},{dataAV.cardHandIndex},_)).")
            if dataAV.cardHandIndex<4:
                for i in range(dataAV.cardHandIndex+1, 5):
                    result = list(self.prolog_query(prolog_thread, f"playerhand({dataAV.lastPlayer.lower()},{i},card(X,Y))."))[0]
                    value_next = result['X']
                    color_next = result['Y']
                    self.prolog_query(prolog_thread, f"retract(playerhand({dataAV.lastPlayer.lower()},{i},_)).")
                    self.prolog_query(prolog_thread, f"assert(playerhand({dataAV.lastPlayer.lower()},{i-1},card({value_next},{color_next}))).")
            blue_tokens = list(self.prolog_query(prolog_thread,f"bluetoken(X)."))[0]['X']
            self.prolog_query(prolog_thread, "retract(bluetoken(_)).")
            self.prolog_query(prolog_thread, f"assertz(bluetoken({blue_tokens + 1})).")
        self.add_card_to_discard(dataAV.card.value, dataAV.card.color) # Add card to discard pile
        if card_unknown:
            self.remove_card_from_deck(dataAV.card.value, dataAV.card.color)

        if self.owner == dataAV.lastPlayer:
            self.player_draws_card(self.owner.lower(), 4, 0, 'unknown')
        else:
            for p in dataGSD.players:
                if p.name != dataAV.lastPlayer:
                    continue
                self.player_draws_card(dataAV.lastPlayer.lower(), 4, p.hand[4].value, p.hand[4].color)
                break

    def remove_card_from_deck(self, value: int, color: str):
        """
        To be used to remove a card from the deck. Updates the KB, reducing the quantity of that card of 1.

        :param value: the value of the card
        :param color: the color of the card
        """
        with self.prolog.create_thread() as prolog_thread:
            quantity_in_deck = list(self.prolog_query(prolog_thread,f"deck(card({value},{color}),X)."))[0]['X']  # Store quantity of card in deck
            self.prolog_query(prolog_thread, f"retract(deck(card({value},{color}),{quantity_in_deck})).")
            self.prolog_query(prolog_thread, f"assertz(deck(card({value},{color}),{quantity_in_deck - 1})).")

    def add_card_to_discard(self, value: int, color: str):
        """
        To be used to add a card to the discard pile. Updates the KB, increasing the quantity of that card of 1.

        :param value: the value of the card
        :param color: the color of the card
        :return:
        """
        with self.prolog.create_thread() as prolog_thread:
            quantity_in_discard = list(self.prolog_query(prolog_thread, f"discardpile(card({value},{color}),X)."))[0]['X']  # Store quantity of card in deck
            self.prolog_query(prolog_thread, f"retract(discardpile(card({value},{color}),{quantity_in_discard})).")
            self.prolog_query(prolog_thread, f"assertz(discardpile(card({value},{color}),{quantity_in_discard + 1})).")

    def player_draws_card(self, player: str, index: int, value: int, color: str):
        """
        To be used when a player draws a card from the deck. What it does is:

        - Removes a card from the deck if its value and color are known
        - Removes the card from the hand of the player at index, if he had one
        - Gives the player a card of value and color at the chosen index.

        :param player: the name of the player
        :param index: the index of the hand
        :param value: the value of the card
        :param color: the color of the card
        """
        if color != 'unknown' and value != 0:
            self.remove_card_from_deck(value, color)
        with self.prolog.create_thread() as prolog_thread:
            result = self.prolog_query(prolog_thread,f"playerhand({player},{index},_).")
            if result:
                self.prolog_query(prolog_thread,f"retract(playerhand({player},{index},_)).")
            self.prolog_query(prolog_thread,f"assertz(playerhand({player},{index},card({value},{color}))).")

    def client_place_firework(self, dataPMO: GameData.ServerPlayerMoveOk, dataGSD: GameData.ServerGameStateData):
        """
                To be used when a player places a card on the table. What it does is:

                - Removes the card from the player's hand
                - Adds the card from the corresponding pile
                - If lotus owner didn't know about the properties of the card, removes it from the deck too
                - Draws the next card for the player who discarded

                :param dataAV: A GameData.ServerActionValid object passed from the client
                :param dataGSD A GameData.ServerGameStateData object passed from the client after the card has been discarded
                """
        card_unknown = False
        with self.prolog.create_thread() as prolog_thread:
            if self.owner == dataPMO.lastPlayer:  # Checks if owner knew about the card he placed
                result = list(self.prolog_query(prolog_thread, f"playerhand({dataPMO.lastPlayer.lower()},{dataPMO.cardHandIndex},card(X,Y))."))[0]
                value = result['X']
                color = result['Y']
                if value == 0 or color == 'unknown':
                    card_unknown = True
            self.prolog_query(prolog_thread, f"retract(playerhand({dataPMO.lastPlayer.lower()},{dataPMO.cardHandIndex},_)).")
            if dataPMO.cardHandIndex < 4:
                for i in range(dataPMO.cardHandIndex + 1, 5):
                    result = list(self.prolog_query(prolog_thread,f"playerhand({dataPMO.lastPlayer.lower()},{i},card(X,Y))."))[0]
                    value_next = result['X']
                    color_next = result['Y']
                    self.prolog_query(prolog_thread, f"retract(playerhand({dataPMO.lastPlayer.lower()},{i},_)).")
                    self.prolog_query(prolog_thread, f"assert(playerhand({dataPMO.lastPlayer.lower()},{i - 1},card({value_next},{color_next}))).")
                self.prolog_query(prolog_thread, f"retract(tablefirework(_,{dataPMO.card.color})).")
                self.prolog_query(prolog_thread, f"assertz(tablefirework({dataPMO.card.value},{dataPMO.card.color})).")
        if card_unknown:
            self.remove_card_from_deck(dataPMO.card.value, dataPMO.card.color)

        if self.owner == dataPMO.lastPlayer:
            self.player_draws_card(self.owner.lower(), 4, 0, 'unknown')
        else:
            for p in dataGSD.players:
                if p.name != dataPMO.lastPlayer:
                    continue
                self.player_draws_card(dataPMO.lastPlayer.lower(), 4, p.hand[4].value, p.hand[4].color)
                break

    def client_thunder_strike(self, dataPTS: GameData.ServerPlayerThunderStrike, dataGSD: GameData.ServerGameStateData):
        """
        To be used when a player plays the wrong card. What it does is:

        - Removes the card from the player's hand
        - If lotus owner didn't know about the properties of the card, removes it from the deck too
        - Adds the card to the discard pile
        - Draws a new card for the player
        - Increases red tokens by 1

        :param dataPTS: A GameData.ServerPlayerThunderStrike object passed from the client
        :param dataGSD: A GameData.ServerGameStateData object passed from the client
        """
        card_unknown = False
        with self.prolog.create_thread() as prolog_thread:
            if self.owner == dataPTS.lastPlayer:  # Checks if owner knew about the card he discarded
                result = list(self.prolog_query(prolog_thread,f"playerhand({dataPTS.lastPlayer.lower()},{dataPTS.cardHandIndex},card(X,Y))."))[0]
                value = result['X']
                color = result['Y']
                if value == 0 or color == 'unknown':
                    card_unknown = True
            self.prolog_query(prolog_thread, f"retract(playerhand({dataPTS.lastPlayer.lower()},{dataPTS.cardHandIndex},_)).")
            if dataPTS.cardHandIndex < 4:
                for i in range(dataPTS.cardHandIndex + 1, 5):
                    self.prolog_query(prolog_thread,f"playerhand({dataPTS.lastPlayer.lower()},{i},card(X,Y)).")
                    result = list(self.prolog_query(prolog_thread,f"playerhand({dataPTS.lastPlayer.lower()},{i},card(X,Y))."))[0]
                    value_next = result['X']
                    color_next = result['Y']
                    self.prolog_query(prolog_thread,f"retract(playerhand({dataPTS.lastPlayer.lower()},{i},_)).")
                    self.prolog_query(prolog_thread.query,f"assert(playerhand({dataPTS.lastPlayer.lower()},{i - 1},card({value_next},{color_next}))).")
            red_tokens = list(self.prolog_query(prolog_thread,"redtoken(X)."))[0]['X']
            self.prolog_query(prolog_thread, "retract(redtoken(_)).")
            self.prolog_query(prolog_thread, f"assertz(redtoken({red_tokens + 1})).")
        self.add_card_to_discard(dataPTS.card.value, dataPTS.card.color)  # Add card to discard pile
        if card_unknown:
            self.remove_card_from_deck(dataPTS.card.value, dataPTS.card.color)

        if self.owner == dataPTS.lastPlayer:
            self.player_draws_card(self.owner.lower(), 4, 0, 'unknown')
        else:
            for p in dataGSD.players:
                if p.name != dataPTS.lastPlayer:
                    continue
                self.player_draws_card(dataPTS.lastPlayer.lower(), 4, p.hand[4].value, p.hand[4].color)
                break


    def client_hint_received(self, dataHD: GameData.ServerHintData):
        with self.prolog.create_thread() as prolog_thread:
            blue_tokens = list(self.prolog_query(prolog_thread, "bluetoken(X)."))[0]['X']
            self.prolog_query(prolog_thread, "retract(bluetoken(_)).")
            self.prolog_query(prolog_thread, f"assertz(bluetoken({blue_tokens - 1})).")
            self.add_player_knowledge(dataHD.destination, dataHD.positions, dataHD.type, dataHD.value)

    def add_player_knowledge(self, player: str, positions: list, type: str, value: int):
        """
        To be used when a player gains direct knowledge about one of his cards. Adds a playerknows fact if the
        player isn't the owner, else it'll add a playerhand fact

        :param player: the player who gains the knowledge
        :param positions: an array of int of the positions he gains knowledge about
        :param type: the type of knowledge. It can be "value" or "color"
        :param value: the information. If type=="color", it'll contain a color, else it'll contain a number.
        """
        with self.prolog.create_thread() as prolog_thread:
            if player == self.owner:
                fact = "playerhand"
            else:
                fact = "playerknows"
            for i in positions:
                result = list(self.prolog_query(prolog_thread, f"{fact}({player.lower()},{i},card(X,Y))."))[0]
                self.prolog_query(prolog_thread, f"retract({fact}({player.lower()},{i},_)).")
                if type == "color":
                    prev_value = result['X']
                    self.prolog_query(prolog_thread,
                                      f"assertz({fact}({player.lower()},{i},card({prev_value},{value}))).")
                else:
                    prev_value = result['Y']
                    self.prolog_query(prolog_thread,
                                      f"assertz({fact}({player.lower()},{i},card({value},{prev_value}))).")

    def prolog_query(self, thread: PrologThread, query: str):
        logging.info("Executing " + query)
        return thread.query(query)

    def client_prolog_query(self, query: str):
        """
        Answers a prolog query to the LotusEngine KB.

        :param query: The prolog query
        :return: A string with the result of the query
        """
        with self.prolog.create_thread() as prolog_thread:
            result = prolog_thread.query(query)
        return result
