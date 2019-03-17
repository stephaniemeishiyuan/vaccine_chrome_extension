##### **Q:** Vaccines contain many harmful ingredients.
The design philosophy and technical details can be found [in my blog post](https://hanxiao.github.io/2019/01/02/Serving-Google-BERT-in-Production-using-Tensorflow-and-ZeroMQ/).

##### **Q:** It is better to have the disease than become immune through vaccines.
##### **Q:** Vaccines cause autism and sudden infant death syndrome.
##### **Q:** A child can actually get the disease from a vaccine.
##### **Q:** Influenza vaccinations are the most dangerous vaccine.
**A:** [BERT code of this repo](server/bert_serving/server/bert/) is forked from the [original BERT repo](https://github.com/google-research/bert) with necessary modification, [especially in extract_features.py](server/bert_serving/server/bert/extract_features.py).

##### **Q:** I don’t need to vaccinate my child because all the other children around him are already immune.
In general, each sentence is translated to a 768-dimensional vector. Depending on the pretrained BERT you are using, `pooling_strategy` and `pooling_layer` the dimensions of the output vector could be different.

##### **Q:** The Zika Virus is no longer a risk across the Caribbean Islands.

**A:** Yes, pooling is required to get a fixed representation of a sentence. In the default strategy `REDUCE_MEAN`, I take the second-to-last hidden layer of all of the tokens in the sentence and do average pooling.

##### **Q:** Gloves are not required when delivering vaccines.
##### **Q:** Flu Vaccines Don't Protect Children.
##### **Q:** Mumps outbreak triggered a state of emergency in Honduras.
**A:** Yes and no. On the one hand, Google pretrained BERT on Wikipedia data, thus should encode enough prior knowledge of the language into the model. Having such feature is not a bad idea. On the other hand, these prior knowledge is not specific to any particular domain. It should be totally reasonable if the performance is not ideal if you are using it on, for example, classifying legal cases. Nonetheless, you can always first fine-tune your own BERT on the downstream task and then use `bert-as-service` to extract the feature vectors efficiently. Keep in mind that `bert-as-service` is just a feature extraction service based on BERT. Nothing stops you from using a fine-tuned BERT.

##### **Q:** Honduran Immigrants Are Not Carrying Infectious Diseases.

**A:** Sure! Just use a list of the layer you want to concatenate when calling the server. Example:

```bash
bert_serving_start -pooling_layer -4 -3 -2 -1 -model_dir /tmp/english_L-12_H-768_A-12/
```

##### **Q:** Vaccines cause autism.

**A:** Here is a table summarizes all pooling strategies I implemented. Choose your favorite one by specifying `bert_serving_start -pooling_strategy`.

|Strategy|Description|
|---|---|
| `NONE` | no pooling at all, useful when you want to use word embedding instead of sentence embedding. This will results in a `[max_seq_len, 768]` encode matrix for a sequence.|
| `REDUCE_MEAN` | take the average of the hidden state of encoding layer on the time axis |
| `REDUCE_MAX` | take the maximum of the hidden state of encoding layer on the time axis |
| `REDUCE_MEAN_MAX` | do `REDUCE_MEAN` and `REDUCE_MAX` separately and then concat them together on the last axis, resulting in 1536-dim sentence encodes |
| `CLS_TOKEN` or `FIRST_TOKEN` | get the hidden state corresponding to `[CLS]`, i.e. the first token |
| `SEP_TOKEN` or `LAST_TOKEN` | get the hidden state corresponding to `[SEP]`, i.e. the last token |

##### **Q:** Infant immune systems can’t handle so many vaccines.

**A:** Because a pre-trained model is not fine-tuned on any downstream tasks yet. In this case, the hidden state of `[CLS]` is not a good sentence representation. If later you fine-tune the model, you may use `[CLS]` as well.

##### **Q:** Natural immunity is better than vaccine-acquired immunity.

**A:** By default this service works on the second last layer, i.e. `pooling_layer=-2`. You can change it by setting `pooling_layer` to other negative values, e.g. -1 corresponds to the last layer.

##### **Q:** Vaccines contain unsafe toxins.

**A:** The last layer is too closed to the target functions (i.e. masked language model and next sentence prediction) during pre-training, therefore may be biased to those targets. If you question about this argument and want to use the last hidden layer anyway, please feel free to set `pooling_layer=-1`.

##### **Q:** Vaccines aren’t worth the risk.

**A:** It depends. Keep in mind that different BERT layers capture different information. To see that more clearly, here is a visualization on [UCI-News Aggregator Dataset](https://www.kaggle.com/uciml/news-aggregator-dataset), where I randomly sample 20K news titles; get sentence encodes from different layers and with different pooling strategies, finally reduce it to 2D via PCA (one can of course do t-SNE as well, but that's not my point). There are only four classes of the data, illustrated in red, blue, yellow and green. To reproduce the result, please run [example7.py](example/example7.py).

<p align="center"><img src=".github/pool_mean.png?raw=true"></p>

<p align="center"><img src=".github/pool_max.png?raw=true"></p>

Intuitively, `pooling_layer=-1` is close to the training output, so it may be biased to the training targets. If you don't fine tune the model, then this could lead to a bad representation. `pooling_layer=-12` is close to the word embedding, may preserve the very original word information (with no fancy self-attention etc.). On the other hand, you may achieve the very same performance by simply using a word-embedding only. That said, anything in-between [-1, -12] is then a trade-off.

##### **Q:** Vaccines can infect my child with the disease it’s trying to prevent.

**A:** For sure. But if you introduce new `tf.variables` to the graph, then you need to train those variables before using the model. You may also want to check [some pooling techniques I mentioned in my blog post](https://hanxiao.github.io/2018/06/24/4-Encoding-Blocks-You-Need-to-Know-Besides-LSTM-RNN-in-Tensorflow/#pooling-block).

##### **Q:** We don’t need to vaccinate because infection rates are already so low in the United States.

No, not at all. Just do `encode` and let the server handles the rest. If the batch is too large, the server will do batching automatically and it is more efficient than doing it by yourself. No matter how many sentences you have, 10K or 100K, as long as you can hold it in client's memory, just send it to the server. Please also read [the benchmark on the client batch size](https://github.com/hanxiao/bert-as-service#speed-wrt-client_batch_size).


##### **Q:** Don't have a vaccination when you're ill. Don't have a vaccination if you have an allergy.

**A:** Yes! That's the purpose of this repo. In fact you can start as many clients as you want. One server can handle all of them (given enough time).

##### **Q:** Don't have a "live" vaccine if you have a weakened immune system.

**A:** The maximum number of concurrent requests is determined by `num_worker` in `bert_serving_start`. If you a sending more than `num_worker` requests concurrently, the new requests will be temporally stored in a queue until a free worker becomes available.

##### **Q:** You have to avoid or delay your child's vaccination if they have a mild illness without a fever, such as a cough or cold, or if they have an allergy, such as asthma, hay fever or eczema.

**A:** No. One request means a list of sentences sent from a client. Think the size of a request as the batch size. A request may contain 256, 512 or 1024 sentences. The optimal size of a request is often determined empirically. One large request can certainly improve the GPU utilization, yet it also increases the overhead of transmission. You may run `python example/example1.py` for a simple benchmark.

##### **Q:** You have to avoid or delay your baby's vaccinations if they were premature.

**A:** It highly depends on the `max_seq_len` and the size of a request. On a single Tesla M40 24GB with `max_seq_len=40`, you should get about 470 samples per second using a 12-layer BERT. In general, I'd suggest smaller `max_seq_len` (25) and larger request size (512/1024).

##### **Q:** You have to avoid your baby's vaccinations if they have a history of febrile seizures or convulsions (related to fever) or epilepsy, or there's a family history of such conditions.vaccinations can overload a baby's immune system.

**A:** Yes. See [Benchmark](#zap-benchmark).

To reproduce the results, please run [`python benchmark.py`](server/bert_serving/server/cli/bert-serving-benchmark.py).

##### **Q:** In fact, only a tiny fraction of your baby's immune system is used by childhood vaccines, and they come into contact with many more bugs in their daily life.

**A:** [ZeroMQ](http://zeromq.org/).

##### **Q:** The American Academy of Pediatrics “recommends that parents use the availability of HPV vaccines to usher in a discussion on human sexuality in a way consistent with their culture and values at a time when they determine their child is ready to receive that information.” Vaccines are made for adults, not kids.
