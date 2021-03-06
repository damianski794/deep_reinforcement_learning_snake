import gym
import gym_snake
# from DQNAgent import DQNAgent
import numpy as np
import tensorflow as tf
from tensorflow.compat.v1.keras.backend import set_session

config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True  # dynamically grow the memory used on the GPU
config.log_device_placement = True  # to log device placement (on which device the operation ran)
sess = tf.compat.v1.Session(config=config)


DISCOUNT = 0.97
REPLAY_MEMORY_SIZE = 50_000  # How many last steps to keep for model training
MIN_REPLAY_MEMORY_SIZE = 1_000  # Minimum number of steps in a memory to start training
MINIBATCH_SIZE = 64  # How many steps (samples) to use for training
UPDATE_TARGET_EVERY = 5  # Terminal states (end of episodes)
MODEL_NAME = '2x256'
MEMORY_FRACTION = 0.20  # useful to train multiple snakes


# Environment settings
EPISODES = 20_000

# Exploration settings
epsilon = 1  # not a constant, going to be decayed
EPSILON_DECAY = 0.99975
MIN_EPSILON = 0.001

#  Stats settings
AGGREGATE_STATS_EVERY = 50  # episodes
SHOW_PREVIEW = False


# the same values when calling random
# random.seed(1)
# np.random.seed(1)
# tf.random.set_seed(1)

## Creating environment
env = gym.make('snake-v0')
env.grid_size = [10, 10]
env.unit_size = 1  # uncomment for Damian's convolutional nn
env.unit_gap = 0   # uncomment for Damian's convolutional nnh


obs = env.reset()

# agent = DQNAgent(obs.shape)

# test models:
# model that avoids walls 8_16_f_16d_2500.model'
# model that verically moves downwards: 8c_maxp_16c_maxp_f_8d_32d_eps_0_2_3500.model'
# 'next model': models\8c_maxp_16c_maxp_f_8d_32d_eps_0_2_11000.model'
# classic nn, snakes performs rly well: d127_d256_d64_d64_d4_1500.model'
model = tf.keras.models.load_model('models\od_Tomka_4_8_f_16d_64d_eps_0_1_same_20000.model')

# Controller
game_controller = env.controller

# Grid
grid_object = game_controller.grid
grid_pixels = grid_object.grid

# Snake(s)
snakes_array = game_controller.snakes
snake_object1 = snakes_array[0]

set_session(sess)


from env_converter import  get_input_for_nn

for i in range(100):
	obs = env.reset()
	done = False
	
	no_of_moves = 0
	while not done:  # run for 1000 steps
		env.render()  # Render latest instance of game
		# if env.controller.snakes[0] is not None:  # uncomment for classic neural network
		# 	get_input_for_nn(env, 0)  # uncomment for classic neural network
		
		# action = np.argmax(model.predict(get_input_for_nn(env, 0).reshape(-1, *get_input_for_nn(env, 0).shape))[0]) # # uncomment for classic neural network
		action = np.argmax(model.predict(obs.reshape(-1, *obs.shape)/255)[0]) # uncomment for convolutional neural network

		print('action -> ', action)
		print(f'EPISODE:  {i}')
		obs, rewards, done, info = env.step([action])  # Implement action
		
		no_of_moves += 1

		if done:
			env.reset()
		
		if no_of_moves > 400:
			done = True

env.close()
