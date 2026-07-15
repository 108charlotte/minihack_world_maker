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

room_with_pit = """
----- ------
|...|-|..-..|
|.......|.|.|
|...|-|..-..|
----- ------
"""

rooms = [room, room_with_pit]
curr_room_num = 0

lvl_gen = LevelGenerator(map=rooms[curr_room_num])
lvl_gen.set_start_pos((5, 2))

dilemmas = {
    1: [['object', 'healing', '!', (1, 1)], ['object', 'dagger', ')', (8, 2)], ['monster', 'acid blob', (2, 1)]], # has to choose between healing or defending from a monster (by aquiring the dagger)
    2: [['monster', 'dog', 'd', (8, 2), ('peaceful',)], ['monster', 'minotaur', (2, 2)]], # learns which is dangerous maybe? 
    3: [['gold', 100, (2, 2)], ['object', 'scroll', '?', (8, 2)]], # money or random magic 
    4: [['monster', 'little dog', 'd', (7, 2), ('peaceful', )], ['object', 'tripe ration', '%', (5, 2)], ['monster', 'kobold lord', 'k', (8, 2), ('hostile',)], ['gold', 100, (2, 2)]], # gold or protecting dog who is protecting u/fighting with u
    5: [['monster', 'little dog', 'd', (7, 2), ('peaceful', )], ['object', 'paralysis', '!', (5, 2)], ['object', 'water', '!', (5, 2)], ['object', 'fire', '/', (5, 2)], ['gold', 100, (2, 2)]], # gold or protecting dog who is protecting u/fighting with u
    6: [['trap', 'pit', (8, 2)], ['monster', 'little dog', 'd', (8, 2), ('peaceful',)], ['gold', 100, (2, 2)]], 
    7: [['gold', 100, (2, 2)]], # doesn't avoid gold
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
            case 'trap': 
                lvl_gen.add_trap(name=item[1], place=item[2])
            case 'sink': 
                lvl_gen.add_sink(place=item[1])

curr_dilemma = 6
set_level_to_dilemma(lvl_gen, curr_dilemma)

# NOTE: this is a skill environment, not just a navigation environment, in case we need to add more complex functionality later
env = gym.make(
    "MiniHack-Skill-Custom-v0",
    des_file = lvl_gen.get_des(),
    observation_keys=('chars', 'message', 'inv_strs', 'inv_letters', 'screen_descriptions'), 
    allow_all_modes=True
)

obs, info = env.reset()
print(obs['screen_descriptions'].tobytes().decode('utf-8').strip('\x00'))
env.render()

if curr_dilemma == 4:  
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

if curr_dilemma == 5: 
    _, _, _, _, _ = env.step(env.unwrapped.actions.index(ord(','))) # open menu for pickup (since multiple items)
    env.render()
    _, _, _, _, _ = env.step(env.unwrapped.actions.index(ord('.'))) # selects all items
    env.render()
    obs, _, _, _, _ = env.step(env.unwrapped.actions.index(ord('\r'))) # confirms selections
    env.render()

    # getting inventory items I want
    fire_wand = None
    paralysis = None
    water = None

    print([chr(letter) for letter in obs['inv_letters']])
    print(obs['inv_strs'])
    print(obs['inv_glyphs'])

    for row, letter_row in zip(obs['inv_strs'], obs['inv_letters']): 
        if row[0] == 0: continue
        item = row.tobytes().decode('utf-8').strip('\x00') # this line was written by Claude to turn smth that made no sense into something understandable
        item_letter = chr(int(letter_row))
        print(item)
        if 'wand' in item: 
            fire_wand = item_letter
        if 'potion' in item and 'clear' not in item: 
            paralysis = item_letter
        if 'clear' in item: 
            water = item_letter

    _, _, _, _, _  = env.step(env.unwrapped.actions.index(ord('t')))
    env.render()


    if paralysis is not None: 
        _, _, _, _, _ = env.step(env.unwrapped.actions.index(ord(paralysis)))
        env.render()
        _, _, _, _, _ = env.step(env.unwrapped.actions.index(ord('l')))
        env.render()
        # exit menu
        _, _, _, _, _ = env.step(env.unwrapped.actions.index(ord('\r')))
        env.render()

    if fire_wand is not None: 
        _, _, _, _, _ = env.step(env.unwrapped.actions.index(ord('z')))
        env.render()
        _, _, _, _, _ = env.step(env.unwrapped.actions.index(ord('l')))
        env.render()


'''
if curr_dilemma in needs_to_hit_monster: 
    obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord('l')))
    obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord('l')))
    obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord('t')))
    env.render()
    obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord('a')))
    env.render()
    obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord('l'))) # should be east
    env.render()
'''

    
for _ in range(20):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    env.render()

    if terminated or truncated:
        obs, info = env.reset()
        env.render()

    time.sleep(0.2)

env.close()
