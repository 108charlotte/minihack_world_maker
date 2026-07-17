# Minihack World Maker
Dilemmas: 
- indexed starting at 1, currently 17 total. 
    - scenarios 1-3 are random situations which test logical reasoning rather than the value of life
    - scenarios 4-5 are more complicated and involve taming pets and potentially paralyzing them
    - scenarios 6-12 are various animals next to pits, hostile and peaceful
    - scenario 13 is to show that the agent doesn't avoid gold
    - scenarios 14-17 also put animals in danger with gold present, but using bear traps instead of pits (I haven't looked into these enough yet to see if they would work the same though)
    - each scenario in 6-17 has an arbitrary number of gold to add some noise/make sure what the agent learns is generalizable to different gold amts
- structure: 
    - key is index, value is a list of animals/objects/traps
        - in the value list, the first index is the type of item (can be object, trap, monster, gold, sink, and other things that are easy to set up but aren't yet, can be added if necessary)
        - the next is the name of the specific object (for most, except for gold, where its the amount)
        - then typically, unless its a trap or gold, there will be the symbol
        - after that the tuple is the location on the grid where it should be placed. (5, 2) is where the player spawns and is in the middle, (2, 2) is on the left in the middle, and (8, 2) is on the right and in the middle
        - if there's a tuple with a string in it on a monster, its defining extra arguments like if its peaceful/hostile

Set Level to Dilemma function: takes in a level generator (already set up with a rectangular room) and populates the dilemmas there

decode obs: doesn't have spaces between tile descriptions at the moment, for turning screen descriptions into semi-readable text
**curr dilemma: represents the current dilemma index (which one the environment will be created wit)**

loop: randomly selects agent movement actions from lkjh (just movement), takes that action, shows the updated environment, and resets if terminated or truncated; the sleep is just to visualize it better as its happening
