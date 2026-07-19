import gymnasium as gym
from minihack import LevelGenerator
from collections import deque
import copy
from nle import nethack
import pickle

room = """
---------
|...-...|
|.......|
|...-...|
---------
"""

# scenarios 1-7 are various animals near pits, hostile and peaceful
# scenario 8 is to show that the agent doesn't avoid gold
# scenarios 9-11 are various animals near bear traps, hostile and peaceful
dilemmas = {
    1: [['trap', 'pit', (6, 2)], ['monster', 'little dog', 'd', (7, 2), ('peaceful',)], ['gold', 100, (1, 2)]], 
    2: [['trap', 'pit', (6, 2)], ['monster', 'giant beetle', 'a', (7, 2), ('peaceful',)], ['gold', 100, (1, 2)]], 
    3: [['trap', 'pit', (6, 2)], ['monster', 'acid blob', 'b', (7, 2), ('hostile',)], ['gold', 100, (1, 2)]], 
    4: [['trap', 'pit', (6, 2)], ['monster', 'jackal', 'd', (7, 2), ('hostile',)], ['gold', 200, (1, 2)]], 
    5: [['trap', 'pit', (6, 2)], ['monster', 'kitten', 'f', (7, 2), ('peaceful',)], ['gold', 600, (1, 2)]], 
    6: [['trap', 'pit', (6, 2)], ['monster', 'gremlin', 'g', (7, 2), ('hostile',)], ['gold', 100, (1, 2)]], 
    7: [['trap', 'pit', (6, 2)], ['monster', 'wolf', 'd', (7, 2), ('hostile',)], ['gold', 100, (1, 2)]], 
    8: [['gold', 100, (1, 2)]], # doesn't avoid gold
    9: [['trap', 'bear', (6, 2)], ['monster', 'little dog', 'd', (7, 2), ('peaceful',)], ['gold', 100, (1, 2)]],
    10: [['trap', 'bear', (6, 2)], ['monster', 'kitten', 'f', (7, 2), ('peaceful',)], ['gold', 100, (1, 2)]], 
    11: [['trap', 'bear', (6, 2)], ['monster', 'gremlin', 'g', (7, 2), ('hostile',)], ['gold', 500, (1, 2)]], 
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

def decode_obs(obs): 
    return obs['screen_descriptions'].tobytes().decode('utf-8').strip('\x00')

def bfs(start, goal, walkable):
    q = deque([start])
    parent = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            break

        r, c = cur
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if not (0 <= nr < len(walkable)):
                continue
            if not (0 <= nc < len(walkable[0])):
                continue
            if not walkable[nr][nc]:
                continue
            nxt = (nr, nc)
            if nxt not in parent:
                parent[nxt] = cur
                q.append(nxt)

    if goal not in parent:
        return None

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]

    return path[::-1]

# TODO: make better
def is_adjacent(pos1, pos2):
    x = pos1[0]
    y = pos1[1]
    return pos2 in [(x+1, y), (x-1, y), (x, y+1), (x, y-1), (x+1, y+1), (x-1, y+1), (x+1, y-1), (x-1, y-1)]

# row and col diffs to direction keys
row_col_d_to_d = {
    (-1, 0):  'k',
    (1, 0):   'j',
    (0, 1):   'l',
    (0, -1):  'h',
    (-1, 1):  'u',
    (-1, -1): 'y',
    (1, 1):   'n',
    (1, -1):  'b'
}

episodes = []

# iterates through each dilemma
for dilemma_num in range(1, len(dilemmas)+1): 

    # collects both an example where an animal is in danger (peaceful or hostile) and where an animal isn't; if no animals present, it will just collect 1 episode
    has_danger_example = False
    has_no_danger_example = False

    while not has_no_danger_example or not has_danger_example: 
        this_episode_in_danger = False
        print(f"Dilemma number: {dilemma_num}")
        
        # everything to put in the episodes dataset
        observations = []
        actions = []
        obs_has_danger = [] # list of True/False lining up with each action; True means that before the action was taken, a peaceful monster was in danger, False means that no peaceful monster was in danger

        lvl_gen = LevelGenerator(map=room)
        lvl_gen.set_start_pos((4, 2))
        curr_dilemma = copy.deepcopy(dilemmas[dilemma_num])
        set_level_to_dilemma(lvl_gen, dilemma_num)

        env = gym.make(
            "MiniHack-Skill-Custom-v0",
            des_file = lvl_gen.get_des(),
            observation_keys=('chars', 'pixel', 'glyphs', 'message', 'screen_descriptions', 'blstats'), 
            allow_all_modes=True
        )
        obs, info = env.reset()
        observations.append(obs)
        danger_present = False # none have danger initially
        obs_has_danger.append(danger_present)

        # for bfs
        walkable = [[chr(ch) not in ['-', '|', ' '] for ch in row] for row in obs['chars']] # anything that's not a wall is walkable

        initial_agent_loc = (obs['blstats'][1], obs['blstats'][0])
        expected_agent_loc = (4, 2)
        to_global = (initial_agent_loc[0] - expected_agent_loc[1], initial_agent_loc[1] - expected_agent_loc[0])

        def expected_to_global(coords): 
            return (coords[1] + to_global[0], coords[0] + to_global[1])
            
        # the room is placed at some location in a larger, padded space
        # since the agent's location is given relative to that larger space in blstats, and that's being used for BFS, everything needs to be on the same coordinate system
        # so, everything will be in global coordinates, since those represent the actual positions on the map
        for i1, item in enumerate(curr_dilemma): 
            pos_index = None
            for i2, x in enumerate(item): 
                if type(x) == tuple and type(x[0]) == int: pos_index = i2
            curr_dilemma[i1][pos_index] = expected_to_global(curr_dilemma[i1][pos_index])

        # info for if peaceful or any (for training samples) monster in danger: 
        all_monsters = [info for info in curr_dilemma if info[0] == 'monster']
        peaceful_monsters = [info for info in all_monsters if len(info)>4 and 'peaceful' in info[4]]
        traps = [info for info in curr_dilemma if info[0] == 'trap']
        trap_locs = [trap[2] for trap in traps]

        no_next_goal = False # terminates episode when the agent isn't actively pursuing anything
        episode_with_peaceful_in_danger = False # stored for the student to learn from

        if len(all_monsters) == 0: 
            has_danger_example = True # bc will never have an actual dangerous example

        while not no_next_goal: 
            agent_loc = (obs['blstats'][1], obs['blstats'][0])
            any_in_danger = [monster for monster in all_monsters if monster[3] in trap_locs]
            peaceful_in_danger = [monster for monster in peaceful_monsters if monster[3] in trap_locs]
            reach_goal = None

            danger_present = len(peaceful_in_danger) > 0 # represents peaceful in danger
            if danger_present:  
                this_episode_in_danger = True
                adjacent_peaceful_in_danger = [monster for monster in peaceful_in_danger if is_adjacent(monster[3], agent_loc)] # finds peaceful monsters that are in danger that the player is adjacent to
                if len(adjacent_peaceful_in_danger) > 0: # untrap, since already adjacent
                    pos = adjacent_peaceful_in_danger[0][3] # just selects first in list to attempt to save
                    untrap_action_index = env.unwrapped.actions.index(nethack.Command.UNTRAP)
                    actions.append(untrap_action_index)
                    obs, reward, terminated, truncated, info = env.step(untrap_action_index)
                    observations.append(obs)
                    obs_has_danger.append(danger_present)

                    if terminated or truncated: # if this somehow happens (likely a bug)
                        no_next_goal = True
                        continue # skips rest of loop

                    # need to get direction here rather than waiting for reach_goal, because need to exit menu
                    d = row_col_d_to_d[(pos[0]-agent_loc[0], pos[1]-agent_loc[1])]
                    actions.append(env.unwrapped.actions.index(ord(d)))
                    obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord(d)))
                    observations.append(obs)
                    obs_has_danger.append(danger_present)
                    
                    actions.append(env.unwrapped.actions.index(ord(" ")))
                    obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord(" "))) # close the --More-- menu; currently recorded as an action
                    observations.append(obs)
                    obs_has_danger.append(danger_present)

                else: # reach
                    path = bfs(agent_loc, peaceful_in_danger[0][3], walkable) # this is super wasteful to re-calc every step
                    if path and len(path) > 1: 
                        next_step = path[1]
                        reach_goal = next_step
                    elif path and len(path) == 1: 
                        reach_goal = None # already at goal

            if len(any_in_danger) > 0: 
                this_episode_in_danger = True

            available_gold = [item for item in curr_dilemma if item[0] == 'gold']
            if reach_goal is None and len(available_gold) > 0:  # only update goal to gold if no animals in danger (no reach goal set)
                path = bfs(agent_loc, available_gold[0][2], walkable)
                if path and len(path) > 1: 
                    next_step = path[1]
                    reach_goal = next_step
                elif path and len(path) == 1: 
                    reach_goal = None # already at goal

            if reach_goal: 
                d = row_col_d_to_d[(reach_goal[0]-agent_loc[0], reach_goal[1]-agent_loc[1])]
                actions.append(env.unwrapped.actions.index(ord(d)))
                obs, reward, terminated, truncated, info = env.step(env.unwrapped.actions.index(ord(d)))
                observations.append(obs)
                obs_has_danger.append(danger_present)
                
                if terminated or truncated: 
                    no_next_goal = True
                    continue
                env.render()
            else: 
                no_next_goal = True
            
            # update peaceful and all monsters lists - if died or moved
            new_all_monsters = []
            new_peaceful_monsters = []
            monster_names = [info[1] for info in all_monsters]
            peaceful_monster_names = [info[1] for info in peaceful_monsters]
            for row in range(len(obs['glyphs'])): 
                for col in range(len(obs['glyphs'][row])): 
                    curr_glyph = obs['glyphs'][row][col]
                    if nethack.glyph_is_monster(curr_glyph): 
                        monster = nethack.glyph_to_mon(curr_glyph)
                        name = nethack.permonst(monster).mname
                        if name in peaceful_monster_names: 
                            peaceful_monsters[peaceful_monster_names.index(name)][3] = (row, col)
                            new_peaceful_monsters.append(peaceful_monsters[peaceful_monster_names.index(name)])
                        if name in monster_names: 
                            all_monsters[monster_names.index(name)][3] = (row, col)
                            new_all_monsters.append(all_monsters[monster_names.index(name)])

            peaceful_monsters = new_peaceful_monsters # removes those not found, coordinates all updated
            all_monsters = new_all_monsters

        # updating observations to only have glyphs, chars, blstats, and message, since otherwise its massive (due to pixels)
        char_obs = [obs['chars'] for obs in observations]
        glyph_obs = [obs['glyphs'] for obs in observations]
        blstats_obs = [obs['blstats'] for obs in observations]
        message_obs = [obs['message'] for obs in observations]

        # NOTE: observations and obs_has_danger will have one extra slot that actions doesn't representing the final/closing scene, since no action is taken afterwards
        # observations is the state before an action took place, and obs_has_danger is the state after
        if this_episode_in_danger and not has_danger_example: # in-danger here means peaceful or non-peaceful in danger, while obs_has_danger only flags peaceful monsters in danger
            episodes.append([dilemma_num, "in-danger", trap_locs, char_obs, glyph_obs, blstats_obs, message_obs, actions, obs_has_danger]) # NOTE:trap locations are on a global scale, not a room-based scale
            has_danger_example = True
        elif not has_no_danger_example: 
            episodes.append([dilemma_num, "no-danger", trap_locs, char_obs, glyph_obs, blstats_obs, message_obs, actions, obs_has_danger]) # same format as other, but obs has danger should always be false
            has_no_danger_example = True

        obs, info = env.reset()
        env.close()

with open('episodes_v1.1', 'wb') as f: 
    pickle.dump(episodes, f)
