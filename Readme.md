### What my project does? [artbred.io](https://artbred.io?utm_source=github&utm_campaign=repository)

#### This project is based on the OpenAI embeddings API, which allows converting text into a numerical format that can be used in machine learning

#### Every time the user enters text on the website, I obtain an embedding from it and compare it to those already calculated (which in this case are embeddings for two positions "product manager" and "backend developer")

##### If you did not get any CV, just enter one of those on the website

<details>
<summary>Technical details</summary>

#### To evaluate the similarity between pre-determined embeddings and the query embedding, I employ cosine similarity as the scoring method. It does not work very well since score ``(1 - distance)`` between random characters and any position is about 0.77 

P.S I don't have much experience with NLP, so I decided to leave this metric

#### In order to apply cosine similarity in efficient way I use [redis search](https://redis.io/docs/stack/search/). To populate embeddings you should run ``make up && make populate FLUSH=-f``, this will clean all redis data and create search index, later you can change contents of [populate.py](./app/populate.py) and just call ``make populate`` (this will only clean previous embeddings)

</details>

#### To determine the most effective channels for acquiring job opportunities, I utilize utm links to measure and analyze performance metrics. I also use [dub.sh](https://dub.sh) as a link shortener.

# firebase, google analytics

#### Each time a user sends a request from the website, I receive UTM params and store them, so I know how many times users tried to get my CV by entering the desired position and how many downloaded it (based on UTM params). Once I gather data, I will evaluate all metrics to see which channel leads to more traffic and/or conversions.


<details>
<summary>Technical details</summary>

#### All redis integrations are located in [storage.py](./app/storage.py). I store revoked jwt tokens in a set, all other data is stored as hashes. I use ``command: ["redis-server", "--loadmodule", "/usr/lib/redis/modules/redisearch.so", "--appendonly", "yes", "--aof-use-rdb-preamble", "yes"]`` for data persistance

</details>

### Why you should hire me as product manager?
#### You are reading this when 11 seconds is the average time of looking into cv


### Why you should hire me as backend developer?
#### Check out code inside [app](./app/) and in [this repository](https://github.com/artbred/ecomdream)