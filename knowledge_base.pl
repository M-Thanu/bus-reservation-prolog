% BusReserve - A Bus seat reservation system

%Dynamic Facts

:- dynamic reserved/4.
:- dynamic blacklisted/1.
:- dynamic waiting_list/2.
:- dynamic blocked_seat/3.
:- dynamic booking_counter/1.
:- dynamic passenger_counter/1.
:- dynamic passenger_type/2.
:- dynamic preference/2.
:- dynamic passenger_name/2.

%  STATIC FACTS

booking_counter(100).
passenger_counter(4).

%bus(BusID, StartingPoint, Destination, Type).
bus(bus101, colombo, kandy,  luxury).
bus(bus102, colombo, galle,  semi_luxury).

%seat(Bus, SeatID, Position, SeatType).
seat(bus101, s1, front,  window).
seat(bus101, s2, front,  aisle).
seat(bus101, s3, middle, window).
seat(bus101, s4, middle, aisle).
seat(bus101, s5, back,   window).

seat(bus102, s1, front,  window).
seat(bus102, s2, front,  aisle).
seat(bus102, s3, middle, window).
seat(bus102, s4, middle, aisle).
seat(bus102, s5, back,   window).

% Seed passengers 
:- assertz(passenger_name(p001, 'Nimal Silva')).
:- assertz(passenger_type(p001, elderly)).
:- assertz(preference(p001, window)).

:- assertz(passenger_name(p002, 'Kamal Perera')).
:- assertz(passenger_type(p002, student)).
:- assertz(preference(p002, window)).

:- assertz(passenger_name(p003, 'Saman Fernando')).
:- assertz(passenger_type(p003, family)).
:- assertz(preference(p003, aisle)).

:- assertz(passenger_name(p004, 'Dilani Jayawardena')).
:- assertz(passenger_type(p004, normal)).
:- assertz(preference(p004, aisle)).

%Seats s1, s2 are nearby
near(s1, s2).
near(s2, s3).
near(s3, s4).
near(s4, s5).

%  PASSENGER REGISTRATION

% ID Generation
next_passenger_id(ID) :-
    retract(passenger_counter(N)),
    N1 is N + 1,
    assertz(passenger_counter(N1)),
    ( N1 < 10
    -> atom_concat('p00', N1, ID)
    ;  N1 < 100
    -> atom_concat('p0',  N1, ID)
    ;  atom_concat('p',   N1, ID)
    ).

% Type Identification
age_to_type(Age, elderly) :- Age >= 60, !.
age_to_type(Age, child)   :- Age =< 12, !.
age_to_type(Age, student)  :- Age > 12, Age < 26, !.
age_to_type(_,   normal).

register_passenger(Name, Age, Pref, ID) :-
    next_passenger_id(ID),
    age_to_type(Age, Type),
    assertz(passenger_name(ID, Name)),
    assertz(passenger_type(ID, Type)),
    assertz(preference(ID, Pref)),
    format('  Registered ~w as ~w (type: ~w, pref: ~w)~n',
           [Name, ID, Type, Pref]).

%  BOOKING RULES

next_booking_id(ID) :-
    retract(booking_counter(N)),
    N1 is N + 1,
    assertz(booking_counter(N1)),
    atom_concat('B', N1, ID).

%available_seat(Bus, Seat) :-
 %   seat(Bus, Seat, _, _),
  %  \+ reserved(_, Bus, Seat, _),
   % \+ blocked_seat(Bus, Seat, _).

available_seat(Bus, Seat) :-
    seat(Bus, Seat, _, _),
    (
        reserved(_, Bus, Seat, _),
        !, fail
    ;
        true
    ),
    (
        blocked_seat(Bus, Seat, _),
        !, fail
    ;
        true
    ).

% can_book(BusID, SeatNo, PassengerID)
can_book(_, _, Passenger) :-
    blacklisted(Passenger),
    !,
    format('  [DENIED] ~w is blacklisted.~n', [Passenger]),
    fail.

can_book(Bus, Seat, _) :-
    available_seat(Bus, Seat),
    !.

can_book(Bus, Seat, _) :-
    format('  [DENIED] Seat ~w on ~w is not available.~n',
           [Seat, Bus]),
    fail.

%  SEAT RECOMMENDATION

suitable_seat(Passenger, Bus, Seat) :-
    passenger_type(Passenger, elderly),
    seat(Bus, Seat, front, _),
    available_seat(Bus, Seat).

suitable_seat(Passenger, Bus, Seat) :-
    passenger_type(Passenger, child),
    seat(Bus, Seat, front, _),
    available_seat(Bus, Seat).

suitable_seat(Passenger, Bus, Seat) :-
    preference(Passenger, window),
    seat(Bus, Seat, _, window),
    available_seat(Bus, Seat).

suitable_seat(Passenger, Bus, Seat) :-
    preference(Passenger, aisle),
    seat(Bus, Seat, _, aisle),
    available_seat(Bus, Seat).

family_seats(Bus, Seat1, Seat2) :-
    near(Seat1, Seat2),
    available_seat(Bus, Seat1),
    available_seat(Bus, Seat2).

recommend_seat(Passenger, Bus, Seat) :-
    suitable_seat(Passenger, Bus, Seat), !.
recommend_seat(_, Bus, Seat) :-
    available_seat(Bus, Seat), !.

%  BOOKING ACTIONS

book_seat(Bus, Seat, Passenger) :-
    ( can_book(Bus, Seat, Passenger)
    -> next_booking_id(ID),
       assertz(reserved(ID, Bus, Seat, Passenger)),
       format('  Booked! ID: ~w | ~w | Seat: ~w | Passenger: ~w~n',
              [ID, Bus, Seat, Passenger])
    ;  true
    ).

cancel_booking(BookingID) :-
    ( retract(reserved(BookingID, Bus, Seat, Passenger))
    -> format('  Cancelled ~w (~w seat ~w for ~w).~n',
              [BookingID, Bus, Seat, Passenger])
    ;  format('  No booking found: ~w~n', [BookingID])
    ).

change_seat(Bus, OldSeat, NewSeat, Passenger) :-
    ( reserved(ID, Bus, OldSeat, Passenger)
    -> cancel_booking(ID),
       book_seat(Bus, NewSeat, Passenger)
    ;  format('  No booking for ~w on seat ~w (~w).~n',
              [Passenger, OldSeat, Bus])
    ).

block_seat(Bus, Seat, Reason) :-
    assertz(blocked_seat(Bus, Seat, Reason)),
    format('  Seat ~w on ~w blocked: ~w~n', [Seat, Bus, Reason]).

unblock_seat(Bus, Seat) :-
    ( retract(blocked_seat(Bus, Seat, _))
    -> format('  Seat ~w on ~w unblocked.~n', [Seat, Bus])
    ;  format('  Seat ~w on ~w was not blocked.~n', [Seat, Bus])
    ).

handle_full_bus(Bus, Passenger) :-
    available_seat(Bus, _), !,
    format('  ~w still has seats available.~n', [Bus]).

handle_full_bus(Bus, Passenger) :-
    assertz(waiting_list(Bus, Passenger)),
    format('  ~w added to waiting list for ~w.~n', [Passenger, Bus]).

add_to_blacklist(Passenger) :-
    ( blacklisted(Passenger)
    -> format('  ~w is already blacklisted.~n', [Passenger])
    ;  assertz(blacklisted(Passenger)),
       format('  ~w blacklisted.~n', [Passenger])
    ).

%  REPORTS

show_all_bookings :-
    nl, write('  --- All Bookings ---'), nl,
    reserved(_, _, _, _), !,
    reserved(ID, Bus, Seat, Passenger),
    format('  ~w | ~w | Seat ~w | ~w~n', [ID, Bus, Seat, Passenger]),
    fail.

show_all_bookings :-
    write('  No bookings yet.'), nl.

show_available_seats(Bus) :-
    findall(Seat, available_seat(Bus, Seat), List),
    format('  Available on ~w: ~w~n', [Bus, List]).

booked_count(Bus, Count) :-
    findall(S, reserved(_, Bus, S, _), List),
    length(List, Count).

show_waiting_list(Bus) :-
    findall(P, waiting_list(Bus, P), List),
    ( List = []
    -> format('  No waiting list for ~w.~n', [Bus])
    ;  format('  Waiting list for ~w: ~w~n', [Bus, List])
    ).

%  INPUT HELPERS (CLI mode)

read_input(Prompt, Atom) :-
    write(Prompt),
    read_line_to_string(user_input, Str),
    atom_string(Atom, Str).

read_int(Prompt, N) :-
    repeat,
    write(Prompt),
    read_line_to_string(user_input, Str),
    ( number_string(N, Str) -> ! ; write('  Enter a number.'), nl, fail ).

%  CLI MENU (fallback if not using GUI)

start :-
    nl,
    write('  ================================'), nl,
    write('    BusReserve Expert System      '), nl,
    write('  ================================'), nl,
    menu_loop.

menu_loop :-
    repeat,
        nl,
        write('  1. Show available seats'), nl,
        write('  2. Book a seat'), nl,
        write('  3. Cancel a booking'), nl,
        write('  4. Show all bookings'), nl,
        write('  0. Exit'), nl,
        read_int('  Choice: ', C), nl,
        handle_menu(C),
        C =:= 0,
    !.

handle_menu(0) :- !, write('  Goodbye.'), nl.
handle_menu(1) :- !, read_input('  Bus ID: ', Bus), show_available_seats(Bus).
handle_menu(2) :- !,
    read_input('  Bus ID: ', Bus),
    read_input('  Seat ID: ', Seat),
    read_input('  Passenger ID: ', P),
    book_seat(Bus, Seat, P).
handle_menu(3) :- !, read_input('  Booking ID: ', ID), cancel_booking(ID).
handle_menu(4) :- !, show_all_bookings.
handle_menu(_) :- write('  Invalid choice.'), nl.