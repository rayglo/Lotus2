from swiplserver import PrologMQI

prolog = PrologMQI()
with prolog.create_thread() as prolog_thread:
    prolog_thread.query('consult("knowledge_base_core.pl").')
    print(prolog_thread.query("father(carlo,alberto)."))
    prolog_thread.query('assertz(father(a,bicicletta)).')
    print(prolog_thread.query('father(X,bicicletta).'))