# Quantic Tic-Tac-Toe

## Description

The objective of this exercise is to build a Quantic Tic-Tac-Toe game (On a 3x3 board, human vs AI), playable using a
REST API.

## Game rules

(based on [this wikipedia article](https://en.wikipedia.org/wiki/Quantum_tic-tac-toe), feel free to use it)

The quantic tic-tac-toe is an alternative to the "classic" tic-tac-toe where players' moves are "superpositions" of
plays.

You have an example of game within the attached [Example Game.pdf](Example\ Game.pdf)

On the classic tic-tac-toe, at each turn, the player marks one cell with its symbol (`X` or `O`). In this variant, the
player will mark two cells as two options. Later on, we will determine which one of those options will come true. Those
options are marked with the symbol and a number matching the move number (two `X1` on the first move, then `O2`,
then `X3`, and so on). So when the first player (`X`) plays their first move, they put two marks `(X1, X1)`, which 
are called "entangled".

Example of a board after 1 play (just `X`)

```
|--------|--------|--------|
|   X1   |        |        |
|--------|--------|--------|
|        |   X1   |        |
|--------|--------|--------|
|        |        |        |
|--------|--------|--------|
```

Example of a board after 3 plays (`X` then `O` then `X` again)

```
|--------|--------|--------|
|   X1   |   O2   |        |
|--------|--------|--------|
|        |X1 O2 X3|        |
|--------|--------|--------|
|        |        |   X3   |    
|--------|--------|--------|
```

At some point we will have a "cyclic entanglement", for example, if `O` adds those `O4`:

```
|--------|--------|--------|
| X1 O4  | O2 O4  |        |
|--------|--------|--------|
|        |X1 O2 X3|        |
|--------|--------|--------|
|        |        |   X3   |    
|--------|--------|--------|
```

We now have a cycle: `X1` -> `O2` -> `O4` -> `X1`.

When we have this cycle, the positions can be reduced using the following rule :

- The next player chooses which of the two marks to keep ("collapse") and removes the second one
- The rest of the cycle is reduced

For example, if the player chose to collapse `X1` to the top left corner:

- We set `X1` to the top left cell, then we remove the other options for this cell (`O4`)
- The only remaining `O4` is on the top centered cell, so will take this place and remove all the other options (`O2`)
- The only remaining `O2` is on the centered cell, so will take this place and remove all the other options (`X1`
  and `X3`)
- The only remaining `X3` is on the bottom right cell, so will take this place and won't remove any options because
  there is none

The reduced board will be:

```
|--------|--------|--------|
|   X1   |   O4   |        |
|--------|--------|--------|
|        |   O2   |        |
|--------|--------|--------|
|        |        |   X3   |    
|--------|--------|--------|
```

The game then continue with `O` playing their move to put options.

The first player to achieve a tic-tac-toe (three in a row horizontally, vertically, or diagonally) consisting entirely
of classical marks is declared the winner.

## Expected Result & Requirements

As mentioned, the purpose of this exercise is to build an API to play the game as described above.
An initial code base has been provided.

A `DummyEngine` that does not check board consistency, does not handle collapse and
ends the game after a specific number of moves is available as an example. You can play with this `DummyEngine`
using `play.py` script with `USE_DUMMY = True` (assuming you run the API first).

`engine.case_engine.CaseEngine` is where you should implement a functioning version of the exercise.

Both `DummyEngine` and `CaseEngine` extends a `BaseEngine` class that includes the support of an AI opponent,
actually playing randomly. There is no need to improve the game.

Feel free to update / restructure any part of the code, especially regarding the additional constraint details below.

**Additional constraint : The API must stay stateless, but secured (in the way that the user can't cheat).**

The code must be pushed on this Github repository. A special consideration will be given to code
quality/robustness/efficiency.

You should not work more than half a day on this case. It's allowed to have a non fully complete result, the following
debrief being used to dig into what could have been done / improved. You're free to spend more time on this case if you
consider you wasted time on "non relevant" things (it happens ! :) - issue on setting up something etc..) 
