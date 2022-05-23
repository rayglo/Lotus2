from swiplserver import PrologMQI

prolog = PrologMQI()
with prolog.create_thread() as prolog_thread:
    with open("knowledge_base_core.txt") as file:
        for line in file:
            if line[0] == '#':
                continue
            prolog_thread.query(f"assert({line}).")

with prolog.create_thread() as prolog_thread:
    print(prolog_thread.query("blue_token(X)."))
    print(prolog_thread.query("deck(card(Number,yellow,Quantity))."))