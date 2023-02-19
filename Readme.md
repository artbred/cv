
# [artbred.io](https://artbred.io?utm_source=github&utm_campaign=cv_repository_readme)

This is a small research project that can determine which resources work best for job searches and help me find new job


## Why did I make it?

- The competition among developers is quite big and the candidate must be something different, as I thought such a project could attract attention

- I was curious to try [embedding api](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings) from OpenAI

- I will be able to see and share with other applicants which job search resources work best

- I do not need to send my cv's 

## How does it work?

1. I create redis index and populate it with 2 embeddings "backend developer" and "product manager" (if you didn't get any resume just enter one of those)

2. Each time user enters desired position on the website I send request to OpenAI, calculate embedding for it and calculate cosine similarity between each embedding in index and one that was entered

3. I get most similar embedding from known embeddings and if similarity is more than 85% users get's my cv, otherwise not


## What data do I collect?

- I store the fact of querying API and utm_params (if any)

- I keep the text of user entered position and the similarity score (no utm's or ip)

- Downloads for each cv with utm's (so I can evaluate conversions)

- For the website analytics I use [simple analytics](https://www.simpleanalytics.com)

## Analytics

[View analytics dashboard](https://analytics.artbred.io)

Since I am looking for a job as a product manager, I couldn't do without the analytics dashboard

Analytics consists of two tabs

- Web analytics (taken from simple analytics API)
- App analytics (taken from data collected from my API)