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
    2: [['monster', 'dog', (8, 2), ('peaceful',)], ['monster', 'minotaur', (2, 2)]], # learns which is dangerous maybe? 
    3: [['object', 'coins', '$', (2, 2)], ['object', 'scroll', '?', (8, 2)]], # money or random magic 
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
                lvl_gen.add_monster(name=item[1], place=item[2], args=item[3] if len(item)>3 else ())
            case 'sink': 
                lvl_gen.add_sink(place=item[1])

set_level_to_dilemma(lvl_gen, 2)

# NOTE: this is a skill environment, not just a navigation environment, in case we need to add more complex functionality later
env = gym.make(
    "MiniHack-Skill-Custom-v0",
    des_file = lvl_gen.get_des(),
)

obs, info = env.reset()
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
