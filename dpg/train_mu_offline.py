from __future__ import print_function
import moutaincar_dpg

import numpy as np

np.set_printoptions(threshold=np.inf)


from nn import nn
from nn_batchnorm import nn_batchnorm

class mu_offline_training():

    def __init__(self, use_batchnorm = True):

        self.num_sgd_updates = 3000

        # create neural network:
        self.car1 = moutaincar_dpg.mountaincar_dpg()
        self.car1.loaddata('dpg_mountain_car_iter250')
        self.car1.plot_policy(mode= 'deterministic')

        obs_low = self.car1.env.observation_space.low
        obs_high = self.car1.env.observation_space.high

        if use_batchnorm:
            self.nn1 = nn_batchnorm(input_low= obs_low, input_high= obs_high, car= self.car1)
        else:
            self.nn1 = nn(input_low= obs_low, input_high= obs_high, car= self.car1)

        self.nn1.main()

    def start_training(self):
        obs_low = self.car1.env.observation_space.low
        obs_high = self.car1.env.observation_space.high

        for i in range(self.num_sgd_updates*self.nn1.batchsize):
            xs = np.array([ np.random.uniform(obs_low[0], obs_high[0]),
                            np.random.uniform(obs_low[1], obs_high[1]) ]).squeeze()

            self.nn1.add_to_batch(state= xs, mu= self.car1.mu(xs))

if __name__ == '__main__':

    t1 = mu_offline_training(use_batchnorm= True)
    t1.start_training()