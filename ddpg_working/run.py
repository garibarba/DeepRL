#!/usr/bin/env python
import experiment
import gym
import numpy as np
import filter_env
import ddpg
import tensorflow as tf
import plotting

flags = tf.app.flags
FLAGS = flags.FLAGS
flags.DEFINE_boolean('upload', False, 'upload to gym (requires evironment variable OPENAI_GYM_API_KEY)')
# flags.DEFINE_string('env', 'MountainCarContinuous-v0', 'gym environment')
flags.DEFINE_string('env', 'InvertedPendulum-v1', 'gym environment')
flags.DEFINE_integer('train', 10000, 'training time between tests. use 0 for test run only')
flags.DEFINE_integer('test', 10000, 'testing time between training')
# flags.DEFINE_integer('train', 10000, 'training time between tests. use 0 for test run only')
# flags.DEFINE_integer('test', 10000, 'testing time between training')
flags.DEFINE_integer('tmax', 10000, 'maximum timesteps per episode')
flags.DEFINE_bool('random', False, 'use random agent')
flags.DEFINE_bool('tot', False, 'train on test data')
flags.DEFINE_integer('total', 1000000, 'total training time')
flags.DEFINE_float('monitor', .05, 'probability of monitoring a test episode')
# ...
# TODO: make command line options

VERSION = 'DDPG-v0'
GYM_ALGO_ID = 'alg_TmtzkcfSauZoBF97o9aQ'

if FLAGS.random:
    FLAGS.train = 0


import time



class Experiment:
    def run(self,env):
        self.t_train = 0
        self.t_test = 0

        # create filtered environment
        # self.env = filter_env.makeFilteredEnv(gym.make(FLAGS.env))
        self.env = filter_env.makeFilteredEnv(gym.make(env))

        self.t_elapsed = []

        # self.env = gym.make(FLAGS.env)

        if tf.gfile.Exists(FLAGS.outdir):
            tf.gfile.DeleteRecursively(FLAGS.outdir)
        # self.env.monitor.start(FLAGS.outdir + '/monitor/', video_callable=lambda _: False)
        # gym.logger.setLevel(gym.logging.WARNING)

        dimO = self.env.observation_space.shape
        dimA = self.env.action_space.shape
        print 'observationspace action space',
        print(dimO, dimA)

        import pprint
        pprint.pprint(self.env.spec.__dict__, width=1)

        self.agent = ddpg.Agent(dimO=dimO, dimA=dimA)

        returns = []

        it = 0
        episodelengths = []
        testlengths = []

        if env == 'Reacher-v1':
            self.train_frequency = 1
            test_frequency = 3
            plot_frequency = 1

        if env == 'MountainCarContinuous-v0':
            test_frequency = 10
            plot_frequency = 1
            self.train_frequency = 16

        if env == 'InvertedPendulum-v1':
            test_frequency = 100
            plot_frequency = 300
            self.train_frequency = 1

        print 'using train frequency', self.train_frequency

        # main loop
        while self.t_train < FLAGS.total:

            it +=1

            episodelengths.append(self.run_episode(test=False))


            if it % test_frequency== 0:
                testlengths.append(self.run_episode(test=True))

            if it % plot_frequency == 0:
                print 'avg time for sim step:', np.mean(np.array(self.t_elapsed))
                plotting.plot_episode_lengths(episodelengths)
                plotting.plot_episode_lengths(testlengths)
                # plotting.plot_replay_memory_2d_state_histogramm(self.agent.rm.observations)
                # plotting.plot_learned_mu(self.agent.act_test, self.env)

            # else:
            #     # test
            #     T = self.t_test
            #     R = []
            #
            #     while self.t_test - T < FLAGS.test:
            #         # print 'running test episode'
            #         R.append(self.run_episode(test=True, monitor=(self.t_test - T < FLAGS.monitor * FLAGS.test)))
            #     avr = np.mean(R)
            #     print('Average test return\t{} after {} timesteps of training'.format(avr, self.t_train))
            #     # save return
            #     returns.append((self.t_train, avr))
            #     np.save(FLAGS.outdir + "/returns.npy", returns)
            #
            #     # evaluate required number of episodes for gym and end training when above threshold
            #     if self.env.spec.reward_threshold is not None and avr > self.env.spec.reward_threshold:
            #         avr = np.mean([self.run_episode(test=True) for _ in range(self.env.spec.trials)])
            #         if avr > self.env.spec.reward_threshold:
            #             break
            #
            #     # train
            #     T = self.t_train
            #     R = []
            #     while self.t_train - T < FLAGS.train:
            #         # print 'running train episode'
            #         R.append(self.run_episode(test=False))
            #     avr = np.mean(R)
            #     print('Average training return\t{} after {} timesteps of training'.format(avr, self.t_train))

        # self.env.monitor.close()
        # upload results
        if FLAGS.upload:
            gym.upload(FLAGS.outdir + "/monitor", algorithm_id=GYM_ALGO_ID)

    def run_episode(self, test=True, monitor=False):
        # self.env.monitor.configure(lambda _: test and monitor)
        observation = self.env.reset()
        self.agent.reset(observation)
        R = 0  # return
        t = 1
        term = False

        self.t_elapsed = []
        while not term:
            t_loopstart = time.clock()
            # self.env.render(mode='human')

            if FLAGS.random:
                action = self.env.action_space.sample()
            else:
                action = self.agent.act(test=test)

            observation, reward, term, info = self.env.step(action)

            
            term = (t >= FLAGS.tmax) or term

            observation = observation.squeeze()

            r_f = self.env.filter_reward(reward)

            perform_trainstep = False
            if t % self.train_frequency == 0:
                perform_trainstep =True
            self.agent.observe(r_f, term, observation, test=test and not FLAGS.tot, perform_trainstep = perform_trainstep)

            if test:
                self.t_test += 1
            else:
                self.t_train += 1

            R += reward
            t += 1

            # if t % 100 == 0:
            #     print t
            self.t_elapsed.append(time.clock() - t_loopstart)

        return R


def main():
    Experiment().run()


if __name__ == '__main__':
    # experiment.run(main)
    e = Experiment()
    e.run('InvertedPendulum-v1')
