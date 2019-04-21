from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import numpy as np
from bert_serving.client import BertClient
from termcolor import colored
from flask_cors import CORS
import os
import csv
import collections
import tokenization
import modeling
import tensorflow as tf
# for getting article text
from nltk import tokenize
from goose3 import Goose

prefix_q = '##### **Q:** '
topk = 5
import sys

from flask import Flask, render_template, request, redirect, Response, jsonify
import random, json

flags = tf.flags

FLAGS = flags.FLAGS

## Required parameters
flags.DEFINE_string("data_dir", None,"The input data dir. Should contain the .tsv files (or other data files) ")

flags.DEFINE_string("bert_config_file", None,"The config json file corresponding to the pre-trained BERT model. ")

flags.DEFINE_string("task_name", None, "The name of the task to train.")

flags.DEFINE_string("vocab_file", None,"The vocabulary file that the BERT model was trained on.")

flags.DEFINE_string("output_dir", None,"The output directory where the model checkpoints will be written.")

## Other parameters

flags.DEFINE_string("init_checkpoint", None,"Initial checkpoint (usually from a pre-trained BERT model).")

flags.DEFINE_bool("do_lower_case", True,"Whether to lower case the input text. Should be True for uncased ")

flags.DEFINE_integer("max_seq_length", 128,"The maximum total input sequence length after WordPiece tokenization. ")

flags.DEFINE_bool("do_train", False, "Whether to run training.")

flags.DEFINE_bool("do_eval", False, "Whether to run eval on the dev set.")

flags.DEFINE_bool("do_predict", False, "Whether to run the model in inference mode on the test set.")

flags.DEFINE_integer("train_batch_size", 32, "Total batch size for training.")

flags.DEFINE_integer("eval_batch_size", 8, "Total batch size for eval.")

flags.DEFINE_integer("predict_batch_size", 8, "Total batch size for predict.")

flags.DEFINE_float("learning_rate", 5e-5, "The initial learning rate for Adam.")

flags.DEFINE_float("num_train_epochs", 3.0, "Total number of training epochs to perform.")

flags.DEFINE_float("warmup_proportion", 0.1,"Proportion of training to perform linear learning rate warmup for. ")

flags.DEFINE_integer("save_checkpoints_steps", 1000, "How often to save the model checkpoint.")

flags.DEFINE_integer("iterations_per_loop", 1000, "How many steps to make in each estimator call.")

flags.DEFINE_bool("use_tpu", False, "Whether to use TPU or GPU/CPU.")

tf.flags.DEFINE_string("tpu_name", None,"The Cloud TPU to use for training. This should be either the name ")

tf.flags.DEFINE_string("tpu_zone", None,"[Optional] GCE zone where the Cloud TPU is located in. If not ")

tf.flags.DEFINE_string("gcp_project", None,"[Optional] Project name for the Cloud TPU-enabled project. If not ")

tf.flags.DEFINE_string("master", None, "[Optional] TensorFlow master URL.")

flags.DEFINE_integer("num_tpu_cores", 8, "Only used if `use_tpu` is True. Total number of TPU cores to use.")

app = Flask(__name__)
CORS(app)

@app.route("/receive", methods = ['POST'])
def worker():
    data = request.get_json()
    filepath = os.path.abspath('vaccine-myths.md')
    print(filepath)
    with open(filepath) as fp:
        questions = [v.replace(prefix_q, '').strip() for v in fp if v.strip() and v.startswith(prefix_q)]
    with BertClient(port=5555, port_out=5556) as bc:
        doc_vecs = bc.encode(questions)
    score = np.sum(data['result'] * doc_vecs, axis=1)
    topk_idx = np.argsort(score)[::-1][:topk]
    result = questions[topk_idx[0]]
    return jsonify({'message': result})

# get entire article text
@app.route("/article", methods = ['POST'])
def article():
    url = request.get_json()
    filepath = os.path.abspath('vaccine-myths.md')
    print(filepath)
    with open(filepath) as fp:
        myths = [v.replace(prefix_q, '').strip() for v in fp if v.strip() and v.startswith(prefix_q)]

    # extract article text
    g = Goose()
    article = g.extract(url=url)
    text = article.cleaned_text
    sentences = tokenize.sent_tokenize(text)

    # encode sentences
    with BertClient(port=5555, port_out=5556) as bc:
        article_encode = bc.encode(sentences)
        doc_vecs = bc.encode(myths)

    # testing with 3rd sentence in article
    score = np.sum(article_encode[3] * doc_vecs, axis=1)
    topk_idx = np.argsort(score)[::-1][:topk]
    result = myths[topk_idx[0]]
    return jsonify({'message': result})

class InputExample(object):
    def __init__(self, text_a, text_b=None, label=None):
        self.text_a = text_a
        self.text_b = text_b
        self.label = label

class DataProcessor(object):
    def get_labels(self):
        raise NotImplementedError()


class MnliProcessor(DataProcessor):
    def get_labels(self):
        return ["contradiction", "entailment", "neutral"]
    def create_examples(self, sentence_a, sentence_b):
        examples = []
        text_a = tokenization.convert_to_unicode(sentence_a)
        text_b = tokenization.convert_to_unicode(sentence_b)
        label = "contradiction"
        examples.append(InputExample(text_a, text_b, label))
        return examples
class PaddingInputExample(object):
      """Fake example so the num input examples is a multiple of the batch size.

      When running eval/predict on the TPU, we need to pad the number of examples
      to be a multiple of the batch size, because the TPU requires a fixed batch
      size. The alternative is to drop the last batch, which is bad because it means
      the entire output data won't be generated.

      We use this class instead of `None` because treating `None` as padding
      battches could cause silent errors.
      """

class InputFeatures(object):

    def __init__(self,input_ids,input_mask,segment_ids,label_id,is_real_example=True):
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.label_id = label_id
        self.is_real_example = is_real_example
class MrpcProcessor(DataProcessor):
    def get_labels(self):
        return ["0", "1"]

    def create_examples(self, sentence_a, sentence_b):
        examples = []
        label = "0"
        text_a = tokenization.convert_to_unicode(sentence_a)
        print(text_a)
        text_b = tokenization.convert_to_unicode(sentence_b)
        print(text_b)
        examples.append(InputExample(text_a, text_b, label))
        return examples
def _truncate_seq_pair(tokens_a, tokens_b, max_length):

  # This is a simple heuristic which will always truncate the longer sequence
  # one token at a time. This makes more sense than truncating an equal percent
  # of tokens from each, since if one sequence is very short then each token
  # that's truncated likely contains more information than a longer sequence.
    while True:
        total_length = len(tokens_a) + len(tokens_b)
        if total_length <= max_length:
            break
        if len(tokens_a) > len(tokens_b):
            tokens_a.pop()
        else:
            tokens_b.pop()

def convert_single_example(ex_index, example, label_list, max_seq_length,tokenizer):


    if isinstance(example, PaddingInputExample):
        return InputFeatures(
            input_ids=[0] * max_seq_length,
            input_mask=[0] * max_seq_length,
            segment_ids=[0] * max_seq_length,
            label_id=0,
            is_real_example=False)

    label_map = {}
    for (i, label) in enumerate(label_list):
        label_map[label] = i

    tokens_a = tokenizer.tokenize(example.text_a)
    tokens_b = None
    if example.text_b:
        tokens_b = tokenizer.tokenize(example.text_b)

    if tokens_b:
    # Modifies `tokens_a` and `tokens_b` in place so that the total
    # length is less than the specified length.
    # Account for [CLS], [SEP], [SEP] with "- 3"
        _truncate_seq_pair(tokens_a, tokens_b, max_seq_length - 3)
    else:
    # Account for [CLS] and [SEP] with "- 2"
        if len(tokens_a) > max_seq_length - 2:
            tokens_a = tokens_a[0:(max_seq_length - 2)]

  # The convention in BERT is:
  # (a) For sequence pairs:
  #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
  #  type_ids: 0     0  0    0    0     0       0 0     1  1  1  1   1 1
  # (b) For single sequences:
  #  tokens:   [CLS] the dog is hairy . [SEP]
  #  type_ids: 0     0   0   0  0     0 0
  #
  # Where "type_ids" are used to indicate whether this is the first
  # sequence or the second sequence. The embedding vectors for `type=0` and
  # `type=1` were learned during pre-training and are added to the wordpiece
  # embedding vector (and position vector). This is not *strictly* necessary
  # since the [SEP] token unambiguously separates the sequences, but it makes
  # it easier for the model to learn the concept of sequences.
  #
  # For classification tasks, the first vector (corresponding to [CLS]) is
  # used as the "sentence vector". Note that this only makes sense because
  # the entire model is fine-tuned.
    tokens = []
    segment_ids = []
    tokens.append("[CLS]")
    segment_ids.append(0)
    for token in tokens_a:
        tokens.append(token)
        segment_ids.append(0)
    tokens.append("[SEP]")
    segment_ids.append(0)

    if tokens_b:
        for token in tokens_b:
            tokens.append(token)
            segment_ids.append(1)
        tokens.append("[SEP]")
        segment_ids.append(1)

    input_ids = tokenizer.convert_tokens_to_ids(tokens)

  # The mask has 1 for real tokens and 0 for padding tokens. Only real
  # tokens are attended to.
    input_mask = [1] * len(input_ids)

  # Zero-pad up to the sequence length.
    while len(input_ids) < max_seq_length:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    label_id = label_map[example.label]
    if ex_index < 5:
        tf.logging.info("*** Example ***")
        tf.logging.info("tokens: %s" % " ".join(
            [tokenization.printable_text(x) for x in tokens]))
        tf.logging.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
        tf.logging.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
        tf.logging.info("segment_ids: %s" % " ".join([str(x) for x in segment_ids]))
        tf.logging.info("label: %s (id = %d)" % (example.label, label_id))

    feature = InputFeatures(
        input_ids=input_ids,
        input_mask=input_mask,
        segment_ids=segment_ids,
        label_id=label_id,
        is_real_example=True)
    return feature




def file_based_convert_examples_to_features(examples, label_list, max_seq_length, tokenizer, output_file):
    """Convert a set of `InputExample`s to a TFRecord file."""
    writer = tf.python_io.TFRecordWriter(output_file)

    for (ex_index, example) in enumerate(examples):

        if ex_index % 10000 == 0:
            tf.logging.info("Writing example %d of %d" % (ex_index, len(examples)))
        feature = convert_single_example(ex_index, example, label_list,max_seq_length, tokenizer)

        def create_int_feature(values):
            f = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
            return f

        features = collections.OrderedDict()
        features["input_ids"] = create_int_feature(feature.input_ids)
        features["input_mask"] = create_int_feature(feature.input_mask)
        features["segment_ids"] = create_int_feature(feature.segment_ids)
        features["label_ids"] = create_int_feature([feature.label_id])
        features["is_real_example"] = create_int_feature([int(feature.is_real_example)])

        tf_example = tf.train.Example(features=tf.train.Features(feature=features))
        writer.write(tf_example.SerializeToString())
    writer.close()

def file_based_input_fn_builder(input_file, seq_length, is_training,drop_remainder):
    name_to_features = {"input_ids": tf.FixedLenFeature([seq_length], tf.int64),"input_mask": tf.FixedLenFeature([seq_length], tf.int64),"segment_ids": tf.FixedLenFeature([seq_length], tf.int64),"label_ids": tf.FixedLenFeature([], tf.int64),"is_real_example": tf.FixedLenFeature([], tf.int64),}

    def _decode_record(record, name_to_features):
        example = tf.parse_single_example(record, name_to_features)

    # tf.Example only supports tf.int64, but the TPU only supports tf.int32.
    # So cast all int64 to int32.
        for name in list(example.keys()):
            t = example[name]
            if t.dtype == tf.int64:
                t = tf.to_int32(t)
                example[name] = t

        return example

    def input_fn(params):
        batch_size = params["batch_size"]
        d = tf.data.TFRecordDataset(input_file)
        if is_training:
            d = d.repeat()
            d = d.shuffle(buffer_size=100)
        d = d.apply(
          tf.contrib.data.map_and_batch(
              lambda record: _decode_record(record, name_to_features),batch_size=batch_size, drop_remainder=drop_remainder))

        return d
    return input_fn
def create_model(bert_config, is_training, input_ids, input_mask, segment_ids, labels, num_labels, use_one_hot_embeddings):
    model = modeling.BertModel(
        config=bert_config,
        is_training=is_training,
        input_ids=input_ids,
        input_mask=input_mask,
        token_type_ids=segment_ids,
        use_one_hot_embeddings=use_one_hot_embeddings)

  # In the demo, we are doing a simple classification task on the entire
  # segment.
  #
  # If you want to use the token-level output, use model.get_sequence_output()
  # instead.
    output_layer = model.get_pooled_output()

    hidden_size = output_layer.shape[-1].value

    output_weights = tf.get_variable(
        "output_weights", [num_labels, hidden_size],
        initializer=tf.truncated_normal_initializer(stddev=0.02))

    output_bias = tf.get_variable(
        "output_bias", [num_labels], initializer=tf.zeros_initializer())

    with tf.variable_scope("loss"):
        if is_training:
      # I.e., 0.1 dropout
            output_layer = tf.nn.dropout(output_layer, keep_prob=0.9)

        logits = tf.matmul(output_layer, output_weights, transpose_b=True)
        logits = tf.nn.bias_add(logits, output_bias)
        probabilities = tf.nn.softmax(logits, axis=-1)
        log_probs = tf.nn.log_softmax(logits, axis=-1)

        one_hot_labels = tf.one_hot(labels, depth=num_labels, dtype=tf.float32)

        per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
        loss = tf.reduce_mean(per_example_loss)

        return (loss, per_example_loss, logits, probabilities)

def model_fn_builder(bert_config, num_labels, init_checkpoint, learning_rate, num_train_steps, num_warmup_steps, use_tpu, use_one_hot_embeddings):
    def model_fn(features, labels, mode, params):
        tf.logging.info("*** Features ***")
        for name in sorted(features.keys()):
            tf.logging.info("  name = %s, shape = %s" % (name, features[name].shape))

        input_ids = features["input_ids"]
        input_mask = features["input_mask"]
        segment_ids = features["segment_ids"]
        label_ids = features["label_ids"]
        is_real_example = None
        if "is_real_example" in features:
            is_real_example = tf.cast(features["is_real_example"], dtype=tf.float32)
        else:
            is_real_example = tf.ones(tf.shape(label_ids), dtype=tf.float32)

        is_training = (mode == tf.estimator.ModeKeys.TRAIN)

        (total_loss, per_example_loss, logits, probabilities) = create_model(bert_config, is_training, input_ids, input_mask, segment_ids, label_ids,num_labels, use_one_hot_embeddings)
        tvars = tf.trainable_variables()
        initialized_variable_names = {}
        scaffold_fn = None
        if init_checkpoint:
            (assignment_map, initialized_variable_names) = modeling.get_assignment_map_from_checkpoint(tvars, init_checkpoint)
            if use_tpu:
                def tpu_scaffold():
                    tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
                    return tf.train.Scaffold()

                scaffold_fn = tpu_scaffold
            else:
                tf.train.init_from_checkpoint(init_checkpoint, assignment_map)

        tf.logging.info("**** Trainable Variables ****")
        for var in tvars:
            init_string = ""
            if var.name in initialized_variable_names:
                init_string = ", *INIT_FROM_CKPT*"
            tf.logging.info("  name = %s, shape = %s%s", var.name, var.shape,init_string)

        output_spec = None
        if mode == tf.estimator.ModeKeys.TRAIN:

            train_op = optimization.create_optimizer(
                total_loss, learning_rate, num_train_steps, num_warmup_steps, use_tpu)

            output_spec = tf.contrib.tpu.TPUEstimatorSpec(mode=mode,loss=total_loss,train_op=train_op,scaffold_fn=scaffold_fn)
        elif mode == tf.estimator.ModeKeys.EVAL:

            def metric_fn(per_example_loss, label_ids, logits, is_real_example):
                predictions = tf.argmax(logits, axis=-1, output_type=tf.int32)
                accuracy = tf.metrics.accuracy(labels=label_ids, predictions=predictions, weights=is_real_example)
                loss = tf.metrics.mean(values=per_example_loss, weights=is_real_example)
                return {
                    "eval_accuracy": accuracy,
                    "eval_loss": loss,
                }

            eval_metrics = (metric_fn,[per_example_loss, label_ids, logits, is_real_example])
            output_spec = tf.contrib.tpu.TPUEstimatorSpec(mode=mode,loss=total_loss,eval_metrics=eval_metrics,scaffold_fn=scaffold_fn)
        else:
            output_spec = tf.contrib.tpu.TPUEstimatorSpec(mode=mode,predictions={"probabilities": probabilities}, scaffold_fn=scaffold_fn)
        return output_spec

    return model_fn


@app.route("/check", methods = ['POST'])
def predict():
    data = request.get_json()
    sentence_a = data['sentence1']
    sentence_b = data['sentence2']
    tf.gfile.MakeDirs(FLAGS.output_dir)
    processor = MnliProcessor()
    label_list = processor.get_labels()
    tokenization.validate_case_matches_checkpoint(FLAGS.do_lower_case,FLAGS.init_checkpoint)
    bert_config = modeling.BertConfig.from_json_file(FLAGS.bert_config_file)
    tokenizer = tokenization.FullTokenizer(vocab_file=FLAGS.vocab_file, do_lower_case=FLAGS.do_lower_case)
    tpu_cluster_resolver = None
    if FLAGS.use_tpu and FLAGS.tpu_name:
        tpu_cluster_resolver = tf.contrib.cluster_resolver.TPUClusterResolver(FLAGS.tpu_name, zone=FLAGS.tpu_zone, project=FLAGS.gcp_project)
    is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2
    run_config = tf.contrib.tpu.RunConfig(cluster=tpu_cluster_resolver, master=FLAGS.master, model_dir=FLAGS.output_dir, save_checkpoints_steps=FLAGS.save_checkpoints_steps, tpu_config=tf.contrib.tpu.TPUConfig( iterations_per_loop=FLAGS.iterations_per_loop, num_shards=FLAGS.num_tpu_cores, per_host_input_for_training=is_per_host))

    train_examples = None
    num_train_steps = None
    num_warmup_steps = None

    # FLAGS.do_predict
    predict_examples = processor.create_examples(sentence_a, sentence_b)
    predict_file = os.path.join(FLAGS.output_dir, "predict.tf_record")
    file_based_convert_examples_to_features(predict_examples, label_list,
                                            FLAGS.max_seq_length, tokenizer,
                                            predict_file)
    tf.logging.info("***** Running prediction*****")
    model_fn_a = model_fn_builder(bert_config=bert_config, num_labels=len(label_list), init_checkpoint=FLAGS.init_checkpoint, learning_rate=FLAGS.learning_rate, num_train_steps=num_train_steps, num_warmup_steps=num_warmup_steps, use_tpu=FLAGS.use_tpu, use_one_hot_embeddings=FLAGS.use_tpu)
    predict_input_fn = file_based_input_fn_builder( input_file=predict_file, seq_length=FLAGS.max_seq_length, is_training=False, drop_remainder=False)
    estimator = tf.contrib.tpu.TPUEstimator(use_tpu=False, model_fn=model_fn_a, config=run_config, train_batch_size=FLAGS.train_batch_size, eval_batch_size=FLAGS.eval_batch_size, predict_batch_size=FLAGS.predict_batch_size)
    result = estimator.predict(input_fn=predict_input_fn)
    output = []
    for (i, prediction) in enumerate(result):
        probabilities = prediction["probabilities"]
        for class_probability in probabilities:
            output.append(str(class_probability))
    print(output)
    return jsonify({'message': output})




if __name__ == "__main__":
    flags.mark_flag_as_required("bert_config_file")
    flags.mark_flag_as_required("vocab_file")
    app.run()
