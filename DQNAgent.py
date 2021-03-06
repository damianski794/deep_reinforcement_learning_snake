import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Activation, Conv2D, Dense, Dropout, Flatten, MaxPool2D
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.optimizers import Adam

from ModifiedTensorBoard import ModifiedTensorBoard

from collections import deque
import numpy as np
import random
import time


DISCOUNT = 0.97
REPLAY_MEMORY_SIZE = 50_000  # How many last steps to keep for model training
MIN_REPLAY_MEMORY_SIZE = 1_000  # Minimum number of steps in a memory to start training
MINIBATCH_SIZE = 64  # How many steps (samples) to use for training
UPDATE_TARGET_EVERY = 5  # Terminal states (end of episodes)

# np = no pooling
# p
# c = conv
# f = flatten
# d = dense
MODEL_NAME = "8c_maxp_16c_maxp_f_8d_32d_eps_0_2"

class DQNAgent:
    def __init__(self, env_shape=(10, 10, 3)):
        print('env shape =', env_shape)

        # Main model
        self.model = self.create_model(env_shape)

        # target network
        self.target_model = self.create_model(env_shape)
        self.target_model.set_weights(self.model.get_weights())

        # An array with last n steps for training
        self.replay_memory = deque(maxlen=REPLAY_MEMORY_SIZE)

        self.tensorboard = ModifiedTensorBoard(log_dir=f'logs\\{MODEL_NAME}_{int(time.time())}')

        # Used to count when to update target network with main network's weights
        self.target_update_counter = 0

    def create_model(self, env_shape):
        model = Sequential()

        model.add(Conv2D(8, (3, 3), activation='relu', input_shape=env_shape))
        model.add(MaxPool2D((3, 3)))
        model.add(Dropout(0.2))

        model.add(Conv2D(16, (3, 3), activation='relu'))
        model.add(MaxPool2D((3, 3)))

        model.add(Dropout(0.2))

        model.add(Flatten())
        model.add(Dense(8, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(4, activation='linear'))  # 4 <- action space size

        model.compile(loss="mse", optimizer=Adam(lr=0.001), metrics=['accuracy'])
        print(model.summary())
        return model

    # Adds step's data to a memory replay array
    # (observation space, action, reward, new observation space, done)
    def update_replay_memory(self, transition):
        self.replay_memory.append(transition)

    # Trains main network every step during episode
    def train(self, terminal_state, step):
        # Start training only if certain number of samples is already saved
        if len(self.replay_memory) < MIN_REPLAY_MEMORY_SIZE:
            return

        # Get a minibatch of random samples from memory replay table
        minibatch = random.sample(self.replay_memory, MINIBATCH_SIZE)

        # Get current states from minibatch, then query NN model for Q values
        current_states = np.array([transition[0] for transition in minibatch]) / 255
        current_qs_list = self.model.predict(current_states)

        # Get future states from minibatch, then query NN model for Q values
        # When using target network, query it, otherwise main network should be queried
        new_current_states = np.array([transition[3] for transition in minibatch]) / 255
        future_qs_list = self.target_model.predict(new_current_states)

        X = []
        y = []

        # Now we need to enumerate our batches
        for index, (current_state, action, reward, new_current_state, done) in enumerate(minibatch):

            # If not a terminal state, get new q from future states, otherwise set it to 0
            # almost like with Q Learning, but we use just part of equation here
            if not done:
                max_future_q = np.max(future_qs_list[index])
                new_q = reward + DISCOUNT * max_future_q
            else:
                new_q = reward

            # Update Q value for given state
            current_qs = current_qs_list[index]
            current_qs[action] = new_q

            # And append to our training data
            X.append(current_state)
            y.append(current_qs)

        # Fit on all samples as one batch, log only on terminal state
        self.model.fit(np.array(X) / 255, np.array(y), batch_size=MINIBATCH_SIZE, verbose=0, shuffle=False,
                       callbacks=[self.tensorboard] if terminal_state else None)

        # Update target network counter every episode
        if terminal_state:
            self.target_update_counter += 1

        # If counter reaches set value, update target network with weights of main network
        if self.target_update_counter > UPDATE_TARGET_EVERY:
            self.target_model.set_weights(self.model.get_weights())
            self.target_update_counter = 0

        # Queries main network for Q values given current observation space (environment state)

    def get_qs(self, state):
        return self.target_model.predict(state.reshape(-1, *state.shape)/255)[0]

