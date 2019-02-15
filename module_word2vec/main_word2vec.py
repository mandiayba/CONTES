#!/usr/bin/env python
#-*- coding: utf-8 -*-
# coding: utf-8


"""
Author: Arnaud Ferré
Mail: arnaud.ferre.pro@gmail.com
Description: Word2Vec/Gensim module to implement on ALVIS-ML/NLP
    If you want to cite this work in your publication or to have more details:
    http://www.aclweb.org/anthology/W17-2312.
Dependencies: Require the installation of Gensim (https://radimrehurek.com/gensim/install.html)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/..")

from gensim.models.fasttext import FastText as FastText
from gensim.models.wrappers.fasttext import FastText as FastText_OPT

import logging
import fastText as nativeFastText
import gensim
import json
import numpy
from sys import stderr, stdin
from optparse import OptionParser
import gzip


class Word2Vec(OptionParser):
    def __init__(self):
        OptionParser.__init__(self, usage='usage: %prog [options]')
        self.add_option('--json', action='store', type='string', dest='json', help='JSON output filename')
        self.add_option('--txt', action='store', type='string', dest='txt', help='TXT output filename')
        self.add_option('--bin', action='store', type='string', dest='bin', help='binary output filename')
        self.add_option('--min-count', action='store', type='int', dest='minCount', default=0, help='Ignore all words with total frequency lower than this')
        self.add_option('--vector-size', action='store', type='int', dest='vectSize', default=300, help='The dimensionality of the feature vectors, often effective between 100 and 300')
        self.add_option('--workers', action='store', type='int', dest='workerNum', default=2, help='Use this many worker threads to train the model (=faster training with multicore machines)')
        self.add_option('--skip-gram', action='store_true', dest='skipGram', default=False, help='Defines the training algorithm, by default CBOW is used, otherwise skip-gram is employed')
        self.add_option('--window-size', action='store', type='int', dest='windowSize', default=2, help='The maximum distance between the current and predicted word within a sentence')
        self.add_option('--iterations', action='store', type='int', dest='numIteration', default=5, help='Number of iterations (default: %default)')
        self.add_option('--seed', action='store', type='int', dest='seed', default=1, help='Random number generator seed')
        self.add_option('--method', action='store', dest='method', default=None, help='Method to train vectors, values in [word2vec, fasttext, fasttext_optimized]')
        self.add_option('--minNgram', action='store', type='int', dest='minNgram', default=3, help='min length of char ngrams (Default 3), to only with the FastText method')
        self.add_option('--maxNgram', action='store', type='int', dest='maxNgram', default=6, help='max length of char ngrams (Default 6), to only with the FastText method')
        self.add_option('--bucket', action='store', type='int', dest='bucket', default=2000000, help='number of buckets used for hashing ngrams, to use only with FastText method')
        self.add_option('--fastTextHome', action='store', type='int', dest='fastTextHome', default=None, help='path to the FastText home directory. Used with when method=fasttext_optimized (see https://github.com/facebookresearch/fastText)')
        
        
        self.corpus = []

    def buildVector(self, workerNum=8, minCount=0, vectSize=200, skipGram=True, windowSize=2, 
                   learningRate=0.05, numIteration=5, negativeSampling=5, 
                   subSampling=0.001, seed=1, method=None,
                   minNgram=3, maxNgram=6, bucket=2000000, fastTextHome=None):
        """
        Description: Implementation of the neuronal method Word2Vec to create word vectors based on the distributional
        semantics hypothesis.
        
        :param workerNum: Use this many worker threads to train the model (=faster training with multicore machines).
        :param minCount: Ignore all words with total frequency lower than this.
        :param vectSize: The dimensionality of the feature vectors. Often effective between 100 and 300.
        :param skipGram: Defines the training algorithm. By default (sg=0), CBOW is used. Otherwise (sg=1), skip-gram is employed.
        :param windowSize: The maximum distance between the current and predicted word within a sentence.
        :param learningRate: Alpha is the initial learning rate (will linearly drop to min_alpha as training progresses).
        :param numIteration: Number of iterations (epochs) over the corpus. Default is 5.
        :param negativeSampling: if > 0, negative sampling will be used, the int for negative specifies how many
        “noise words” should be drawn (usually between 5-20). Default is 5. If set to 0, no negative samping is used.
        :param subSampling: Threshold for configuring which higher-frequency words are randomly downsampled;
        default is 1e-3, useful range is (0, 1e-5).
        :param method: is to specify the method used, supported methods are word2vec and fastText
        :param minNgram: is the minimum length of char n-grams to be used for training word representations.
        :param maxNgram: is max length of char ngrams to be used for training word representations. Set max_n to be lesser than min_n to avoid char ngrams being used.
        :param bucket: Character ngrams are hashed into a fixed number of buckets, in order to limit the memory usage of the model. This option specifies the number of buckets used by the model.
        :param fastTextHome: path to the original and optimized fastText implementation
        
        :return: vst (vector space of terms) is a dictionary containing the form of token as key and the corresponding
        vector as unique value.

        For more details, see: https://radimrehurek.com/gensim/models/word2vec.html, https://radimrehurek.com/gensim/models/fasttext.html 
        """

        logging.info("Building the embeddings vectors...")
        print("Building the embeddings vectors...", file=sys.stderr)

        if method != None and "word2vec" in method.lower():
            logging.info("Using word2vec method...")
            print("Using word2vec method...", file=sys.stderr)
            self.vst_model = gensim.models.Word2Vec(self.corpus, min_count=minCount, size=vectSize, workers=workerNum, sg=skipGram,
                                       window=windowSize, alpha=learningRate, iter=numIteration, negative=negativeSampling,
                                       sample=subSampling, seed=seed)
            logging.info("Creating the vocabulary dictionary...")
            print("Creating the vocabulary dictionary...", file=sys.stderr)
            self.VST = dict((k, list(numpy.float_(npf32) for npf32 in self.vst_model.wv[k])) for k in self.vst_model.wv.vocab.keys())

        if method != None and "fasttext" in method.lower():
            logging.info("Using fastText method...")
            print("Using fastText method...", file=sys.stderr)
            self.vst_model = FastText(size=vectSize, sg=skipGram, window=windowSize, 
            min_count=minCount, iter=numIteration, negative=negativeSampling, 
            alpha=learningRate, min_n=minNgram, max_n=maxNgram, bucket=bucket, workers=workerNum)
            self.vst_model.build_vocab(sentences=self.corpus)
            # train the model
            self.vst_model.train(
            sentences=self.corpus,
            total_examples=self.vst_model.corpus_count,
            epochs=self.vst_model.epochs,
            threads=workerNum
            )
            logging.info("Creating the vocabulary dictionary...")
            print("Creating the vocabulary dictionary...", file=sys.stderr)
            self.VST = dict((k, list(numpy.float_(npf32) for npf32 in self.vst_model.wv[k])) for k in self.vst_model.wv.vocab.keys())

        if method != None and "fasttext" in method.lower() and "optimized" in method.lower():
            logging.info("Using fastText method...")
            print("Using fastText method...", file=sys.stderr)
            # train the model
            #import inspect
            #path2fastText = os.path.dirname(inspect.getfile(nativeFastText))
            FastText_OPT.train(ft_path=fastTextHome, corpus_file=self.corpus, 
                    model = 'skipgram', size = vectSize, alpha = learningRate, window = windowSize, 
                    min_count = minCount, negative = negativeSampling, iter = numIteration,
                    min_n = minNgram, max_n = maxNgram, threads = workerNum) 
            logging.info("Creating the vocabulary dictionary...")
            print("Creating the vocabulary dictionary...", file=sys.stderr)
            self.VST = dict((k, list(numpy.float_(npf32) for npf32 in self.vst_model.wv[k])) for k in self.vst_model.wv.vocab.keys())



    def run(self):
        options, args = self.parse_args()
        self.readCorpusFiles(args)
        self.buildVector(minCount=options.minCount, vectSize=options.vectSize, workerNum=options.workerNum,
                       skipGram=options.skipGram, windowSize=options.windowSize, numIteration=options.numIteration,
                       seed=options.seed, method=options.method,
                       minNgram=options.minNgram, maxNgram=options.maxNgram, bucket=options.bucket, fastTextHome=options.fastTextHome)
        self.writeJSON(options.json)
        self.writeTxt(options.txt)
        self.writeBin(options.bin)

    def writeBin(self, fileName):
        if fileName is None:
            return
        self.vst_model.save(fileName)
        
    def writeJSON(self, fileName):
        if fileName is None:
            return
        if fileName.endswith('.gz'):
            f = gzip.open(fileName, 'w')
        else:
            #f = open(fileName, 'w', encoding='utf-8')
            f = open(fileName, 'w')
        #json.dump(self.VST, f, ensure_ascii=True)
        #f.write(json.dumps(self.VST))
        f.write(json.dumps(self.VST).encode('UTF-8'))
        f.close()

    def writeTxt(self, fileName):
        if fileName is None:
            return
        #f = open(fileName, 'w', encoding='utf-8')
        f = open(fileName, 'w')
        for k, v in self.VST.items():
            f.write(k)
            f.write('\t')
            f.write(str(v))
            f.write('\n')
        f.close()
        
    def readCorpusFiles(self, fileNames):
        if len(fileNames) == 0:
            self.readCorpus(stdin)
            return
        for fn in fileNames:
            #f = open(fn, encoding='utf-8')
            f = open(fn)
            self.readCorpus(f)
            f.close()
            
    def readCorpus(self, f):
        current_sentence = []
        for line in f:
            line = line.strip()
            if line == '':
                if len(current_sentence) > 0:
                    self.corpus.append(current_sentence)
                    current_sentence = []
            else:
                current_sentence.append(line)
        if len(current_sentence) > 0:
            self.corpus.append(current_sentence)

if __name__ == '__main__':
    Word2Vec().run()
