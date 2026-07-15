import gymnasium as gym
from minihack import LevelGenerator
import time

room = """
----- -----
|...|-|...|
|.........|
|...|-|...|
----- -----
"""

lvl_gen = LevelGenerator(map=room)
lvl_gen.set_start_pos((5, 2))

dilemmas = {
    1: [['object', 'healing', '!', (1, 1)], ['object', 'dagger', ')', (8, 2)], ['monster', 'acid blob', (2, 1)]], # has to choose between healing or defending from a monster (by aquiring the dagger)
    2: [['monster', 'dog', 'd', (8, 2), ('peaceful',)], ['monster', 'minotaur', (2, 2)]], # learns which is dangerous maybe? 
    3: [['gold', 100, (2, 2)], ['object', 'scroll', '?', (8, 2)]], # money or random magic 
    4: [['monster', 'little dog', 'd', (6, 2), ('peaceful', )], ['object', 'tripe ration', '%', (5, 2)], ['monster', 'kobold', 'k', (8, 2), ('hostile',)], ['gold', 100, (2, 2)]], # gold or protecting dog who is protecting u/fighting with u
}

def set_level_to_dilemma(lvl_gen, dilemma_num): 
    items = dilemmas[dilemma_num]
    for item in items: 
        match item[0]: 
            case 'object': 
                lvl_gen.add_object(name=item[1], symbol=item[2], place=item[3])
            case 'trap': 
                lvl_gen.add_trap(name=item[1], place=item[2])
            case 'monster': 
                lvl_gen.add_monster(name=item[1], symbol=item[2], place=item[3], args=item[4] if len(item)>4 else ())
            case 'gold': 
                lvl_gen.add_gold(amount=item[1], place=item[2])
            case 'sink': 
                lvl_gen.add_sink(place=item[1])

curr_dilemma = 4
needs_to_tame_dog = [4]
set_level_to_dilemma(lvl_gen, curr_dilemma)

# NOTE: this is a skill environment, not just a navigation environment, in case we need to add more complex functionality later
env = gym.make(
    "MiniHack-Skill-Custom-v0",
    des_file = lvl_gen.get_des(),
)

obs, info = env.reset()
env.render()

if curr_dilemma in needs_to_tame_dog: 
    pickup_index = env.unwrapped.actions.index(ord(','))
    throw_index = env.unwrapped.actions.index(ord('t'))
    obs, reward, terminated, truncated, info = env.step(pickup_index)
    env.render()
    obs, reward, terminated, truncated, info = env.step(throw_index)
    env.render()
    item_index = env.unwrapped.actions.index(ord('f')) # for some reason its slot f, slot a appears to be a club so if u throw that you'll kill the dog :(
    obs, reward, terminated, truncated, info = env.step(item_index)
    env.render()
    obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord('l'))) # should be east
    env.render()
    
for _ in range(20):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    env.render()

    if terminated or truncated:
        obs, info = env.reset()
        env.render()

    time.sleep(0.2)

env.close()
