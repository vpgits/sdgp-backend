# sdgp-backend

Welcome to the sdgp-backend repository!

This repository contains the source code related to the Software Development Group Project (SDGP) machine learning component. Specifically, it includes a docker compose file and related github actions related to CI-CD pipeline

## Requirements

To run the backend successfully, ensure that your machine meets the following requirements:

- A VPS with least 2BG RAM , 1 VCPU and least 5Gb of Storage
- A stable internet connection
- API keys to supabase, fireworks, runpod

## Key-Takeaways

- You have to download gte/small[link:https://huggingface.co/thenlper/gte-small] and place it inside `celery_workers/src/api`
- Manually running without docker will require manually changing the code to configure rabbitmq and redis.

## Deployment

- You can try to replicate the given code and make your own version. You are free to explore and use it as you see fit.
- Or if you want to deploy this , locally can be done through docker compose. Make the appropriate changes to make docker compose work.
- If need to be deployed on cloud, setup a reverse proxy and use docker compose for hosting.
