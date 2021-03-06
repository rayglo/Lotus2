:- dynamic bluetoken/1.
:- dynamic redtoken/1.
:- dynamic deck/2.
:- dynamic tablefirework/2.
:- dynamic discardpile/2.
:- dynamic playerhand/3.
:- dynamic playerknows/3.
:- dynamic player/1.
:- dynamic playerturn/2.

% initial items
bluetoken(8).
redtoken(0).

% cards_in_deck (card(number,color), quantity)
deck(card(1,yellow),3).
deck(card(1,red),3).
deck(card(1,green),3).
deck(card(1,white),3).
deck(card(1,blue),3).
deck(card(2,yellow),2).
deck(card(2,red),2).
deck(card(2,green),2).
deck(card(2,white),2).
deck(card(2,blue),2).
deck(card(3,yellow),2).
deck(card(3,red),2).
deck(card(3,green),2).
deck(card(3,white),2).
deck(card(3,blue),2).
deck(card(4,yellow),2).
deck(card(4,red),2).
deck(card(4,green),2).
deck(card(4,white),2).
deck(card(4,blue),2).
deck(card(5,yellow),1).
deck(card(5,red),1).
deck(card(5,green),1).
deck(card(5,white),1).
deck(card(5,blue),1).

% table info (color, number)
tablefirework(0,yellow).
tablefirework(0,red).
tablefirework(0,green).
tablefirework(0,white).
tablefirework(0,blue).

% discard pile (card(number,color),quantity)
discardpile(card(1,yellow),0).
discardpile(card(1,red),0).
discardpile(card(1,green),0).
discardpile(card(1,white),0).
discardpile(card(1,blue),0).
discardpile(card(2,yellow),0).
discardpile(card(2,red),0).
discardpile(card(2,green),0).
discardpile(card(2,white),0).
discardpile(card(2,blue),0).
discardpile(card(3,yellow),0).
discardpile(card(3,red),0).
discardpile(card(3,green),0).
discardpile(card(3,white),0).
discardpile(card(3,blue),0).
discardpile(card(4,yellow),0).
discardpile(card(4,red),0).
discardpile(card(4,green),0).
discardpile(card(4,white),0).
discardpile(card(4,blue),0).
discardpile(card(5,yellow),0).
discardpile(card(5,red),0).
discardpile(card(5,green),0).
discardpile(card(5,white),0).
discardpile(card(5,blue),0).

% card state rules
playable(card(X,Y)) :-
    X=\=0,
    Y\=unknown,
    tablefirework(Z,Y),
    Z=:=X-1.

useful_ric_f(C,[X|T]) :-
    (
        (deck(card(X,C),Q),Q>0);
        playerhand(_,_,card(X,C))
    ),
    length(T,N),
    (
        N=:=0;
        useful_ric_f(C,T)
    ).

useful(card(X,Y)) :-
    X=\=0,Y\=unknown,
    tablefirework(Z,Y),
    S is Z+1,
    D is X-1,
    S<X,
    numlist(S,D,L),
    useful_ric_f(Y,L).

useful(card(X,Y)) :-
    playable(card(X,Y)).